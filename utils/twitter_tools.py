import tweepy
import os
import yaml
import asyncio
from twitter_stream import FilteredStream

with open("utils/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

running = True
# myStream = tweepy.Stream(os.getenv("TWITTER_BEARER_TOKEN"), os.getenv("TWITTER_API_KEY"), os.getenv(
#     "TWITTER_ACCESS_TOKEN"), os.getenv("TWITTER_ACCESS_TOKEN_SECRET"))

myStream = tweepy.StreamingClient(
    os.getenv("TWITTER_BEARER_TOKEN"))


async def initTwitter():  # function for initializing Twitter API
    auth = tweepy.OAuthHandler(
        os.getenv("TWITTER_API_KEY"), os.getenv("TWITTER_API_SECRET_KEY"))
    auth.set_access_token(os.getenv("TWITTER_ACCESS_TOKEN"),
                          os.getenv("TWITTER_ACCESS_TOKEN_SECRET"))
    api = tweepy.API(auth)
    print("TWITTER API INITIALIZED")
    return api


async def call_once(api, account, cancel):
    if not cancel:
        tweets = api.search_tweets(
            q=account, count=config["tweet_history"])
        print("TWEET HISTORY CALLED ONCE")
        return tweets
    else:
        print("CANCELLED")
        return cancel


async def init_listener(api, account, cancel):
    # mentions of [account_to_query]
    # myStream.filter(track=["@"+account], callback=on_tweet)
    # api.filter(track=["@"+account], callback=on_tweet)
    # myStream.filter(track=["@"+account])
    myStream.on_data = on_tweet
    print("STREAMING TWEETS", myStream)
    await asyncio.sleep(5)
    running = False
    print("STREAMING CANCELLED")
    return running


async def on_tweet(tweet):
    print("TWEET RECEIVED")
    print(tweet.text)
    print(tweet.user.screen_name)
    print(tweet.created_at)
    print(f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
    return tweet


async def closeListener():
    myStream.disconnect()
    print("STREAMING DISCONNECTED")
    running = False


async def printTweetHistory(tweets, tweetFile):
    count = 1
    for tweet in tweets:
        print("TWEET ", count, ": ", tweet.text)
        tweetFile.write("TWEET " + str(count) + ": " + tweet.text + "\n")
        print("TWEET AUTHOR ", count, ": ", tweet.user.screen_name)
        tweetFile.write("TWEET AUTHOR " + str(count) +
                        ": " + tweet.user.screen_name + "\n")
        print("TWEET TIMESTAMP ", count, ": ", tweet.created_at)
        tweetFile.write("TWEET TIMESTAMP " + str(count) +
                        ": " + str(tweet.created_at) + "\n")
        print("TWEET LINK ", count, ": ",
              f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
        tweetFile.write("TWEET LINK " + str(count) + ": " + "https://twitter.com/" +
                        tweet.user.screen_name + "/status/" + str(tweet.id) + "\n")
        tweetFile.write("\n")
        count += 1
    return tweets
