import tweepy
import os


async def initTwitter():  # function for initializing Twitter API
    auth = tweepy.OAuthHandler(
        os.getenv("TWITTER_API_KEY"), os.getenv("TWITTER_API_SECRET_KEY"))
    auth.set_access_token(os.getenv("TWITTER_ACCESS_TOKEN"),
                          os.getenv("TWITTER_ACCESS_TOKEN_SECRET"))
    api = tweepy.API(auth)
    print("TWITTER API INITIALIZED")
    return api


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