#!/usr/bin/python3
#
# autoblockchainify — Turn a directory into a GIT Blockchain
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

# Set up the daemon


import logging as _logging
import subprocess
from pathlib import Path

import autoblockchainify.commit
import autoblockchainify.config
import autoblockchainify.version

logging = _logging.getLogger('daemon')


def finish_setup(arg):
    # Create git repository, if necessary and set user name/email
    repo = autoblockchainify.config.arg.repository
    Path(repo).mkdir(parents=True, exist_ok=True)
    if not Path(repo, '.git').is_dir():
        subprocess.run(['git', 'init'], cwd=repo, check=True)
        # Default identity is forced onto new repositories only;
        # otherwise, the default is not to change the user settings.
        if arg.identity is None:
            arg.identity = 'Autoblockchainify <autoblockchainify@localhost>'
        # Ignore 'pgp-timestamper.rev'
        if not Path(repo, '.gitignore').is_file():
            with open(Path(repo, '.gitignore'), 'a') as ignore:
                ignore.write('pgp-timestamp.tmp\n')
    if arg.identity is not None:
        logging.info("Initializing new repo with user info")
        (name, mail) = arg.identity.split(' <')
        subprocess.run(['git', 'config', 'user.name', name],
                       cwd=repo, check=True)
        subprocess.run(['git', 'config', 'user.email', mail[:-1]],
                       cwd=repo, check=True)


def run():
    autoblockchainify.config.get_args()
    finish_setup(autoblockchainify.config.arg)
    # Try to resume waiting for a PGP Timestamping Server reply, if any
    if autoblockchainify.config.arg.stamper_own_address:
        repo = autoblockchainify.config.arg.repository
        logging.info("possibly resuming cross-timestamping by mail")
        autoblockchainify.mail.async_email_timestamp(resume=True)
    autoblockchainify.commit.loop()
