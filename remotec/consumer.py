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

from remotec.tasks import start_app, stop_app, scale_app, delete_app, restart_app

logging.basicConfig()
LOG = logging.getLogger('remotec.consumer')
LOG.setLevel('INFO')

# Regular expressions for tweet parsing
SCALE = r'(?P<action>scale)'
STOP = r'(?P<action>stop)'
START = r'(?P<action>start)'
RESTART = r'(?P<action>restart)'
DELETE = r'(?P<action>delete)'
INSTANCES = r'(?P<instances>\d+)'
ACTION_PATTERNS = (
    r'{action}\s+{instances}'.format(action=SCALE, instances=INSTANCES),
    r'{action}\s+({instances})?'.format(action=START, instances=INSTANCES),
    r'{action}'.format(action=RESTART),
    r'{action}'.format(action=STOP),
    r'{action}'.format(action=DELETE),
)
ACTIONS = {
    'start': start_app,
    'scale': scale_app,
    'delete': delete_app,
    'restart': restart_app,
    'stop': stop_app,
}
STREAM_HASHTAG = os.environ['STREAM_HASHTAG']
MAX_INSTANCES = 10


def parse_dockeraas_tweet(text):
    """Return a normalized dict containing the tweet action, if any."""
    for pattern in ACTION_PATTERNS:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            command = m.groupdict()
            command['action'] = command['action'].lower()
            if command.get('instances'):
                command['instances'] = int(command['instances'])
                if command['instances'] > MAX_INSTANCES:
                    command['instances'] = MAX_INSTANCES
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
        LOG.info("Streaming tweets from hashtag %r" % STREAM_HASHTAG)
        try:
            streamer.filter(track=[STREAM_HASHTAG])
        except KeyboardInterrupt:
            LOG.info('Disconnecting from Twitter API')
            streamer.disconnect()
            sys.exit(1)
        except Exception as exc:
            LOG.exception(exc)
            connection_attempts += 1
            time.sleep(connection_attempts * 5)
