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

# Committing to git and obtaining upstream timestamps
#
# The state machine used is described in ../doc/StateMachine.md

import datetime
import logging as _logging
import os
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

import zeitgitter.config
import zeitgitter.mail
import zeitgitter.stamper

logging = _logging.getLogger('commit')

# To serialize all commit-related operations
# - writing commit entries in order (that includes obtaining the timestamp)
# - rotating files
# - performing other operations in the repository
serialize = threading.Lock()


def commit_to_git(repo, log, preserve=None, msg="Newly timestamped commits"):
    subprocess.run(['git', 'add', log.as_posix()],
                   cwd=repo, check=True)
    env = os.environ.copy()
    env['GNUPGHOME'] = zeitgitter.config.arg.gnupg_home
    subprocess.run(['git', 'commit', '-m', msg, '--allow-empty',
                    '--gpg-sign=' + zeitgitter.config.arg.keyid],
                   cwd=repo, env=env, check=True)
    # Mark as processed; use only while locked!
    if preserve is None:
        log.unlink()
    else:
        log.rename(preserve)
        with preserve.open('r') as p:
            for line in p:
                logging.debug('%s: %s' % (preserve, line))


def commit_dangling(repo, log):
    """If there is still a hashes.log hanging around, commit it now"""
    # `subprocess.run(['git', …], …)` (called from `commit_to_git()`) may also
    # raise FileNotFoundError. This, we do not want to be hidden by the `pass`.
    # Therefore, this weird construct.
    stat = None
    try:
        stat = log.stat()
    except FileNotFoundError:
        pass
    if stat is not None:
        d = datetime.datetime.utcfromtimestamp(stat.st_mtime)
        dstr = d.strftime('%Y-%m-%d %H:%M:%S UTC')
        # Do not preserve for PGP Timestamper, as another commit will follow
        # immediately
        commit_to_git(repo, log, None,
                      "Found uncommitted data from " + dstr)


def rotate_log_file(tmp, log):
    tmp.rename(log)


def push_upstream(repo, to, branches):
    logging.info("Pushing to %s" % (['git', 'push', to] + branches))
    ret = subprocess.run(['git', 'push', to] + branches,
                         cwd=repo)
    if ret.returncode != 0:
        logging.error("'git push %s %s' failed" % (to, ' '.join(branches)))


def cross_timestamp(repo, options, delete_fake_time=False):
    # Servers specified by servername only always use wallclock for the
    # timestamps. Servers specified as `branch=server` tuples will
    # allow wallclock to be overridden by `ZEITGITTER_FAKE_TIME`.
    # This is needed for testing only, so that both reproducible
    # signatures can be generated (with ourselves as timestamper
    # and `ZEITGITTER_FAKE_TIME`) as well as remote Zeitgitter
    # servers can be used.
    if delete_fake_time and 'ZEITGITTER_FAKE_TIME' in os.environ:
        env = os.environ.copy()
        del env['ZEITGITTER_FAKE_TIME']
    else:
        env = os.environ
    ret = subprocess.run(['git', 'timestamp'] + options, cwd=repo, env=env)
    if ret.returncode != 0:
        sys.stderr.write("git timestamp " + ' '.join(options) + " failed")


def do_commit():
    """To be called in a non-daemon thread to reduce possibilities of
    early termination.

    0. Check if there is anything uncommitted
    1. Rotate log file
    2. Commit to git
    3. (Optionally) cross-timestamp using HTTPS (synchronous)
    4. (Optionally) push
    5. (Optionally) cross-timestamp using email (asynchronous)"""
    try:
        repo = zeitgitter.config.arg.repository
        tmp = Path(repo, 'hashes.work')
        log = Path(repo, 'hashes.log')
        preserve = Path(repo, 'hashes.stamp')
        with serialize:
            commit_dangling(repo, log)
            # See comment in `commit_dangling`
            stat = None
            try:
                stat = tmp.stat()
            except FileNotFoundError:
                logging.info("Nothing to rotate")
            if stat is not None:
                rotate_log_file(tmp, log)
                d = datetime.datetime.utcfromtimestamp(stat.st_mtime)
                dstr = d.strftime('%Y-%m-%d %H:%M:%S UTC')
                commit_to_git(repo, log, preserve,
                              "Newly timestamped commits up to " + dstr)
                with tmp.open(mode='ab'):
                    pass  # Recreate hashes.work
        repositories = zeitgitter.config.arg.push_repository
        branches = zeitgitter.config.arg.push_branch
        for r in zeitgitter.config.arg.upstream_timestamp:
            logging.info("Cross-timestamping %s" % r)
            if '=' in r:
                (branch, server) = r.split('=', 1)
                cross_timestamp(repo, ['--branch', branch, '--server', server])
            else:
                cross_timestamp(repo, ['--server', r], delete_fake_time=True)
            time.sleep(zeitgitter.config.arg.upstream_sleep.total_seconds())
        for r in repositories:
            logging.info("Pushing upstream to %s" % r)
            push_upstream(repo, r, branches)

        if zeitgitter.config.arg.stamper_own_address:
            logging.info("cross-timestamping by mail")
            zeitgitter.mail.async_email_timestamp(preserve)
        logging.info("do_commit done")
    except Exception as e:
        logging.error("Unhandled exception in do_commit() thread: %s: %s" %
                      (e, ''.join(traceback.format_tb(sys.exc_info()[2]))))


def wait_until():
    """Run at given interval and offset"""
    interval = zeitgitter.config.arg.commit_interval.total_seconds()
    offset = zeitgitter.config.arg.commit_offset.total_seconds()
    while True:
        now = time.time()
        until = now - (now % interval) + offset
        if until <= now:
            until += interval
        time.sleep(until - now)
        threading.Thread(target=do_commit, daemon=False).start()


def run():
    """Start background thread to wait for given time"""
    threading.Thread(target=wait_until, daemon=True).start()
