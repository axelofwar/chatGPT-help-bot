import asyncio
from tweepy import StreamingClient

myStream = tweepy.Stream(os.getenv("TWITTER_BEARER_TOKEN"), os.getenv("TWITTER_API_KEY"), os.getenv(
    "TWITTER_ACCESS_TOKEN"), os.getenv("TWITTER_ACCESS_TOKEN_SECRET"))


async def init_listener(api, account):
    myStream = tweepy.StreamingClient(
        os.getenv("TWITTER_BEARER_TOKEN"))
    print("STREAMING CLIENT INITIALIZED")
    # mentions of [account_to_query]
    print("STREAM ENTERED", myStream)
    track_rule = tweepy.StreamRule([{"value": "@"+account, "tag": "account"},
                                    {"value": "@y00tsNFT", "tag": "y00tsNFT"}])
    myStream.add_rules([track_rule])
    # myStream.add_rules(["@"+account])
    print("TRACK RULE: ", track_rule.value)
    print("STREAMING RULES ADDED")
    myStream.filter()
    print("STREAMING FILTERED TWEETS")
    # myStream.filter(follow=["@"+account])
    myStream.on_request_error = on_error
    myStream.on_connection_error = on_error
    myStream.on_data = on_tweet
    await asyncio.sleep(5)
    running = False
    print("STREAMING CANCELLED")
    return myStream, running


async def on_tweet(tweet):
    print("TWEET RECEIVED")
    print(tweet.text)
    print(tweet.user.screen_name)
    print(tweet.created_at)
    print(f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
    return tweet


async def on_error(error):
    print("ERROR RECEIVED")
    print(error)
    return error


async def close_listener(myStream):
    myStream.disconnect()
    print("STREAMING DISCONNECTED")
    running = False
