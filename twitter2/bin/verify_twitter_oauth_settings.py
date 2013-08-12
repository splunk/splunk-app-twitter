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

This script is invoked by Splunk whenever the user inputs new credentials
on the Twitter app's setup page, which is defined by `setup.xml`. If the
credentials are deemed invalid, an error message will be presented to the user
at the time the credentials are entered.
"""

from twython import Twython, TwythonError
import optparse
import sys


def parse_arguments(args):
    parser = optparse.OptionParser()

    parser.add_option('', '--app_key', action='store', type='string',
                      dest='app_key')
    parser.add_option('', '--app_secret', action='store', type='string',
                      dest='app_secret')
    parser.add_option('', '--oauth_token', action='store', type='string',
                      dest='oauth_token')
    parser.add_option('', '--oauth_token_secret', action='store',
                      type='string',
                      dest='oauth_token_secret')

    (opts, args) = parser.parse_args(args)

    return vars(opts)

# pycharm

def main():
    # Read args passed by splunkd. They look like:
    #   --<arg-name>=<arg-value>
    args = []

    while True:
        line = sys.stdin.readline().strip()
        if len(line) == 0:
            break
        args.append(line)

    kwargs = parse_arguments(args)

    app_key = kwargs.get('app_key', None)
    app_secret = kwargs.get('app_secret', None)
    oauth_token = kwargs.get('oauth_token', None)
    oauth_token_secret = kwargs.get('oauth_token_secret')

    if app_key is None or app_secret is None or oauth_token is None or \
                    oauth_token_secret is None:
        raise Exception(
            'App_key, app_secret, oauth_token, or oauth_token_secret ' +
            'arguments not specified.')

    twitter = Twython(
        app_key=app_key,
        app_secret=app_secret,
        oauth_token=oauth_token,
        oauth_token_secret=oauth_token_secret)

    twitter.verify_credentials()

    try:
        twitter.verify_credentials()
        sys.stdout.write('--status=success\n')

    except TwythonError as e:
        sys.stdout.write('--status=fail - %s\n' % e.message)


if __name__ == '__main__':
    main()
