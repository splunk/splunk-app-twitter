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
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Verifies whether a set of Twitter credentials are valid.

This script is invoked by `forms.py` whenever the user inputs new credentials
on the Twitter app's setup page. If the credentials are deemed invalid,
an error message will be presented to the user at the time the credentials
are entered.
"""

from twython import Twython, TwythonError
import sys

def main(args):
    (_, api_key, api_secret, access_token, access_token_secret) = args
    
    twitter = Twython(
        app_key=api_key,
        app_secret=api_secret,
        oauth_token=access_token,
        oauth_token_secret=access_token_secret)
    try:
        twitter.verify_credentials()
    except TwythonError:
        # Invalid credentials
        return 1
    
    # Okay
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
