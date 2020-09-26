#!/usr/bin/python3
#
# zeitgitterd — Independent GIT Timestamping, HTTPS server
#
# Copyright (C) 2019,2020 Marcel Waldvogel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

# Sending and receiving mail

import logging as _logging
import os
import re
import subprocess
import threading
import time
from datetime import datetime, timedelta
from imaplib import IMAP4
from pathlib import Path
from smtplib import SMTP
from time import gmtime, strftime

import pygit2 as git

import autoblockchainify.config

logging = _logging.getLogger('mail')


def split_host_port(host, default_port):
    if ':' in host:
        host, port = host.split(':', 1)
        return (host, int(port))
    else:
        return (host, default_port)


def send(body, subject='Stamping request', to=None):
    # Does not work in unittests if assigned in function header
    # (are bound too early? At load time instead of at call time?)
    if to is None:
        to = autoblockchainify.config.arg.stamper_to
    logging.debug('SMTP server %s' % autoblockchainify.config.arg.stamper_smtp_server)
    (host, port) = split_host_port(autoblockchainify.config.arg.stamper_smtp_server, 587)
    with SMTP(host, port=port) as smtp:
        smtp.starttls()
        smtp.login(autoblockchainify.config.arg.stamper_username,
                   autoblockchainify.config.arg.stamper_password)
        frm = autoblockchainify.config.arg.stamper_own_address
        date = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        msg = """From: %s
To: %s
Date: %s
Subject: %s

%s""" % (frm, to, date, subject, body)
        smtp.sendmail(frm, to, msg)


def extract_pgp_body(body):
    try:
        body = str(body, 'ASCII')
    except TypeError as t:
        logging.warning("Conversion error for message body: %s" % t)
        return None
    lines = body.splitlines()
    start = None
    for i in range(0, len(lines)):
        if lines[i] == '-----BEGIN PGP SIGNED MESSAGE-----':
            logging.debug("Found start at %d: %s" % (i, lines[i]))
            start = i
            break
    else:
        return None

    end = None
    for i in range(start, len(lines)):
        if lines[i] == '-----END PGP SIGNATURE-----':
            logging.debug("Found end at %d: %s" % (i, lines[i]))
            end = i
            break
    else:
        return None
    return lines[start:end + 1]


def save_signature(bodylines, logfile):
    repo = autoblockchainify.config.arg.repository
    ascfile = Path(repo, 'pgp-timestamp.sig')
    with ascfile.open(mode='w') as f:
        f.write('\n'.join(bodylines) + '\n')
        # Change will be picked up by next check for directory modification
    logfile.unlink()  # Mark as reply received, no need for resumption


def maybe_decode(s):
    """Decode, if it is not `None`"""
    if s is None:
        return s
    else:
        return s.decode('ASCII')


def body_signature_correct(bodylines, stat):
    body = '\n'.join(bodylines)
    logging.debug("Bodylines: %s" % body)
    # Cannot use Python gnupg wrapper: Requires GPG 1.x to verify
    # Copy env for gnupg without locale
    env = {}
    for k in os.environ:
        if not k.startswith('LC_'):
            env[k] = os.environ[k]
    env['LANG'] = 'C'
    env['TZ'] = 'UTC'
    res = subprocess.run(['gpg1', '--pgp2', '--verify'],
                         env=env, input=body.encode('ASCII'),
                         stderr=subprocess.PIPE)
    stderr = maybe_decode(res.stderr)
    logging.debug(stderr)
    if res.returncode != 0:
        logging.warning("gpg1 return code %d (%r)" % (res.returncode, stderr))
        return False
    if '\ngpg: Good signature' not in stderr:
        logging.warning("Not good signature (%r)" % stderr)
        return False
    if not stderr.startswith('gpg: Signature made '):
        logging.warning("Signature not made (%r)" % stderr)
        return False
    if not ((' key ID %s\n' % autoblockchainify.config.arg.stamper_keyid)
            in stderr):
        logging.warning("Wrong KeyID (%r)" % stderr)
        return False
    try:
        logging.debug(stderr[24:48])
        sigtime = datetime.strptime(stderr[24:48], "%b %d %H:%M:%S %Y %Z")
        logging.debug(sigtime)
    except ValueError:
        logging.warning("Illegal date (%r)" % stderr)
        return False
    if sigtime > datetime.utcnow() + timedelta(seconds=30):
        logging.warning("Signature time %s lies more than 30 seconds in the future"
                        % sigtime)
        return False
    modtime = datetime.utcfromtimestamp(stat.st_mtime)
    if sigtime < modtime - timedelta(seconds=30):
        logging.warning("Signature time %s is more than 30 seconds before\n"
                        "file modification time %s"
                        % (sigtime, modtime))
        return False
    return True


def verify_body_and_save_signature(body, stat, logfile, msgno):
    bodylines = extract_pgp_body(body)
    if bodylines is None:
        logging.warning("No body lines")
        return False

    res = body_contains_file(bodylines, logfile)
    if res is None:
        logging.warning("File contents not in message %s" % msgno)
        return False
    else:
        (before, after) = res
        logging.debug("before %d, after %d" % (before, after))
        if before > 20 or after > 20:
            logging.warning("Too many lines added by the PGP Timestamping Server"
                            " before (%d)/after (%d) our contents" % (before, after))
            return False

    if not body_signature_correct(bodylines, stat):
        logging.warning("Body signature incorrect")
        return False

    save_signature(bodylines, logfile)
    return True


def body_contains_file(bodylines, logfile):
    if bodylines is None:
        return None
    linesbefore = 0
    with logfile.open(mode='r') as f:
        # A few empty/comment lines at the beginning
        firstline = f.readline().rstrip()
        for i in range(len(bodylines)):
            if bodylines[i] == firstline:
                break
            elif bodylines[i] == '' or bodylines[i][0] in '#-':
                linesbefore += 1
            else:
                return None
        # Now should be contiguous
        i += 1
        for line in f:
            if bodylines[i] != line.rstrip():
                return None
            i += 1
        # Now there should only be empty lines and a PGP signature
        linesafter = len(bodylines) - i
        i += 1
        while bodylines[i] == '':
            i += 1
        if bodylines[i] != '-----BEGIN PGP SIGNATURE-----':
            return None
        # No further line starting with '-'
        for i in range(i + 1, len(bodylines) - 1):
            if bodylines[i] != '' and bodylines[i][0] == '-':
                return None
        return (linesbefore, linesafter)


def file_unchanged(stat, logfile):
    try:
        cur_stat = logfile.stat()
        return (cur_stat.st_mtime == stat.st_mtime
                and cur_stat.st_ino == stat.st_ino)
    except FileNotFoundError:
        return False


def imap_idle(imap, stat, logfile):
    while True:
        imap.send(b'%s IDLE\r\n' % (imap._new_tag()))
        logging.info("IMAP waiting for IDLE response")
        line = imap.readline().strip()
        logging.debug("IMAP IDLE → %s" % line)
        if line != b'+ idling':
            logging.info("IMAP IDLE unsuccessful")
            return False
        # Wait for new message
        while file_unchanged(stat, logfile):
            line = imap.readline().strip()
            if line == b'' or line.startswith(b'* BYE '):
                return False
            match = re.match(r'^\* ([0-9]+) EXISTS$', str(line, 'ASCII'))
            if match:
                logging.info("You have new mail %s!"
                             % match.group(1).encode('ASCII'))
                # Stop idling
                imap.send(b'DONE\r\n')
                if check_for_stamper_mail(imap, stat, logfile) is True:
                    return False
                break  # Restart IDLE command
            # Otherwise: Uninteresting untagged response, continue idling
        logging.error("Next mail sent, giving up waiting on now-old reply")


def check_for_stamper_mail(imap, stat, logfile):
    # See `--no-dovecot-bug-workaround`:
    query = ('FROM', '"%s"' % autoblockchainify.config.arg.stamper_from,
             'UNSEEN',
             'LARGER', str(stat.st_size),
             'SMALLER', str(stat.st_size + 16384))
    logging.debug("IMAP SEARCH " + (' '.join(query)))
    (typ, msgs) = imap.search(None, *query)
    logging.info("IMAP SEARCH → %s, %s" % (typ, msgs))
    if len(msgs) == 1 and len(msgs[0]) > 0:
        mseq = msgs[0].replace(b' ', b',')
        (typ, contents) = imap.fetch(mseq, 'BODY[TEXT]')
        logging.debug("IMAP FETCH → %s (%d)" % (typ, len(contents)))
        remaining_msgids = mseq.split(b',')
        for m in contents:
            if m != b')':
                msgid = remaining_msgids[0]
                remaining_msgids = remaining_msgids[1:]
                logging.debug("IMAP FETCH BODY (%s) → %s…" % (msgid, m[1][:20]))
                if verify_body_and_save_signature(m[1], stat, logfile, msgid):
                    logging.info("Verify_body() succeeded; deleting %s" % msgid)
                    imap.store(msgid, '+FLAGS', '\\Deleted')
                    return True
    return False


def wait_for_receive(logfile):
    stat = logfile.stat()  # Should always succeed
    logging.debug("Timestamp revision file is from %d" % stat.st_mtime)
    (host, port) = split_host_port(autoblockchainify.config.arg.stamper_imap_server, 143)
    with IMAP4(host=host, port=port) as imap:
        imap.starttls()
        imap.login(autoblockchainify.config.arg.stamper_username,
                   autoblockchainify.config.arg.stamper_password)
        imap.select('INBOX')
        if not check_for_stamper_mail(imap, stat, logfile):
            # No existing message found, wait for more incoming messages
            # and process them until definitely okay or giving up for good
            if 'IDLE' in imap.capabilities:
                imap_idle(imap, stat, logfile)
            else:
                logging.warning("IMAP server does not support IDLE")
                # Poll every minute, for 10 minutes
                for i in range(10):
                    time.sleep(60)
                    if check_for_stamper_mail(imap, stat, logfile):
                        return
                logging.error("No response received, giving up")


def async_email_timestamp(resume=False):
    """If called with `resume=True`, tries to resume waiting for the mail"""
    path = autoblockchainify.config.arg.repository
    repo = git.Repository(path)
    head = repo.head
    logfile = Path(path, 'pgp-timestamp.tmp')
    if repo.head_is_unborn:
        logging.error("Cannot timestamp by email in repository without commits")
        return
    if resume:
        if not logfile.is_file():
            logging.info("Not resuming mail timestamp: No pending mail reply")
            return
        with logfile.open() as f:
            contents = f.read()
        if len(contents) < 40:
            logging.info("Not resuming mail timestamp: No revision info")
            return
    else:  # Fresh request
        new_rev = ("Timestamp requested for\ngit commit %s\nat %s\n" %
                   (head.target.hex,
                    strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())))
        with logfile.open('w') as f:
            f.write(new_rev)
        send(new_rev)
    threading.Thread(target=wait_for_receive, args=(logfile,),
                     daemon=True).start()
