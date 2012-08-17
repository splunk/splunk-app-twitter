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
Scripted input that streams data from Twitter's 1% sample feed to standard
output, with each event on a separate line in JSON format.

The original JSON from Twitter is augmented with an extra '__time' key on each
event. This makes it possible for Splunk to use a regex to parse out the
timestamp accurately.
"""

import http_stream
import json
import splunk
import splunklib.client
import sys


class LineBufferedOutputStream(object):
    def __init__(self, write_line_func, terminator='\r\n'):
        self.buffer = ''
        self.write_line_func = write_line_func
        self.terminator = terminator
    
    def write(self, bytes):
        self.buffer += bytes
        
        start_search_pos = max(0,
            len(self.buffer) - len(bytes) - len(self.terminator))
        while True:
            pos = self.buffer.find(self.terminator, start_search_pos)
            if pos == -1:
                break
            else:
                self.write_line_func(self.buffer[0:pos])
                self.buffer = self.buffer[pos + len(self.terminator):]
                start_search_pos = 0
    
    def close(self):
        # If buffer is non-empty, its contents are lost
        pass


def write_twitter_line(line):
    try:
        line_obj = json.loads(line)
    except Exception, e:
        # Invalid JSON
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        return
    
    # Generate a synthetic field with the desired timestamp
    if 'created_at' in line_obj:
        line_obj['__time'] = line_obj['created_at']
    
    json.dump(line_obj, sys.stdout,
        # Preserve compact output format
        separators=(',', ':'))
    sys.stdout.write('\r\n')


def get_credentials(session_key):
    """
    Reads the user's Twitter credentials from the `admin/passwords` endpoint
    on the Splunk server.
    
    These credentials are entered by the user on the setup page for this app,
    which is defined by `setup.xml`.
    """
    
    # NOTE: Requires 'develop' version of splunklib past 0.8.0
    #       for 'token' parameter to be honored.
    service = splunklib.client.Service(
        host=splunk.getDefault('host'),
        port=splunk.getDefault('port'),
        scheme=splunk.getDefault('protocol'),
        owner='nobody',
        app='twitter2',
        token='Splunk %s' % session_key)
    
    # Return first set of credentials
    passwords = splunklib.client.Collection(service, 'admin/passwords')
    for password in passwords:
        return password['username'], password['clear_password']
    
    sys.stderr.write('Could not get Twitter credentials from splunk. Error: No credentials supplied, please complete the Twitter app setup\n')
    exit(1)


def main():
    # Read session key from splunkd
    session_key = sys.stdin.readline().strip()
    if len(session_key) == 0:
        sys.stderr.write('Did not receive a session key from splunkd. Please enable passAuth in inputs.conf for this script\n')
        exit(2)
    
    username, password = get_credentials(session_key)
    
    http_stream.start(
        username=username,
        password=password,
        host='stream.twitter.com',
        path='/1/statuses/sample.json',
        use_https=True,
        chunk_size=102400,
        out_stream=LineBufferedOutputStream(write_twitter_line))


if __name__ == '__main__':
    main()
