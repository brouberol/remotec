import os
import tweepy

from remotec.consumer import consume_stream

auth = tweepy.OAuthHandler(
    os.environ['TWITTER_CONSUMER_KEY'],
    os.environ['TWITTER_SECRET_KEY'])
auth.set_access_token(
    os.environ['TWITTER_KEY'],
    os.environ['TWITTER_SECRET'])
api = tweepy.API(auth)

if __name__ == '__main__':
    consume_stream(api)
