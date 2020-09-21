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

# Timestamp creation

import logging as _logging
import os
import re
import shutil
import sys
import threading
import time
from pathlib import Path

import gnupg

import zeitgitter.commit
import zeitgitter.config

logging = _logging.getLogger('stamper')


def get_nick(domain):
    fields = domain.split('.')
    for i in fields:
        if i != '' and i != 'igitt' and i != 'zeitgitter' and 'stamp' not in i:
            return i
    sys.exit("Please specify a keyid")


def create_key(gpg, keyid):
    name, mail = keyid.split(' <')
    mail = mail[:-1]
    gki = gpg.gen_key_input(name_real=name, name_email=mail,
                            key_type='eddsa', key_curve='Ed25519', key_usage='sign')
    # Force to not ask (non-existant) user for passphrase
    gki = '%no-protection\n' + gki
    key = gpg.gen_key(gki)
    if key.fingerprint is None:
        sys.exit("Cannot create PGP key for %s: %s" % (keyid, key.stderr))
    logging.info("Created PGP key %s" % key.fingerprint)
    return key.fingerprint


def get_keyid(keyid, domain, gnupg_home):
    """Find (and possibly create) a key ID by trying the following, in order:
    1. `keyid` is not `None`:
       1. `keyid` matches exactly one secret key: return the hexadecimal
           key ID of that key.
       2. `keyid` does not match any existing key, but matches the pattern
           "Name <email>": Create an ed25519 key and return its ID.
       3. Else fail.
    2. `keyid` is `None`:
       1. If there is exactly one secret key in the keyring, return that one.
       2. If there are no secret keys in the keyring, create an ed25519 key
          named "Nickname Timestamping Service <domain-to-email>", where
          "Nickname" is the capitalized first dot-separated part of `domain`
          which is not "zeitgitter", "igitt", or "*stamp*"; and
          "domain-to-email" is `domain` with its first dot is replaced by an @.
       3. Else fail.
    Design decision: The key is only created if the next start would chose that
    key (this obviates the need to monkey-patch the config file).

    All these operations must be done before round-robin operations (and
    copying the "original" GnuPG "home" directory) start."""
    gpg = gnupg.GPG(gnupghome=gnupg_home)
    if keyid is not None:
        keyinfo = gpg.list_keys(secret=True, keys=keyid)
        if len(keyinfo) == 1:
            return keyinfo[0]['keyid']
        elif re.match("^[A-Z][A-Za-z0-9 ]+ <[-_a-z0-9.]+@[-a-z0-9.]+>$",
                      keyid) and len(keyinfo) == 0:
            return create_key(gpg, keyid)
        else:
            if len(keyinfo) > 0:
                sys.exit("Too many secret keys matching key '%s'" % keyid)
            else:
                sys.exit("No secret keys match keyid '%s', "
                         "use the form 'Description <email>' if zeitgitterd "
                         "should create one automatically with that name" % keyid)
    else:
        keyinfo = gpg.list_keys(secret=True)
        if len(keyinfo) == 1:
            return keyinfo[0]['keyid']
        elif len(keyinfo) == 0:
            nick = get_nick(domain)
            maildomain = domain.replace('.', '@', 1)
            return create_key(gpg, "%s Timestamping Service <%s>"
                              % (nick.capitalize(), maildomain))
        else:
            sys.exit("Please specify a keyid in the configuration file")


class Stamper:
    def __init__(self):
        self.sem = threading.BoundedSemaphore(
            zeitgitter.config.arg.max_parallel_signatures)
        self.gpg_serialize = threading.Lock()
        self.timeout = zeitgitter.config.arg.max_parallel_timeout
        self.url = zeitgitter.config.arg.own_url
        self.keyid = zeitgitter.config.arg.keyid
        self.gpgs = [gnupg.GPG(gnupghome=zeitgitter.config.arg.gnupg_home)]
        self.max_threads = 1  # Start single-threaded
        self.keyinfo = self.gpg().list_keys(True, keys=self.keyid)
        if len(self.keyinfo) == 0:
            raise ValueError("No keys found")
        self.fullid = self.keyinfo[0]['uids'][0]
        self.pubkey = self.gpg().export_keys(self.keyid)
        self.extra_delay = None

    def start_multi_threaded(self):
        self.max_threads = zeitgitter.config.arg.number_of_gpg_agents

    def gpg(self):
        """Return the next GnuPG object, in round robin order.
        Create one, if less than `number-of-gpg-agents` are available."""
        with self.gpg_serialize:
            if len(self.gpgs) < self.max_threads:
                home = Path('%s-%d' % (zeitgitter.config.arg.gnupg_home, len(self.gpgs)))
                # Create copy if needed; to trick an additional gpg-agent
                # being started for the same directory
                if home.exists():
                    if home.is_symlink():
                        logging.info("Creating GnuPG key copy %s→%s"
                                     ", replacing old symlink"
                                     % (zeitgitter.config.arg.gnupg_home, home))
                        home.unlink()
                        # Ignore sockets (must) and backups (may) on copy
                        shutil.copytree(zeitgitter.config.arg.gnupg_home,
                                        home, ignore=shutil.ignore_patterns("S.*", "*~"))
                else:
                    logging.info("Creating GnuPG key copy %s→%s"
                                 % (zeitgitter.config.arg.gnupg_home, home))
                    shutil.copytree(zeitgitter.config.arg.gnupg_home,
                                    home, ignore=shutil.ignore_patterns("S.*", "*~"))
                nextgpg = gnupg.GPG(gnupghome=home.as_posix())
                self.gpgs.append(nextgpg)
                logging.debug("Returning new %r (gnupghome=%s)" % (nextgpg, nextgpg.gnupghome))
                return nextgpg
            else:
                # Rotate list left and return element wrapped around (if the list
                # just became full, this is the one least recently used)
                nextgpg = self.gpgs[0]
                self.gpgs = self.gpgs[1:]
                self.gpgs.append(nextgpg)
                logging.debug("Returning old %r (gnupghome=%s)" % (nextgpg, nextgpg.gnupghome))
                return nextgpg

    def sig_time(self):
        """Current time, unless in test mode"""
        return int(os.getenv('ZEITGITTER_FAKE_TIME', time.time()))

    def get_public_key(self):
        return self.pubkey

    def valid_tag(self, tag):
        """Tag validity defined in doc/Protocol.md

        Switching to `pygit2.reference_is_valid_name()` should be considered
        when this function is widely availabe in installations
        (was only added on 2018-10-17)"""
        # '$' always matches '\n' as well. Don't want this here.
        return (re.match('^[_a-z][-._a-z0-9]{,99}$', tag, re.IGNORECASE)
                and ".." not in tag and not '\n' in tag)

    def valid_commit(self, commit):
        # '$' always matches '\n' as well. Don't want this here.
        if '\n' in commit:
            return False
        return re.match('^[0-9a-f]{40}$', commit)

    def limited_sign(self, now, commit, data):
        """Sign, but allow at most <max-parallel-timeout> executions.
        Requests exceeding this limit will return None after <timeout> s,
        or wait indefinitely, if `--max-parallel-timeout` has not been
        given (i.e., is None). It logs any commit ID to stable storage
        before attempting to even create a signature. It also makes sure
        that the GnuPG signature time matches the GIT timestamps."""
        if self.sem.acquire(timeout=self.timeout):
            ret = None
            try:
                if self.extra_delay:
                    time.sleep(self.extra_delay)
                ret = self.gpg().sign(data, keyid=self.keyid, binary=False,
                                      clearsign=False, detach=True,
                                      extra_args=('--faked-system-time',
                                                  str(now) + '!'))
            finally:
                self.sem.release()
            return ret
        else:  # Timeout
            return None

    def log_commit(self, commit):
        with Path(zeitgitter.config.arg.repository,
                  'hashes.work').open(mode='ab', buffering=0) as f:
            f.write(bytes(commit + '\n', 'ASCII'))
            os.fsync(f.fileno())

    def stamp_tag(self, commit, tagname):
        if self.valid_commit(commit) and self.valid_tag(tagname):
            with zeitgitter.commit.serialize:
                now = int(self.sig_time())
                self.log_commit(commit)
            isonow = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now))
            tagobj = """object %s
type commit
tag %s
tagger %s %d +0000

:watch: %s tag timestamp
""" % (commit, tagname, self.fullid, now,
       self.url)

            sig = self.limited_sign(now, commit, tagobj)
            if sig == None:
                return None
            else:
                return tagobj + str(sig)
        else:
            return 406

    def stamp_branch(self, commit, parent, tree):
        if (self.valid_commit(commit) and self.valid_commit(tree)
                and (parent == None or self.valid_commit(parent))):
            with zeitgitter.commit.serialize:
                now = int(self.sig_time())
                self.log_commit(commit)
            isonow = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now))
            if parent == None:
                commitobj1 = """tree %s
parent %s
author %s %d +0000
committer %s %d +0000
""" % (tree, commit, self.fullid, now, self.fullid, now)
            else:
                commitobj1 = """tree %s
parent %s
parent %s
author %s %d +0000
committer %s %d +0000
""" % (tree, parent, commit, self.fullid, now, self.fullid, now)

            commitobj2 = """
:watch: %s branch timestamp %s
""" % (self.url, isonow)

            sig = self.limited_sign(now, commit, commitobj1 + commitobj2)
            if sig == None:
                return None
            else:
                # Replace all inner '\n' with '\n '
                gpgsig = 'gpgsig ' + str(sig).replace('\n', '\n ')[:-1]
                assert gpgsig[-1] == '\n'
                return commitobj1 + gpgsig + commitobj2
        else:
            return 406
