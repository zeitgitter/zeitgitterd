#!/usr/bin/python3
#
# autoblockchainify — Turn any directory into a GIT Blockchain
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

# Configuration handling

import argparse
import configargparse
import datetime
import logging as _logging
import os
import sys
import random

import autoblockchainify.deltat
import autoblockchainify.version


logging = _logging.getLogger('config')


def get_args(args=None, config_file_contents=None):
    global arg
    # Config file in /etc or the program directory
    parser = configargparse.ArgumentParser(
        auto_env_var_prefix="autoblockchainify_",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="autoblockchainify — Turn any directory into a GIT Blockchain.",
        default_config_files=['/etc/autoblockchainify.conf',
            os.path.join(os.getenv('HOME'), 'autoblockchainify.conf')])

    # General
    parser.add_argument('--config-file', '-c',
                        is_config_file=True,
                        help="config file path")
    parser.add_argument('--debug-level',
                        default='INFO',
                        help="""amount of debug output: WARN, INFO, or DEBUG.
                            Debug levels for specific loggers can also be
                            specified using 'name=level'. Valid logger names:
                            `config`, `daemon`, `commit` (incl. requesting
                            timestamps), `gnupg`, `mail` (interfacing with PGP
                            Timestamping Server).  Example: `DEBUG,gnupg=INFO`
                            sets the default debug level to DEBUG, except for
                            `gnupg`.""")
    parser.add_argument('--version',
                        action='version', version=autoblockchainify.version.VERSION)

    # Identity
    # Default is applied in daemon.py:finish_setup()
    parser.add_argument('--identity',
                        help="""'Full Name <email@address>' for tagging
                        GIT commits.
                        Default (will only be applied to new repositories):
                        'Autoblockchainify <autoblockchainify@localhost>'.
                        An explicit value (non-default) will always update
                        the current GIT config.""")

    # Stamping
    parser.add_argument('--commit-interval',
                        default='1h',
                        help="how often to commit")
    parser.add_argument('--commit-offset',
                        help="""when to commit within that interval; e.g. after
                            37m19.3s. Default: Random choice in the interval.
                            For a production server, please fix a value in
                            the config file to avoid it jumping after every
                            restart.""")
    parser.add_argument('--force-after-intervals',
                        type=int,
                        default=6,
                        help="""After how many intervals to force a commit (and
                            request a timestamp by email, if configured).""")
    parser.add_argument('--repository',
                        default='.',
                        help="""path to the GIT repository (default '.')""")
    parser.add_argument('--zeitgitter-servers',
                        default=
                            'diversity-timestamps=https://diversity.zeitgitter.net'
                            ' gitta-timestamps=https://gitta.zeitgitter.net',
                        help="""any number of <branch>=<URL> tuples of
                            Zeitgitter timestampers""")

    # Pushing
    parser.add_argument('--push-repository',
                        default='',
                        help="""Space-separated list of repositores to push to;
                            setting this enables automatic push""")
    parser.add_argument('--push-branch',
                        default='',
                        help="Space-separated list of branches to push")

    # PGP Digital Timestamper interface
    parser.add_argument('--stamper-own-address', '--mail-address', '--email-address',
                        help="""our email address; enables
                            cross-timestamping from the PGP timestamper""")
    parser.add_argument('--stamper-keyid', '--external-pgp-timestamper-keyid',
                        default="70B61F81",
                        help="PGP key ID to obtain email cross-timestamps from")
    parser.add_argument('--stamper-to', '--external-pgp-timestamper-to',
                        default="clear@stamper.itconsult.co.uk",
                        help="""destination email address
                            to obtain email cross-timestamps from""")
    parser.add_argument('--stamper-from', '--external-pgp-timestamper-from',
                        default="mailer@stamper.itconsult.co.uk",
                        help="""email address used by PGP timestamper
                            in its replies""")
    parser.add_argument('--stamper-smtp-server', '--smtp-server',
                        help="""SMTP server to use for
                            sending mail to PGP Timestamper""")
    parser.add_argument('--stamper-imap-server', '--imap-server',
                        help="""IMAP server to use for
                            receiving mail from PGP Timestamper""")
    parser.add_argument('--stamper-username', '--mail-username',
                        help="""username to use for IMAP and SMTP
                            (default from `--stamper-own-address`)""")
    parser.add_argument('--stamper-password', '--mail-password',
                        help="password to use for IMAP and SMTP")
    parser.add_argument('--no-dovecot-bug-workaround', action='store_true',
                        help="""Some Dovecot mail server seem unable to match
                            the last char of an email address in an IMAP
                            SEARCH, so this cuts off the last char from
                            `stamper-from`. Should not impact other mail
                            servers.""")

    arg = parser.parse_args(args=args, config_file_contents=config_file_contents)

    _logging.basicConfig()
    for level in str(arg.debug_level).split(','):
        if '=' in level:
            (logger, lvl) = level.split('=', 1)
        else:
            logger = None # Root logger
            lvl = level
        try:
            lvl = int(lvl)
            lvl = _logging.WARN - lvl * (_logging.WARN - _logging.INFO)
        except ValueError:
            # Does not work in Python 3.4.0 and 3.4.1
            # See note in https://docs.python.org/3/library/logging.html#logging.getLevelName
            lvl = _logging.getLevelName(lvl.upper())
        _logging.getLogger(logger).setLevel(lvl)

    if arg.stamper_username is None:
        arg.stamper_username = arg.stamper_own_address

    if arg.force_after_intervals < 2:
        sys.exit("--force-after-intervals must be >= 2")

    arg.commit_interval = autoblockchainify.deltat.parse_time(arg.commit_interval)
    if arg.stamper_own_address is None:
        if arg.commit_interval < datetime.timedelta(minutes=1):
            sys.exit("--commit-interval may not be shorter than 1m")
    else:
        if arg.commit_interval*arg.force_after_intervals < datetime.timedelta(minutes=10):
            sys.exit("--commit-interval times --force-after-intervals may "
                     "not be shorter than 10m when using the (mail-based) "
                     "PGP Digital Timestamping Service")

    if arg.commit_offset is None:
        # Avoid the seconds around the full interval, to avoid clustering
        # with other system activity.
        arg.commit_offset = arg.commit_interval * random.uniform(0.05, 0.95)
        logging.info("Chose --commit-offset %s" % arg.commit_offset)
    else:
        arg.commit_offset = autoblockchainify.deltat.parse_time(arg.commit_offset)
    if arg.commit_offset < datetime.timedelta(seconds=0):
        sys.exit("--commit-offset must be positive")
    if arg.commit_offset >= arg.commit_interval:
        sys.exit("--commit-offset must be less than --commit-interval")

    # Work around ConfigArgParse list bugs by implementing lists ourselves
    arg.zeitgitter_servers = arg.zeitgitter_servers.split()
    arg.push_repository = arg.push_repository.split()
    arg.push_branch = arg.push_branch.split()

    for i in arg.zeitgitter_servers:
        if not '=' in i:
            sys.exit("--upstream-timestamp requires (space-separated list of)"
                " <branch>=<url> arguments")

    if not arg.no_dovecot_bug_workaround:
        arg.stamper_from = arg.stamper_from[:-1] # See help text

    logging.debug("Settings applied: %s" % str(arg))
    return arg
