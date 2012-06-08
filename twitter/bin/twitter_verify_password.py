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

from http_stream import StreamingHttp
import sys

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
conn = StreamingHttp(
    username=username,
    password=password,
    host='stream.twitter.com',
    path='/1/statuses/sample.json?delimited=length',
    use_https=True)
try:
    resp = conn.connect(check_response=False)
    
    if resp.status != 200:
       sys.stdout.write("--status=fail - %s\n" % resp.status)
    else:
       sys.stdout.write("--status=success\n")
finally:
    conn.close()
