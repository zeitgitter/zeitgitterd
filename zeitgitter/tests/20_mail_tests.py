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

# Test mail sending/receiving

# All the information needs to be passed in environment variables, as the
# credentials cannot be included in the test suite:
# ZEITGITTER_SMTP_SERVER, ZEITGITTER_IMAP_SERVER, ZEITGITTER_USERNAME, ZEITGITTER_PASSWORD, ZEITGITTER_MAILADDRESS


import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import zeitgitter.config
import zeitgitter.mail
import zeitgitter.stamper


def environment_ok():
    for i in ('ZEITGITTER_SMTP_SERVER', 'ZEITGITTER_IMAP_SERVER',
              'ZEITGITTER_USERNAME', 'ZEITGITTER_PASSWORD',
              'ZEITGITTER_MAILADDRESS'):
        if not i in os.environ:
            return False
    return True


def assertEqual(a, b):
    if type(a) != type(b):
        raise AssertionError(
            "Assertion failed: Type mismatch %r (%s) != %r (%s)"
            % (a, type(a), b, type(b)))
    elif a != b:
        raise AssertionError(
            "Assertion failed: Value mismatch: %r (%s) != %r (%s)"
            % (a, type(a), b, type(b)))


@unittest.skipUnless(environment_ok(), "ZEITGITTER_* environment variables missing")
class MailTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        zeitgitter.config.get_args(args=[
            '--gnupg-home',
            str(Path(os.path.dirname(os.path.realpath(__file__)),
                     'gnupg')),
            '--keyid', '353DFEC512FA47C7',
            '--own-url', 'https://hagrid.snakeoil',
            '--max-parallel-timeout', '1',
            '--repository', self.tmpdir.name,
            '--mail-address', os.environ['ZEITGITTER_MAILADDRESS'],
            '--imap-server', os.environ['ZEITGITTER_IMAP_SERVER'],
            '--smtp-server', os.environ['ZEITGITTER_SMTP_SERVER'],
            '--mail-username', os.environ['ZEITGITTER_USERNAME'],
            '--mail-password', os.environ['ZEITGITTER_PASSWORD'],
            # Send test mails to self
            '--external-pgp-timestamper-to', os.environ['ZEITGITTER_MAILADDRESS'],
            '--external-pgp-timestamper-reply', os.environ['ZEITGITTER_MAILADDRESS']
        ])

    #    self.stamper = zeitgitter.stamper.Stamper()

    def tearDown(self):
        self.tmpdir.cleanup()

    testbody = '''Stamper is a service provided free of charge to Internet users.

You are very welcome to use Stamper, but you may only do so if 
you have first read our Terms of use, which exclude liability on 
our part and which provide for you to indemnify us against any 
potential liability arising from your use of Stamper.  By using 
Stamper you warrant that you have read and accept the Terms.

The Terms of use are available by sending email to 
info@stamper.itconsult.co.uk or from the web page 
http://www.itconsult.co.uk/stamper.htm.

-----BEGIN PGP SIGNED MESSAGE-----

########################################################
#
# The text of this message was stamped by
# stamper.itconsult.co.uk with reference 1069430
# at 16:55 (GMT) on Monday 11 March 2019
#
# For information about the Stamper service see
#        http://www.itconsult.co.uk/stamper.htm
#
########################################################

40324f75a41642f1abf9cf9305f46aa6bfa567e2
73abac26438e48d2af7476f564b97a7baba14645
3f4f63f7dde84822b24e348fd16d50b0aec93fb9
4cd7b8798a6e4c0a9c76ade2b6041b8e1a779458
a8254faa27394f4d893c80d899169d40b6a4d324
98f08d97f53d426e91affe8e1c7fb05688884435
303cc43ce91547a89daea16c7a695d9896585f17
fa94ffe675454658bd11219693d60844b995a74d



-----BEGIN PGP SIGNATURE-----
Version: 2.6.3i
Charset: noconv
Comment: Stamper Reference Id: 1069430

iQEVAgUBXIaS5IGVnbVwth+BAQEiwQf+JWhf0Vgy16Md5WpB/th4oYP5WMix7R3Y
6Dhr433k9DZiieRHL6GWsCzuU4bo2/ADXMYrUDzw+7mWMUxwWyJBX/IaxJWQXyD/
eR2/7WIP23vsOopnirRyZdiJ+OiSxLKNN2IgxAs73Sy0W69tIaCP0WRfZcbQd+15
5g2bI6gZlIle9nGnIveXJqsGGnl+OJa9lW90hSwz3+yN02UEX/zN4QxRmZCL402p
kHoZMCubtmPBZYScn9TI+vlg+fYHtmk1YJKetXoiblxiJXywNKe4umMjQgOdu5Ia
svIDuY71obFkHtgqAXFK4zMXjcm7t3R2GxUqLA760bptwoF1mDOFSA==
=UMWh
-----END PGP SIGNATURE-----
'''

    def test_10_send_mail(self):
        zeitgitter.mail.send(self.testbody)

    def test_20_receive_mail(self):
        p = Path(zeitgitter.config.arg.repository, 'hashes.log')
        with open(p, 'w') as f:
            f.write('''40324f75a41642f1abf9cf9305f46aa6bfa567e2
73abac26438e48d2af7476f564b97a7baba14645
3f4f63f7dde84822b24e348fd16d50b0aec93fb9
4cd7b8798a6e4c0a9c76ade2b6041b8e1a779458
a8254faa27394f4d893c80d899169d40b6a4d324
98f08d97f53d426e91affe8e1c7fb05688884435
303cc43ce91547a89daea16c7a695d9896585f17
fa94ffe675454658bd11219693d60844b995a74d
''')
        ftime = datetime(year=2019, month=3, day=11,
                         hour=16, minute=55, second=0,
                         tzinfo=timezone.utc).timestamp()
        os.utime(p, times=(ftime, ftime))
        # Receive the mail from the previous test
        zeitgitter.mail.receive_async()
