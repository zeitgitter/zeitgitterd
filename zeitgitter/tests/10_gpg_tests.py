#!/usr/bin/python3 -tt
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

# Test GPG signature creation

import os
import pathlib
import tempfile
import threading

import zeitgitter.config
import zeitgitter.stamper


def assertEqual(a, b):
    if type(a) != type(b):
        raise AssertionError(
            "Assertion failed: Type mismatch %r (%s) != %r (%s)"
            % (a, type(a), b, type(b)))
    elif a != b:
        raise AssertionError(
            "Assertion failed: Value mismatch: %r (%s) != %r (%s)"
            % (a, type(a), b, type(b)))


def setup_module():
    global stamper
    global tmpdir
    tmpdir = tempfile.TemporaryDirectory()
    zeitgitter.config.get_args(args=[
        '--gnupg-home',
        str(pathlib.Path(os.path.dirname(os.path.realpath(__file__)),
                         'gnupg')),
        '--country', '', '--owner', '', '--contact', '',
        '--keyid', '353DFEC512FA47C7',
        '--own-url', 'https://hagrid.snakeoil',
        '--max-parallel-signatures', '10',
        '--max-parallel-timeout', '1',
        '--repository', tmpdir.name])
    stamper = zeitgitter.stamper.Stamper()
    os.environ['ZEITGITTER_FAKE_TIME'] = '1551155115'


def teardown_module():
    del os.environ['ZEITGITTER_FAKE_TIME']
    tmpdir.cleanup()


def oirset(start, end):
    """Set of the range of `ord()` values from `start` to `end`, inclusive"""
    return set(range(ord(start), ord(end)+1))


def test_commit():
    assert stamper.valid_commit('0123456789012345678901234567890123456789')
    assert stamper.valid_commit('0123456789abcdef678901234567890123456789')
    assert not stamper.valid_commit('012345678901234567890123456789012345678')
    assert not stamper.valid_commit('0123456789012345678901234567890123456789\n')
    assert not stamper.valid_commit('01234567890123456789012345678901234567890')
    assert not stamper.valid_commit('0123456789ABCDEF678901234567890123456789')
    assert not stamper.valid_commit('0123456789abcdefghij01234567890123456789')
    for i in (set(range(0, 255))
            - oirset('0', '9') - oirset('a', 'f')):
        commit = chr(i) * 40
        if stamper.valid_commit(commit):
            raise AssertionError(
                "Assertion failed: '%s' (%d) is valid commit" % (commit, i))


def test_tag():
    assert stamper.valid_tag('a')
    assert stamper.valid_tag('a' * 100)
    assert stamper.valid_tag('A' * 100)
    assert stamper.valid_tag('abcdefghijklmnopqrstuvwxyz0123456789-_')
    assert not stamper.valid_tag('')
    for i in (set(range(0, 255))
              - set((ord('-'), ord('_'), ord('.')))
              - oirset('0', '9') - oirset('A', 'Z') - oirset('a', 'z')):
        if stamper.valid_tag('a' + chr(i)):
            raise AssertionError(
                "Assertion failed: 'a%s' (%d) is valid tag" % (chr(i), i))
    for i in (set(range(0, 255))
              - set((ord('_'),))
              - oirset('A', 'Z') - oirset('a', 'z')):
        if stamper.valid_tag(chr(i)):
            raise AssertionError(
                "Assertion failed: '%s' (%d) is valid tag" % (chr(i), i))
    assert not stamper.valid_tag('a ')
    assert not stamper.valid_tag('0')
    assert not stamper.valid_tag('a' * 101)
    assert not stamper.valid_tag('..')


def test_pubkey():
    pubkey = stamper.get_public_key()
    assertEqual(pubkey, """-----BEGIN PGP PUBLIC KEY BLOCK-----

mQGiBFx0B0kRBACw2++3YW1ECOVsXBCd0RuXdIJHaJ8z4EfPhG6cnJWeITFawTBw
4uboTu2NZ99qWH/eEGcOGS38TZvZHbti65AeWkks8SV7nuwuWXF4td0+dVXkDieP
XTw7O8dCI8gDlvpCE+FSgzjzQjSSyYzsCju0GXCZYORrFzU2oILUzloe6wCgpP7l
nhd+0ulQyU87q/n12uLRO1ED+wT7sLS/+RVlwpKPc7cm9JQ/bJEDFOVn1RUWPPAI
lmZjhX78hf5xg6mwqOastH4i0D4CL3TjRzrbu2XF7Is86sp1NKlEXFeWUMpIeFak
eTcFg9DAyB+I84GZHFpXajC8fkz78rJvuDBwLa8p249kWOOb7MZnsLGJNM5mRk1D
uKu5A/97BIRhMYT2nKaR6TKE1QSs4dLG0/ZyGW30P+iYALqcRybHhJfNn2sVkAre
fo+5+id3NgWqU+/Zm+3QRLoHTKzrurR+amZ8EGoE3szlnLH1kkfSJqhN038e02Hn
osUGGIBpVW4IoTltElCX+wJrYF+EAFR5dGv6PjNTuKF7SKMH7bRDSGFncmlkIFNu
YWtlb2lsIFRpbWVzdG9tcGluZyBTZXJ2aWNlIDx0aW1lc3RvbXBpbmdAaGFncmlk
LnNuYWtlb2lsPoh4BBMRAgA4FiEEykr6smxYsglZnIAlNT3+xRL6R8cFAlx0B0kC
GwMFCwkIBwIGFQoJCAsCBBYCAwECHgECF4AACgkQNT3+xRL6R8e96QCffB81wYci
eUVPRmPROLObWS2mzfEAn1dMGgRB2pPRQeaayWyodleWuWZy
=w4y2
-----END PGP PUBLIC KEY BLOCK-----
""")


def test_sign_tag():
    tagstamp = stamper.stamp_tag('1' * 40, 'sample-timestamping-tag')
    print(tagstamp)
    assertEqual(tagstamp, """object 1111111111111111111111111111111111111111
type commit
tag sample-timestamping-tag
tagger Hagrid Snakeoil Timestomping Service <timestomping@hagrid.snakeoil> 1551155115 +0000

:watch: https://hagrid.snakeoil tag timestamp
-----BEGIN PGP SIGNATURE-----

iF0EABECAB0WIQTKSvqybFiyCVmcgCU1Pf7FEvpHxwUCXHS/qwAKCRA1Pf7FEvpH
xz10AJ4iSQRbbKVPFSk2hhORPBe8mEkzhQCcCmz/GQwmv4ZwTWE6G0ltXJ5oZ+Y=
=fFsz
-----END PGP SIGNATURE-----
""")


def test_sign_branch1():
    branchstamp = stamper.stamp_branch('1' * 40, '2' * 40, '3' * 40)
    print(branchstamp)
    assertEqual(branchstamp, """tree 3333333333333333333333333333333333333333
parent 2222222222222222222222222222222222222222
parent 1111111111111111111111111111111111111111
author Hagrid Snakeoil Timestomping Service <timestomping@hagrid.snakeoil> 1551155115 +0000
committer Hagrid Snakeoil Timestomping Service <timestomping@hagrid.snakeoil> 1551155115 +0000
gpgsig -----BEGIN PGP SIGNATURE-----
 
 iF0EABECAB0WIQTKSvqybFiyCVmcgCU1Pf7FEvpHxwUCXHS/qwAKCRA1Pf7FEvpH
 x017AJ0chjOGdSe1OuMa8PCuF/cP/bFHBQCeJuH81Wd6NinAIM699OJdMOiSM08=
 =cmOj
 -----END PGP SIGNATURE-----

:watch: https://hagrid.snakeoil branch timestamp 2019-02-26 04:25:15 UTC
""")


def test_sign_branch2():
    branchstamp = stamper.stamp_branch('1' * 40, None, '3' * 40)
    print(branchstamp)
    assertEqual(branchstamp, """tree 3333333333333333333333333333333333333333
parent 1111111111111111111111111111111111111111
author Hagrid Snakeoil Timestomping Service <timestomping@hagrid.snakeoil> 1551155115 +0000
committer Hagrid Snakeoil Timestomping Service <timestomping@hagrid.snakeoil> 1551155115 +0000
gpgsig -----BEGIN PGP SIGNATURE-----
 
 iF0EABECAB0WIQTKSvqybFiyCVmcgCU1Pf7FEvpHxwUCXHS/qwAKCRA1Pf7FEvpH
 x7FWAJ4vY50YYkvvGlrJRUH55LpFEPFiEgCdHALRIo5ueyk4UNdFJul2c5Hys9M=
 =aZZl
 -----END PGP SIGNATURE-----

:watch: https://hagrid.snakeoil branch timestamp 2019-02-26 04:25:15 UTC
""")


def test_multithreading1():
    stamper.extra_delay = 0.5
    threads = []
    for i in range(20):
        t = threading.Thread(target=test_sign_tag, name="test_multithreading1_%d" % i)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


counter_lock = threading.Lock()
counter = 0


def count_sign_tag():
    global counter
    try:
        test_sign_tag()
        with counter_lock:
            counter = counter + 1
    except AssertionError:
        pass


def test_multithreading5():
    stamper.extra_delay = 1.5
    threads = []
    for i in range(20):
        t = threading.Thread(target=count_sign_tag, name="test_multithreading5_%d" % i)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    print('counter =' + str(counter))
    assert (counter == 10)
