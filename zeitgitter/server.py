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

# HTTP request handling


import cgi
import importlib.resources
import logging as _logging
import os
import re
import socket
import socketserver
import subprocess
import urllib
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import zeitgitter.commit
import zeitgitter.config
import zeitgitter.stamper
import zeitgitter.version
from zeitgitter import moddir

logging = _logging.getLogger('server')


class SocketActivationMixin:
    """Use systemd provided socket, if available.
    When socket activation is used, exactly one socket needs to be passed."""

    def server_bind(self):
        nfds = 0
        if os.environ.get('LISTEN_PID', None) == str(os.getpid()):
            nfds = int(os.environ.get('LISTEN_FDS', 0))
            if nfds == 1:
                self.socket = socket.socket(fileno=3)
            else:
                logging.error("Socket activation must provide exactly one socket (for now)\n")
                exit(1)
        else:
            super().server_bind()


class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Replacement for http.server.ThreadingHTTPServer for Python < 3.7"""
    pass


class SocketActivationHTTPServer(SocketActivationMixin, ThreadingHTTPServer):
    pass


class FlatFileRequestHandler(BaseHTTPRequestHandler):
    def send_file(self, content_type, filename, replace={}):
        try:
            webroot = zeitgitter.config.arg.webroot
            if webroot is None:
                webroot = moddir('web')
            if webroot and os.path.isdir(webroot):
                with Path(webroot, filename).open(mode='rb') as f:
                    contents = f.read()
            else:
                contents = importlib.resources.read_binary('zeitgitter', filename)
            for k, v in replace.items():
                contents = contents.replace(k, v)
            self.send_response(200)
            if content_type.startswith('text/'):
                self.send_header('Content-Type', content_type + '; charset=UTF-8')
            else:
                self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(contents))
            self.end_headers()
            self.wfile.write(contents)
        except IOError as e:
            self.send_bodyerr(404, "File not found",
                              "This file was not found on this server")

    def send_bodyerr(self, status, title, body):
        explain = """<html><head><title>%s</title></head>
<body><h1>%s</h1>%s
<p><a href="/">Go home</a></p></body></html>
""" % (title, title, body)
        explain = bytes(explain, 'UTF-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=UTF-8')
        self.send_header('Content-Length', len(explain))
        self.end_headers()
        self.wfile.write(explain)

    def do_GET(self):
        subst = {b'ZEITGITTER_DOMAIN': bytes(zeitgitter.config.arg.domain, 'UTF-8'),
                 b'ZEITGITTER_OWNER': bytes(zeitgitter.config.arg.owner, 'UTF-8'),
                 b'ZEITGITTER_CONTACT': bytes(zeitgitter.config.arg.contact, 'UTF-8'),
                 b'ZEITGITTER_COUNTRY': bytes(zeitgitter.config.arg.country, 'UTF-8')}

        if self.path == '/':
            self.send_file('text/html', 'index.html', replace=subst)
        else:
            match = re.match('^/([a-z0-9][-_.a-z0-9]*).(html|css|js|png|jpe?g|svg)$',
                             self.path, re.IGNORECASE)
            mimemap = {
                'html': 'text/html',
                'css': 'text/css',
                'js': 'text/javascript',
                'png': 'image/png',
                'svg': 'image/svg+xml',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg'}
            if match and match.group(2) in mimemap:
                if match.group(2) == 'html':
                    self.send_file(mimemap[match.group(2)], self.path[1:],
                                   replace=subst)
                else:
                    self.send_file(mimemap[match.group(2)], self.path[1:])
            else:
                self.send_bodyerr(406, "Illegal file name",
                                  "<p>This type of file/path is not served here.</p>")


stamper = None
public_key = None


def ensure_stamper(start_multi_threaded=False):
    global stamper
    if stamper is None:
        stamper = zeitgitter.stamper.Stamper()
    if start_multi_threaded:
        stamper.start_multi_threaded()


class StamperRequestHandler(FlatFileRequestHandler):
    def __init__(self, *args, **kwargs):
        ensure_stamper()
        self.protocol_version = 'HTTP/1.1'
        super().__init__(*args, **kwargs)

    def version_string(self):
        return "zeitgitter/" + zeitgitter.version.VERSION

    def send_public_key(self):
        global stamper, public_key
        if public_key == None:
            public_key = stamper.get_public_key()
        if public_key == None:
            self.send_bodyerr(500, "Internal server error",
                              "<p>No public key found</p>")
        else:
            pk = bytes(public_key, 'ASCII')
            self.send_response(200)
            self.send_header('Content-Type', 'application/pgp-keys')
            self.send_header('Content-Length', len(pk))
            self.end_headers()
            self.wfile.write(pk)

    def handle_signature(self, params):
        global stamper
        if 'request' in params:
            if (params['request'][0] == 'stamp-tag-v1'
                    and 'commit' in params and 'tagname' in params):
                return stamper.stamp_tag(params['commit'][0],
                                         params['tagname'][0])
            elif (params['request'][0] == 'stamp-branch-v1'
                  and 'commit' in params and 'tree' in params):
                if 'parent' in params:
                    return stamper.stamp_branch(params['commit'][0],
                                                params['parent'][0],
                                                params['tree'][0])
                else:
                    return stamper.stamp_branch(params['commit'][0],
                                                None,
                                                params['tree'][0])
        else:
            return 406

    def handle_request(self, params):
        sig = self.handle_signature(params)
        if sig == 406:
            self.send_bodyerr(406, "Unsupported timestamping request",
                              "<p>See the documentation for the accepted requests</p>")
        elif sig == None:
            self.send_bodyerr(429, "Too many requests",
                              "<p>The server is currently overloaded</p>")
        else:
            sig = bytes(sig, 'ASCII')
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-git-object')
            self.send_header('Content-Length', len(sig))
            self.end_headers()
            self.wfile.write(sig)

    def do_POST(self):
        self.method = 'POST'
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
        try:
            clen = self.headers['Content-Length']
            clen = int(clen)
        except:
            self.send_bodyerr(411, "Length required",
                              "<p>Your request did not contain a valid length</p>")
            return
        if clen > 1000 or clen < 0:
            self.send_bodyerr(413, "Request too long",
                              "<p>Your request is too long</p>")
            return
        if ctype == 'multipart/form-data':
            params = cgi.parse_multipart(self.rfile, pdict)
            self.handle_request(params)
        elif ctype == 'application/x-www-form-urlencoded':
            contents = self.rfile.read(clen)
            contents = contents.decode('UTF-8')
            params = urllib.parse.parse_qs(contents)
            self.handle_request(params)
        else:
            self.send_bodyerr(415, "Unsupported media type",
                              "<p>Need form data input</p>")

    def do_GET(self):
        self.method = 'GET'
        if self.path.startswith('/?'):
            params = urllib.parse.parse_qs(self.path[2:])
            if 'request' in params and params['request'][0] == 'get-public-key-v1':
                self.send_public_key()
            else:
                self.send_bodyerr(406, "Bad parameters",
                                  "<p>Need a valid `request` parameter</p>")
        else:
            super().do_GET()

    def send_response(self, code, message=None):
        if code != 200 and self.method == 'HEAD':
            self.method = self.method + '+error'
        super().send_response(code, message)

    def end_headers(self):
        """If it is a successful HEAD request, drop the body.
        Evil hack for minimal HEAD support."""
        super().end_headers()
        if self.method == 'HEAD':
            self.wfile.close()
            self.rfile.close()

    def do_HEAD(self):
        self.method = 'HEAD'
        self.do_GET()


def finish_setup(arg):
    # 1. Determine or create key, if possible
    #    (Not yet ready to use global stamper)
    arg.keyid = zeitgitter.stamper.get_keyid(arg.keyid,
                                             arg.domain, arg.gnupg_home)
    # Now, we're ready
    ensure_stamper()

    # 2. Create git repository, if necessary
    #    and set user name/email
    repo = zeitgitter.config.arg.repository
    Path(repo).mkdir(parents=True, exist_ok=True)
    if not Path(repo, '.git').is_dir():
        logging.info("Initializing new repo with user info")
        subprocess.run(['git', 'init'], cwd=repo, check=True)
        (name, mail) = stamper.fullid[:-1].split(' <')
        subprocess.run(['git', 'config', 'user.name', name],
                       cwd=repo, check=True)
        subprocess.run(['git', 'config', 'user.email', mail],
                       cwd=repo, check=True)

    # 3. Create initial files in repo, when needed
    #    (`hashes.work` will be created on demand).
    #    Will be committed with first commit.
    pubkey = Path(repo, 'pubkey.asc')
    if not pubkey.is_file():
        logging.info("Storing pubkey.asc in repository")
        with pubkey.open('w') as f:
            f.write(stamper.get_public_key())
        subprocess.run(['git', 'add', 'pubkey.asc'],
                       cwd=repo, check=True)
        subprocess.run(['git', 'commit', '-m', 'Started timestamping'],
                       cwd=repo, check=True)


def run():
    zeitgitter.config.get_args()
    finish_setup(zeitgitter.config.arg)
    zeitgitter.commit.run()
    httpd = SocketActivationHTTPServer(
        (zeitgitter.config.arg.listen_address,
         zeitgitter.config.arg.listen_port),
        StamperRequestHandler)
    logging.info("Start serving")
    ensure_stamper(start_multi_threaded=True)
    # Try to resume a waiting for a PGP Timestamping Server reply, if any
    if zeitgitter.config.arg.stamper_own_address:
        repo = zeitgitter.config.arg.repository
        preserve = Path(repo, 'hashes.stamp')
        if preserve.exists():
            logging.info("possibly resuming cross-timestamping by mail")
            zeitgitter.mail.async_email_timestamp(preserve)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Received Ctrl-C, shutting down...")
    httpd.server_close()
