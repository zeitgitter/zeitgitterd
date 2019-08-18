#!/usr/bin/python3
#
# zeitgitter — Independent GIT Timestamping, HTTPS server
#
# Copyright (C) 2019 Marcel Waldvogel
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

import datetime
import logging
import os
import random

import configargparse
from zeitgitter import moddir
import zeitgitter.deltat
import zeitgitter.version


def get_args(args=None, config_file_contents=None):
    global arg
    # Config file in /etc or the program directory
    parser = configargparse.ArgumentParser(
        description="zeitgitterd.py — The Independent git Timestamper server.",
        default_config_files=['/etc/zeitgitter.conf',
            os.path.join(os.getenv('HOME'), 'zeitgitter.conf')])

    parser.add_argument('--config-file', '-c',
                        is_config_file=True,
                        help="config file path")
    parser.add_argument('--webconfig',
                        choices=('never', 'always', 'if-needed'),
                        default='if-needed',
                        help="allow web-based configuration on"
                            " <listen-address>:<listen-port> if configuration"
                            " is missing important parameters (those marked"
                            " with '(NECESSARY)' in this help)")
    parser.add_argument('--debug-level',
                        default=0, type=int,
                        help="increase debugging output")
    parser.add_argument('--keyid',
                        help="our PGP key ID to timestamp with (NECESSARY)")
    parser.add_argument('--own-url',
                        help="the URL of this service (NECESSARY)")
    parser.add_argument('--domain',
                        help="the domain name, for HTML substitution and SMTP greeting. "
                             "Defaults to host part of --own-url")
    parser.add_argument('--country',
                        help="the jurisdiction this falls under,"
                            " for HTML substitution (NECESSARY)")
    parser.add_argument('--owner',
                        help="owner and operator of this instance,"
                        " for HTML substitution (NECESSARY)")
    parser.add_argument('--contact',
                        help="contact for this instance,"
                        " for HTML substitution (NECESSARY)")
    parser.add_argument('--commit-interval',
                        default='4h',
                        help="how often to commit")
    parser.add_argument('--commit-offset',
                        help="when to commit within that interval; e.g. after 37m19.3s. "
                             "Default: Random choice in the interval")
    parser.add_argument('--webroot',
                        default=moddir('web'),
                        help="path to the webroot")
    parser.add_argument('--repository',
                        default=os.path.join(
                            os.getenv('HOME', '/var/lib/zeitgitter'), 'repo'),
                        help="path to the GIT repository")
    parser.add_argument('--upstream-timestamp',
                        default=
                          'diversity-timestamps=https://diversity.zeitgitter.net'
                          ' gitta-timestamps=https://gitta.zeitgitter.net',
                        help="any number of space-separated <branch>=<URL>"
                            " tuples of upstream IGITT timestampers")
    parser.add_argument('--listen-address',
                        default='127.0.0.1',  # Still not all machines support ::1
                        help="IP address to listen on")
    parser.add_argument('--listen-port',
                        default=8080, type=int,
                        help="port number to listen on")
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
                        help="GnuPG Home Dir to use (default from "
                            "$GNUPGHOME or $HOME/.gnupg)")
    parser.add_argument('--external-pgp-timestamper-keyid',
                        default="70B61F81",
                        help="PGP key ID to obtain email cross-timestamps from")
    parser.add_argument('--external-pgp-timestamper-to',
                        default="clear@stamper.itconsult.co.uk",
                        help="destination email address "
                             "to obtain email cross-timestamps from")
    parser.add_argument('--external-pgp-timestamper-reply',
                        default="mailer@stamper.itconsult.co.uk",
                        help="email address used by PGP timestamper "
                             "in its replies")
    parser.add_argument('--email-address',
                        help="our email address; enables "
                             "cross-timestamping from the PGP timestamper")
    parser.add_argument('--smtp-server',
                        help="SMTP server to use for "
                             "sending mail to PGP Timestamper")
    parser.add_argument('--imap-server',
                        help="IMAP server to use for "
                             "receiving mail from PGP Timestamper")
    parser.add_argument('--mail-username',
                        help="username to use for IMAP and SMTP")
    parser.add_argument('--mail-password',
                        help="password to use for IMAP and SMTP")
    parser.add_argument('--push-repository',
                        default='',
                        help="Space-separated list of repositores to push to; "
                             "setting this enables automatic push")
    parser.add_argument('--push-branch',
                        default='',
                        help="Space-separated list of branches to push")
    parser.add_argument('--version',
                        action='version', version=zeitgitter.version.VERSION)

    arg = parser.parse_args(args=args, config_file_contents=config_file_contents)

    if arg.webconfig == 'auto':
        # Disable when all 'NECESSARY' parameters are already set
        arg.webconfig = not (keyid is None or own_url is None
                or country is None or owner is None or contact is None)
    else if arg.webconfig == 'always':
        arg.webconfig = True
    else:
        arg.webconfig = False


    arg.commit_interval = zeitgitter.deltat.parse_time(arg.commit_interval)
    if arg.email_address is None:
        if arg.commit_interval < datetime.timedelta(minutes=1):
            sys.exit("--commit-interval may not be shorter than 1m")
    else:
        if arg.commit_interval < datetime.timedelta(minutes=30):
            sys.exit("--commit-interval may not be shorter than 30m when "
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

    if arg.domain is None:
        arg.domain = arg.own_url.replace('https://', '')

    # Work around ConfigArgParse list bugs by implementing lists ourselves
    arg.upstream_timestamp = arg.upstream_timestamp.split()
    arg.push_repository = arg.push_repository.split()
    arg.push_branch = arg.push_branch.split()

    for i in arg.upstream_timestamp:
        if not '=' in i:
            sys.exit("--upstream-timestamp requires (space-separated list of)"
                " <branch>=<url> arguments")

    level = logging.WARN - arg.debug_level * (logging.WARN - logging.INFO)
    logging.basicConfig(level=level)

    return arg
