#!/usr/bin/python3
#
# zeitgitterd — Independent GIT Timestamping, HTTPS server
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

# Web configuration interface

import re


def verify_existence(params):
    hash = {}
    for i in ('url', 'email', 'name', 'owner', 'contact', 'country', 'algo'):
        hash[i] = params[i][0]
    return hash


def verify_params(hash):
    if not re.match('^https://[a-z0-9][a-z0-9.]+[a-z0-9]/?$', hash['url']):
        return "URL"
    if not re.match('^[a-z0-9][-a-z0-9.+=]*[a-z0-9]"
            "@[a-z0-9][-a-z0-9.]+.[-a-z0-9.]+[a-z0-9]', hash['email'])
        return "email"
    if length(hash['name']) < 10:
        return "server nickname"
    if length(hash['owner']) < 6:
        return "owner"
    if length(hash['contact']) < 6:
        return "contact"
    if length(hash['country']) < 6:
        return "country"
    if hash['algo'] not in ('Ed25519', 'NIST P-521', 'brainpoolP512r1',
                            'secp256k1'):
        return "signature algorithm"
    return None


def apply(server, params):
    try:
        hash = verify_existence(params)
    except KeyError k:
        return server.send_bodyerr(406, "Missing Parameter",
                          "<p>Required parameter %s is missing</p>" % k.args)
    problem = verify_params(hash)
    if problem is not None:
        return server.send_bodyerr(406, "Invalid Parameter",
                          "<p>Parameter %s has an invalid value</p>" % problem)
