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
    Retries a function or method until it returns True.
    
    Original: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    """
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            try_one_last_time = True
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                    try_one_last_time = False
                    break
                except ExceptionToCheck, e:
                    sys.stderr.write('%s, Retrying in %d seconds...' % (str(e), mdelay))
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
                    sys.stderr.flush()
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry  # true decorator
    return deco_retry


class StreamingHttp:
    def __init__(self, username, password, host, path, use_https):
        self.username = username
        self.password = password
        self.host = host
        self.path = path
        self.use_https = use_https
        
        self.buffer = ''
        self.connection = None

    def connect(self, check_response=True):
        # Login using basic auth
        login = '%s:%s' % (self.username, self.password)
        token = 'Basic ' + str.strip(base64.encodestring(login))
        headers = {
            'Content-Length': '0',
            'Authorization': token,
            'Host': self.host,
            'User-Agent': 'splunk_streaming_http.py/0.1',
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


def cmdline():
    parser = optparse.OptionParser()
    parser.add_option('', '--https', action='store_true', dest='use_https')
    parser.add_option('-u', '--username', action='store', type='string', dest='username')
    parser.add_option('-p', '--password', action='store', type='string', dest='password')
    parser.add_option('', '--host', action='store', type='string', dest='host')
    parser.add_option('', '--path', action='store', type='string', dest='path')
    parser.add_option('', '--chunk', action='store', type='int', dest='chunk', default=10 * 1024)
    (opts, args) = parser.parse_args(sys.argv[1:])
    
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


def listen(username, password, host, path, use_https, chunk_size, out_stream=None):
    if out_stream is None:
        out_stream = sys.stdout
    
    streaming_http = StreamingHttp(username, password, host, path, use_https)
    stream = streaming_http.connect()
    
    is_gzip = False
    if stream.getheader('content-encoding', '') == 'gzip':
        is_gzip = True
        
    zlib_mode = 16 + zlib.MAX_WBITS
    decompressor = zlib.decompressobj(zlib_mode)

    buffer = ''
    tries = 0

    while True and tries < MAX_TRIES:
        # Read a chunk
        data = stream.read(chunk_size)
        
        if is_gzip:
            decompressed_data = decompressor.decompress(data)
            decompressed_data += decompressor.decompress(bytes())
            buffer = decompressed_data
        else:
            buffer = data
            
        out_stream.write(buffer)
        
        # Make sure we're actually making forward progress
        if len(buffer) == 0:
            tries += 1
        elif len(buffer) > 0:
            tries = 0
        
        buffer = ''
        
    if tries == MAX_TRIES:
        stream.close()
        raise Exception('Reached maximum read attempts')


# We encode all the logic for starting up the HTTP connection, 
# together with the actual processing
# logic into one function. This allows us to decorate it with
# the ability to keep retrying if an exception happens, using
# exponential backoff.
@retry(Exception)
def start(username, password, host, path, use_https, chunk_size, out_stream=None):
    try: 
        listen(username, password, host, path, use_https, chunk_size, out_stream)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise Exception()


def main():
    kwargs = cmdline()
    
    start(
        username=kwargs['username'],
        password=kwargs['password'], 
        host=kwargs['host'],
        path=kwargs['path'],
        use_https=kwargs['use_https'],
        chunk_size=kwargs['chunk'])

        
if __name__ == '__main__':
    main()
