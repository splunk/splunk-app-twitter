# Twitter App for Splunk

This app provides a scripted input for [Splunk](http://www.splunk.com/) that
automatically extracts tweets from [Twitter](https://twitter.com/)'s [1% sample
stream](https://dev.twitter.com/docs/api/1.1/get/statuses/sample). It is tested on
Splunk 5.0.4.

A number of dashboards and searches are also included to demonstrate how Splunk
can be used to visualize Twitter activity.

## Installation

* Install the app by copying the `twitter2` directory to
  `$SPLUNK_HOME/etc/apps/twitter2`.

* (Re)start Splunk so that the app is recognized.

* In the Splunk web interface, from the App menu, select the Twitter app
  and press "Continue to app setup page".

* Enter the OAuth settings for a Twitter application that will be used to access
  tweets from the sample stream and click "Save".

  If you don't already have a Twitter account, you can sign up for one at
  [https://twitter.com/](https://twitter.com/). If you need to create a Twitter
  application for accessing tweets, you can create one at
  [https://dev.twitter.com/apps](https://dev.twitter.com/apps). It need only be
  enabled for read access to Twitter data. See
  [https://dev.twitter.com/docs/application-permission-model](https://dev.twitter.com/docs/application-permission-model)
  for details on the Twitter application permission model

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

Displays the locations of tweets on a map.

## License

This software is licensed under the Apache License 2.0. Details can be found in
the file LICENSE.
