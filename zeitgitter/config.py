#!/usr/bin/python3
#
# zeitgitter — Independent GIT Timestamping, HTTPS server
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
import datetime
import logging as _logging
import os
import random
import sys

import configargparse

import zeitgitter.deltat
import zeitgitter.version

logging = _logging.getLogger('config')


def print_sample_config():
    from zeitgitter import moddir
    from pathlib import Path
    try:
        with Path(moddir(), 'sample.conf').open(mode='r') as f:
            print(f.read())
    except IOError:
        import importlib.resources
        print(importlib.resources.read_text('zeitgitter', 'sample.conf'))
    sys.exit(0)


def get_args(args=None, config_file_contents=None):
    global arg
    writeback = {}
    # Config file in /etc or the program directory
    parser = configargparse.ArgumentParser(
        auto_env_var_prefix="zeitgitter_",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="zeitgitterd.py — The Independent git Timestamping server.",
        default_config_files=['/etc/zeitgitter.conf',
                              os.path.join(os.getenv('HOME'), 'zeitgitter.conf')])

    # General
    parser.add_argument('--config-file', '-c',
                        is_config_file=True,
                        help="config file path")
    parser.add_argument('--print-sample-config',
                        action='store_true',
                        help="""output sample configuration file from package
                            and exit""")
    parser.add_argument('--debug-level',
                        default='INFO',
                        help="""amount of debug output: WARN, INFO, or DEBUG.
                            Debug levels for specific loggers can also be
                            specified using 'name=level'. Valid logger names:
                            `config`, `server`, `stamper`, `commit` (incl.
                            requesting cross-timestamps), `gnupg`, `mail`
                            (interfacing with PGP Timestamping Server).
                            Example: `DEBUG,gnupg=INFO` sets the default
                            debug level to DEBUG, except for `gnupg`.""")
    parser.add_argument('--version',
                        action='version', version=zeitgitter.version.VERSION)

    # Identity
    parser.add_argument('--keyid',
                        help="""the PGP key ID to timestamp with, creating
                            this key first if necessary.""")
    parser.add_argument('--own-url',
                        help="the URL of this service (REQUIRED)")
    parser.add_argument('--domain',
                        help="the domain name, for HTML substitution and SMTP greeting. "
                             "Defaults to host part of --own-url")
    parser.add_argument('--country',
                        help="the jurisdiction this falls under,"
                             " for HTML substitution (REQUIRED)")
    parser.add_argument('--owner',
                        help="owner and operator of this instance,"
                             " for HTML substitution (REQUIRED)")
    parser.add_argument('--contact',
                        help="contact for this instance,"
                             " for HTML substitution (REQUIRED)")

    # Server
    parser.add_argument('--webroot',
                        help="path to the webroot (fallback: in-module files)")
    parser.add_argument('--listen-address',
                        default='127.0.0.1',  # Still not all machines support ::1
                        help="IP address to listen on")
    parser.add_argument('--listen-port',
                        default=15177, type=int,
                        help="port number to listen on")

    # GnuPG
    parser.add_argument('--max-parallel-signatures',
                        default=2, type=int,
                        help="""maximum number of parallel timestamping operations.
                            Please note that GnuPG serializes all operations through
                            the gpg-agent, so parallelism helps very little""")
    parser.add_argument('--max-parallel-timeout',
                        type=float,
                        help="""number of seconds to wait for a timestamping thread
                            before failing (default: wait forever)""")
    parser.add_argument('--number-of-gpg-agents',
                        default=1, type=int,
                        help="number of gpg-agents to run")
    parser.add_argument('--gnupg-home',
                        default=os.getenv('GNUPGHOME',
                                          os.getenv('HOME', '/var/lib/zeitgitter') + '/.gnupg'),
                        help="""GnuPG Home Dir to use (default from $GNUPGHOME
                            or $HOME/.gnupg or /var/lib/zeitgitter/.gnupg)""")

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
    parser.add_argument('--repository',
                        default=os.path.join(
                            os.getenv('HOME', '/var/lib/zeitgitter'), 'repo'),
                        help="""path to the GIT repository (default from
                            $HOME/repo or /var/lib/zeitgitter/repo)""")
    parser.add_argument('--upstream-timestamp',
                        default='diversity gitta',
                        help="""any number of space-separated upstream
                             Zeitgitter servers of the form
                             `[<branch>=]<server>`. The server name will
                             be passed with `--server` to `git timestamp`,
                             the (optional) branch name with `--branch`.""")
    parser.add_argument('--upstream-sleep',
                        default='0s',
                        help="""Delay between cross-timestamping for the
                             different timestampers""")

    # Pushing
    parser.add_argument('--push-repository',
                        default='',
                        help="""Space-separated list of repositores to push to;
                            setting this enables automatic push""")
    parser.add_argument('--push-branch',
                        default='*',
                        help="""Space-separated list of branches to push.
                            `*` means all, as `--all` is eaten by ConfigArgParse""")

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

    if arg.print_sample_config:
        print_sample_config()
        sys.exit(0)

    # To be able to support `--print-sample-config`, we need to handle
    # `required` attributes ourselves
    missing = []
    if arg.owner is None:
        missing.append("--owner")
    if arg.contact is None:
        missing.append("--contact")
    if arg.country is None:
        missing.append("--country")
    if arg.own_url is None:
        missing.append("--own-url")
    if len(missing):
        parser.print_help()
        sys.exit("Required arguments missing: " + ", ".join(missing))

    _logging.basicConfig()
    for level in str(arg.debug_level).split(','):
        if '=' in level:
            (logger, lvl) = level.split('=', 1)
        else:
            logger = None  # Root logger
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

    arg.commit_interval = zeitgitter.deltat.parse_time(arg.commit_interval)
    if arg.stamper_own_address is None:
        if arg.commit_interval < datetime.timedelta(minutes=1):
            sys.exit("--commit-interval may not be shorter than 1m")
    else:
        if arg.commit_interval < datetime.timedelta(minutes=10):
            sys.exit("--commit-interval may not be shorter than 10m when "
                     "using the PGP Digital Timestamper")

    if arg.commit_offset is None:
        # Avoid the seconds around the full interval, to avoid clustering
        # with other system activity.
        arg.commit_offset = arg.commit_interval * random.uniform(0.05, 0.95)
        logging.info("Chose --commit-offset %s" % arg.commit_offset)
    else:
        arg.commit_offset = zeitgitter.deltat.parse_time(arg.commit_offset)
    if arg.commit_offset < datetime.timedelta(seconds=0):
        sys.exit("--commit-offset must be positive")
    if arg.commit_offset >= arg.commit_interval:
        sys.exit("--commit-offset must be less than --commit-interval")

    arg.upstream_sleep = zeitgitter.deltat.parse_time(arg.upstream_sleep)

    if arg.domain is None:
        arg.domain = arg.own_url.replace('https://', '')

    # Work around ConfigArgParse list bugs by implementing lists ourselves
    # and working around the problem that values cannot start with `-`.
    arg.upstream_timestamp = arg.upstream_timestamp.split()
    arg.push_repository = arg.push_repository.split()
    if arg.push_branch == '*':
        arg.push_branch = ['--all']
    else:
        arg.push_branch = arg.push_branch.split()

    if not arg.no_dovecot_bug_workaround:
        arg.stamper_from = arg.stamper_from[:-1]  # See help text

    return arg
