import asyncio
import yaml
import tweepy
import os

from utils import twitter_tools as th
from dotenv import load_dotenv
load_dotenv()

with open("utils/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)


# async def main():
#     twitterAPI = await th.init_twitter()
#     myStream, runner = await th.init_listener(twitterAPI, config["account_to_query"])
#     return print("STREAM: ", myStream, "RUNNER: ", runner)
#     # TODO: FIX SO THAT RIGHT ACCOUNTS ARE TRACKED WHEN STREAMING CLIENT RUNNING

# asyncio.run(main())


class Filter(tweepy.Stream):

    def __init__(self, consumerKey, consumerSecret, accessToken, accessTokenSecret, tweet_count, keyword):
        self.process_count = 0
        self.consumer_key = consumerKey
        self.consumer_secret = consumerSecret
        self.access_token = accessToken
        self.access_token_secret = accessTokenSecret
        self.limit = tweet_count
        self.keywords = keyword
        self.running = False
        self.user_agent = "chatGPT-Client"
        super().__init__(self.consumer_key, self.consumer_secret,
                         self.access_token, self.access_token_secret)

    def on_status(self, status):
        if self.process_count == self.limit:
            self.disconnect(1)

        if status.retweeted or 'RT @' in status.text:
            return

        if hasattr(status, "extended_tweet"):
            tweet_text = status.extended_tweet['full_text']
        else:
            tweet_text = status.text

        keyword = self.check_keyword(tweet_text)
        if not keyword:
            return

        location = status.coordinates
        if location:
            location = str(status.coordinates['coordinates'])

        self.process_count += 1

    def check_keyword(self, tweet_text):
        for word in self.keywords:
            if word in tweet_text:
                return word
        return None


def start_listener():
    myStream = tweepy.Stream(os.getenv("TWITTER_BEARER_TOKEN"), os.getenv("TWITTER_API_KEY"), os.getenv(
        "TWITTER_ACCESS_TOKEN"), os.getenv("TWITTER_ACCESS_TOKEN_SECRET"))
    return myStream


def main():
    myStream = start_listener()

    keyword = config["account_to_query"]

    # stream = Filter(os.getenv("TWITTER_API_KEY"), os.getenv("TWITTER_API_SECRET_KEY"),
    # os.getenv("TWITTER_ACCESS_TOKEN"), os.getenv("TWITTER_ACCESS_TOKEN_SECRET"), 100, keyword)
    # stream.filter(track=keyword, languages=['en'])

    myStream.filter(track=keyword, languages=['en'])


asyncio.run(main())
