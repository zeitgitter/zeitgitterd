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
                   cwd=repo).check_returncode()
    env = os.environ.copy()
    env['GNUPGHOME'] = zeitgitter.config.arg.gnupg_home
    subprocess.run(['git', 'commit', '-m', msg, '--allow-empty',
                    '--gpg-sign=' + zeitgitter.config.arg.keyid],
                   cwd=repo, env=env).check_returncode()
    # Mark as processed; use only while locked!
    if preserve is None:
        log.unlink(log)
    else:
        log.rename(preserve)
        with preserve.open('r') as p:
            for line in p:
                logging.debug('%s: %s' % (preserve, line))


def commit_dangling(repo, log):
    """If there is still a hashes.log hanging around, commit it now"""
    try:
        stat = log.stat()
        d = datetime.datetime.utcfromtimestamp(stat.st_mtime)
        dstr = d.strftime('%Y-%m-%d %H:%M:%S UTC')
        commit_to_git(repo, log,
                      "Found uncommitted data from " + dstr)
    except FileNotFoundError:
        pass


def rotate_log_file(tmp, log):
    tmp.rename(log)


def push_upstream(repo, to, branches):
    logging.info("Pushing to %s" % (['git', 'push', to] + branches))
    ret = subprocess.run(['git', 'push', to] + branches,
                         cwd=repo)
    if ret.returncode != 0:
        logging.error("'git push %s %s' failed" % (to, branches))


def cross_timestamp(repo, branch, server):
    ret = subprocess.run(['git', 'timestamp',
                          '--branch', branch, '--server', server],
                         cwd=repo)
    if ret.returncode != 0:
        sys.stderr.write("git timestamp --branch %s --server %s failed"
                         % (branch, server))


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
            try:
                stat = tmp.stat()
                rotate_log_file(tmp, log)
                d = datetime.datetime.utcfromtimestamp(stat.st_mtime)
                dstr = d.strftime('%Y-%m-%d %H:%M:%S UTC')
                commit_to_git(repo, log, preserve,
                        "Newly timestamped commits up to " + dstr)
                with tmp.open(mode='ab'):
                    pass  # Recreate hashes.work
            except FileNotFoundError:
                logging.info("Nothing to rotate")
        repositories = zeitgitter.config.arg.push_repository
        branches = zeitgitter.config.arg.push_branch
        for r in zeitgitter.config.arg.upstream_timestamp:
            logging.info("Cross-timestamping %s" % r);
            (branch, server) = r.split('=', 1)
            cross_timestamp(repo, branch, server)
        for r in repositories:
            logging.info("Pushing upstream to %s" % r);
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
