import os
import tweepy
import yaml

with open("utils/yamls/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

running = True


# INITIALIZE TWITTER API
async def init_twitter():
    auth = tweepy.OAuthHandler(
        os.getenv("TWITTER_API_KEY"), os.getenv("TWITTER_API_SECRET_KEY"))
    auth.set_access_token(os.getenv("TWITTER_ACCESS_TOKEN"),
                          os.getenv("TWITTER_ACCESS_TOKEN_SECRET"))
    api = tweepy.API(auth)
    print("TWITTER API INITIALIZED")
    return api


# GET TWEET HISTORY BY ACCOUNT FOR DAYS SPECIFIED IN CONFIG
async def call_once(api, account, cancel):
    if not cancel:
        tweets = api.search_tweets(
            q=account, count=config["tweet_history"])
        print("TWEET HISTORY CALLED ONCE \n")
        return tweets
    else:
        print("CANCELLED")
        return cancel


# PRINT TWEET HISTORY TO FILE
async def print_tweet_history(tweets, tweetFile):
    count = 1
    for tweet in tweets:
        # print("TWEET ", count, ": ", tweet.text)
        tweetFile.write("TWEET " + str(count) + ": " + tweet.text + "\n")
        # print("TWEET AUTHOR ", count, ": ", tweet.user.screen_name)
        tweetFile.write("TWEET AUTHOR " + str(count) +
                        ": " + tweet.user.screen_name + "\n")
        # print("TWEET TIMESTAMP ", count, ": ", tweet.created_at)
        tweetFile.write("TWEET TIMESTAMP " + str(count) +
                        ": " + str(tweet.created_at) + "\n")
        # print("TWEET LINK ", count, ": ",
        #   f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
        tweetFile.write("TWEET LINK " + str(count) + ": " + "https://twitter.com/" +
                        tweet.user.screen_name + "/status/" + str(tweet.id) + "\n")
        tweetFile.write("\n")
        count += 1
    return tweets
