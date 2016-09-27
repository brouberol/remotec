"""
Definition of a Twitter streaming consumer, receiving all tweets on the OVH Summit
hashtag, and sending them to workers, for further analysis and potential actions.
"""

import os
import sys
import tweepy
import logging
import re
import time

from .tasks import start_app, stop_app, scale_app, delete_app, restart_app

logging.basicConfig()
LOG = logging.getLogger('remotec.consumer')
LOG.setLevel('INFO')

# Regular expressions for tweet parsing
SCALE = r'(?P<action>scale)'
STOP = r'(?P<action>stop)'
START = r'(?P<action>start)'
RESTART = r'(?P<action>restart)'
DELETE = r'(?P<action>delete)'
APP = r'(?P<app>[-/\w]+)'
INSTANCES = r'(?P<instances>\d+)'
ACTION_PATTERNS = (
    r'{action}\s+{app}\s+{instances}'.format(action=SCALE, app=APP, instances=INSTANCES),
    r'{action}\s+{app}(\s+{instances})?'.format(action=START, app=APP, instances=INSTANCES),
    r'{action}\s+{app}'.format(action=RESTART, app=APP),
    r'{action}\s+{app}'.format(action=STOP, app=APP),
    r'{action}\s+{app}'.format(action=DELETE, app=APP),
)
ACTIONS = {
    'start': start_app,
    'scale': scale_app,
    'delete': delete_app,
    'restart': restart_app,
    'stop': stop_app,
}


def parse_dockeraas_tweet(text):
    """Return a normalized dict containing the tweet action, if any."""
    for pattern in ACTION_PATTERNS:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            command = m.groupdict()
            command['action'] = command['action'].lower()
            if command.get('instances'):
                command['instances'] = int(command['instances'])
            elif command['action'] == 'start':
                command['instances'] = 1
            else:
                command['instances'] = None
            LOG.info('%r parsed into %r' % (text, command))
            return command


class SummitStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        LOG.info("Received tweet: %r", status.text)
        username = status.user.screen_name
        command = parse_dockeraas_tweet(status.text)
        if command:
            LOG.info('{action} app for user {username}{instances}'.format(
                action=command['action'],
                username=username,
                instances=' to %d instances' % (command['instances']) if command.get('instances') else ''))
            ACTIONS[command['action']].delay(username=username, instances=command['instances'])


def consume_stream(api):
    stream_listener = SummitStreamListener()
    streamer = tweepy.Stream(auth=api.auth, listener=stream_listener)
    connection_attempts = 0
    while True:
        LOG.info("Streaming tweets from hashtag %r" % (os.environ['STREAM_HASHTAG']))
        try:
            streamer.filter(track=[os.environ['STREAM_HASHTAG']])
        except KeyboardInterrupt:
            LOG.info('Disconnecting from Twitter API')
            streamer.disconnect()
            sys.exit(1)
        except Exception as exc:
            LOG.exception(exc)
            connection_attempts += 1
            time.sleep(connection_attempts * 5)
