#!/usr/bin/env python
#
# Copyright 2012 Splunk, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"): you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, sofaare 
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT 
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the 
# License for the specific language governing permissions and limitations 
# under the License.

"""
Connects to an HTTP or HTTPS URL and streams its content to standard output
or to a user-provided output stream.

This script can be used as a standalone command-line program or imported as a
module and invoked directly via either the `start` method or the
`read_http_stream` method.
"""

import base64
from getpass import getpass
import httplib
import json
import sys
import time
import traceback
import optparse
import zlib


# Maximum number of times to try reading from the HTTP(S) socket before
# giving up and closing the stream.
MAX_TRIES = 100


def retry(ExceptionToCheck, tries=10, delay=3, backoff=2):
    """
    Retry decorator with exponential backoff.
    Retries a function or method until it does not throw the specified exception type.
    Returns `None` if the maximum number of retries is exceeded.
    
    Original: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    """
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, e:
                    sys.stderr.write('%s, Retrying in %d seconds...\n' % (str(e), mdelay))
                    sys.stderr.flush()
                    
                    time.sleep(mdelay)
                    
                    mtries -= 1
                    mdelay *= backoff
                    continue
            
            return None
        return f_retry  # true decorator
    return deco_retry


class AuthenticatedHttpConnection:
    """
    Represents a connection to an HTTP(S) URL that requires authentication.
    """
    
    def __init__(self, username, password, host, path, use_https):
        self.username = username
        self.password = password
        self.host = host
        self.path = path
        self.use_https = use_https
        
        self.connection = None

    def connect(self, check_response=True):
        # Login using basic auth
        login = '%s:%s' % (self.username, self.password)
        token = 'Basic ' + str.strip(base64.encodestring(login))
        headers = {
            'Content-Length': '0',
            'Authorization': token,
            'Host': self.host,
            'User-Agent': 'http_stream.py/0.1',
            'Accept': '*/*',
            'Accept-Encoding': '*,gzip'
        }
        
        if self.use_https:
            self.connection = httplib.HTTPSConnection(self.host)
        else:
            self.connection = httplib.HTTPConnection(self.host)
        self.connection.request('GET', self.path, '', headers)
        response = self.connection.getresponse()
        if check_response and response.status != 200:
            raise Exception('HTTP Error %d (%s)' % (
                response.status, response.reason))

        return response
    
    def close(self):
        self.connection.close()


def parse_arguments(args):
    parser = optparse.OptionParser()
    parser.add_option('', '--https', action='store_true', dest='use_https')
    parser.add_option('-u', '--username', action='store', type='string', dest='username')
    parser.add_option('-p', '--password', action='store', type='string', dest='password')
    parser.add_option('', '--host', action='store', type='string', dest='host')
    parser.add_option('', '--path', action='store', type='string', dest='path')
    parser.add_option('', '--chunk', action='store', type='int', dest='chunk', default=10 * 1024)
    (opts, args) = parser.parse_args(args)
    
    kwargs = vars(opts)
    
    # Prompt for HTTP username/password/host/path if not provided on command line
    if not 'username' in kwargs or not kwargs['username']:
        kwargs['username'] = raw_input('HTTP stream username: ')
    if not 'password' in kwargs or not kwargs['password']:
        kwargs['password'] = getpass('HTTP stream password: ')
    if not 'host' in kwargs or not kwargs['host']:
        kwargs['host'] = raw_input('HTTP stream host: ')
    if not 'path' in kwargs or not kwargs['path']:
        kwargs['path'] = raw_input('HTTP stream path: ')

    return kwargs


def read_http_stream(username, password, host, path, use_https, chunk_size=None, out_stream=None):
    """
    Continuously reads from the specified HTTP(S) URL and writes its contents to
    the specified output stream (or `sys.stdout` if no stream is provided).
    
    Never returns, unless an I/O error occurs.
    
    :param username:    the username to authenticate with.
    :param password:    the password to authenticate with.
    :param host:        the hostname to connect to.
    :param path:        the path to request on the HTTP server.
    :param use_https:   whether to use HTTP (`False`) HTTPS or (`True`).
    :param chunk_size:  (optional) size of the internal buffer that data will
                        be downloaded to.
    :param out_stream:  (optional) a file-like object that data will be written to.
                        Must support a `write` method. Defaults to `sys.stdout`.
    :raises Exception:  if no data can be read from the URL after a sufficent
                        number of tries.
    """
    
    if chunk_size is None:
        chunk_size = 102400
    if out_stream is None:
        out_stream = sys.stdout
    
    connection = AuthenticatedHttpConnection(
        username, password, host, path, use_https)
    stream = connection.connect()
    
    is_gzip = False
    if stream.getheader('content-encoding', '') == 'gzip':
        is_gzip = True
        
    zlib_mode = 16 + zlib.MAX_WBITS
    decompressor = zlib.decompressobj(zlib_mode)

    tries = 0
    while tries < MAX_TRIES:
        # Read a chunk
        data = stream.read(chunk_size)
        
        if is_gzip:
            decompressed_data = decompressor.decompress(data)
            buffer = decompressed_data
        else:
            buffer = data
            
        out_stream.write(buffer)
        
        # Make sure we're actually making forward progress
        if len(buffer) == 0:
            tries += 1
        elif len(buffer) > 0:
            tries = 0
    
    stream.close()
    raise Exception('Reached maximum read attempts.')


@retry(Exception)
def start(username, password, host, path, use_https, chunk_size=None, out_stream=None):
    """
    Continuously reads from the specified HTTP(S) URL and writes its contents to
    the specified output stream (or `sys.stdout` if no stream is provided).
    
    If a connection cannot be established initially, exponential backoff will be
    used to retry.
    
    Never returns, unless multiple attempts to read from the URL have failed.
    
    .. seealso:: :py:func:`read_http_stream`
    """
    
    try: 
        read_http_stream(username, password, host, path, use_https, chunk_size, out_stream)
    except KeyboardInterrupt:
        pass
    except Exception:
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise


def main():
    kwargs = parse_arguments(sys.argv[1:])
    
    start(
        username=kwargs['username'],
        password=kwargs['password'], 
        host=kwargs['host'],
        path=kwargs['path'],
        use_https=kwargs['use_https'],
        chunk_size=kwargs['chunk'])

        
if __name__ == '__main__':
    main()
