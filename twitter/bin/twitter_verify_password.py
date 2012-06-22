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
Verifies whether a set of Twitter credentials are valid.

This script is invoked by Splunk whenever the user inputs new credentials
on the Twitter app's setup page, which is defined by `setup.xml`. If the
credentials are deemed invalid, an error message will be presented to the user
at the time the credentials are entered.
"""

from http_stream import AuthenticatedHttpConnection
import sys

def main():
    username = None
    password = None
    
    # Read args passed by splunkd. They look like:
    #   --<arg-name>=<arg-value>
    while True:
        line = sys.stdin.readline().strip()
        if len(line) == 0:
            break
        if line.startswith('--'):
            kv = line[2:].split('=', 1)
            if len(kv) == 2:
                if kv[0] == 'username':
                    username = kv[1]
                elif kv[0] == 'password':
                    password = kv[1]
    
    if username is None or password is None:
        raise Exception('Username or password argument not specified.')
    
    # Verify the password by connecting to the streaming API.
    # We'll get an HTTP 200 response if the username and password are valid.
    connection = AuthenticatedHttpConnection(
        username=username,
        password=password,
        host='stream.twitter.com',
        path='/1/statuses/sample.json?delimited=length',
        use_https=True)
    try:
        response = connection.connect(check_response=False)
        
        if response.status != 200:
           sys.stdout.write("--status=fail - %s\n" % response.status)
        else:
           sys.stdout.write("--status=success\n")
    finally:
        connection.close()

if __name__ == '__main__':
    main()
