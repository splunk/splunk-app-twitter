# Splunk-Twitter Connector

This app provides a scripted input for [Splunk](http://www.splunk.com/) that
automatically extracts tweets from [Twitter](https://twitter.com/)'s [1% sample
stream](https://dev.twitter.com/docs/api/1/get/statuses/sample). It is tested on
Splunk 4.3.2.

A number of dashboards and searches are also included to demonstrate how Splunk
can be used to visualize Twitter activity.

## Installation

* Install the app by copying the `twitter2` directory to
  `$SPLUNK_HOME/etc/apps/twitter2`.

* (Re)start Splunk so that the app is recognized.

* In the Splunk web interface, from the App menu, select the Twitter app. And
  press "Continue to app setup page".

* Enter your Twitter credentials and click "Save". (If you don't already have a
  Twitter account, you can sign up for one at
  [https://twitter.com/](https://twitter.com/).)

* Wait 15 seconds or so for some tweets to be extracted.

* Run the search `index=twitter` in Splunk to see the events. If you don't see
  any events, open `$SPLUNK_HOME/var/log/splunk/splunkd.log` and look for errors
  issued by ExecProcessor related to the
  `$SPLUNK_HOME/etc/apps/twitter2/bin/twitter_stream.py` script.

## Dashboards and Searches

### Views > <u>Twitter General Activity</u>

Provides information about trending activity during the last 15 minutes.

### Views > <u>Twitter Per-User Activity</u>

Drills down into activity related to a particular user or hashtag.

This view could be used as a social dashboard for tracking activity related to a
user of interest.

### Searches & Reports > <u>Tweet Locations</u>

_NOTE: This view requires the [Google
Maps](http://splunk-base.splunk.com/apps/22365/google-maps) application from
SplunkBase to be installed._

Displays the locations of tweets on a map.

## License

This software is licensed under the Apache License 2.0. Details can be found in
the file LICENSE.
