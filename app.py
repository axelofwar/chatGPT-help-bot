import os
import openai
import asyncio
import ui
import sys
import yaml
import discord
import tweepy
import urllib.parse
import re
from collections import Counter
from dotenv import load_dotenv

load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")  # if using python .env file
# if using replit Secrets function
openai.api_key = os.environ['OPENAI_API_KEY']
if not openai.api_key:
    openai.api_key = ""
    print("OPENAI API KEY NOT FOUND")

with open("config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

openai.api_endpoint = config["OPENAI_ENDPOINT"]

# get config params
prompt = config["prompt"]
model = config["davinci"]
temp = config["temp"]
max_tokens = config["max_tokens"]


async def chatGPTcall(mPrompt, mModel, mTemp, mTokens):  # function for ChatGPT call
    response = openai.Completion.create(
        model=mModel,
        prompt=mPrompt,
        # uniqueness modifiers
        temperature=mTemp,
        max_tokens=mTokens,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"])
    return response


async def initTwitter():  # function for initializing Twitter API
    auth = tweepy.OAuthHandler(
        os.getenv("TWITTER_API_KEY"), os.getenv("TWITTER_API_SECRET_KEY"))
    auth.set_access_token(os.getenv("TWITTER_ACCESS_TOKEN"),
                          os.getenv("TWITTER_ACCESS_TOKEN_SECRET"))
    api = tweepy.API(auth)
    print("TWITTER API INITIALIZED")
    return api


async def get_channel_history():  # function for intializing Discord client and getting desired channel history
    task = asyncio.create_task(ui.main())
    try:
        channel_id, history_days, cancel = await task
        print("UI SUCCESS: APP.PY USED UI VALUES")
        print("UI CHANNEL_ID: ", channel_id)
        print("CANCEL: ", cancel)
    except:
        print("UI FAILED/EMPTY: APP.PY USED DEFAULTS")
        channel_id = config["discord_channel_id"]
        print("EXCEPT CHANNEL_ID: ", channel_id)
        print("EXCEPT CANCEL: ", cancel)
        history_days = 30

    print("DISCORD BOT ENTERED")

    # Create a Discord client
    if not cancel:
        discord_token = os.getenv("DISCORD_TOKEN")  # if using python .env file
        intents = discord.Intents.default()
        intents.message_content = True
        client = discord.Client(intents=intents)
    else:
        print("CANCELLED")
        return

    if client.is_closed():
        print('Closed client: ', client.status)
        sys.exit()
    else:
        print('Opened client:', client.status)

    @client.event
    async def on_ready():
        # ensure the bot is ready and not stuck in a current activity
        print("The bot is ready!")
        print(f'{client.user} has connected to Discord!')
        print(f'{client.user} status: {client.status}')
        print(f'{client.user} is connected to the following guild:')
        print(f'{client.user} current activity: {client.activity}')

    @client.event
    async def on_disconnect():
        print(f'{client.user} has disconnected from Discord!')

    try:
        # start discord client
        # TODO: improve logic so that client closes on complete instead of timeout required
        if not cancel:
            task = asyncio.create_task(client.start(discord_token))
            await asyncio.wait_for(task, config["timeout"])
        else:
            print("TASK CANCELLED")
            sys.exit()

        # TODO: modify to display this info properly
        print("Client User: ", client.user)
        print(f'{client.user} status: {client.status}')
        print(f'{client.user} is connected to the following guild:')
        print(f'{client.user} current activity: {client.activity}')
        print("CLIENT STARTED SUCCESSFULLY", client.status)
    except asyncio.TimeoutError:
        print("CLIENT TIMEOUT")
    except discord.errors.LoginFailure as exc:
        print(f'Error: {exc}')
    except discord.errors.ClientException as exc1:
        print(f'Error: {exc1}')
    except discord.errors.HTTPException as exc2:
        print(f'Error: {exc2}')
    except discord.errors.DiscordException as exc4:
        print(f'Error: {exc4}')

    # TODO: add more channels to this list
    print("DISCORD BOT STARTED")
    if channel_id == None:
        # use channel_id from config id
        channel_value = int(config["discord_channel_id"])
        print("CHANNEL_VALUE: ", channel_value)
        channel = client.get_channel(channel_value)
        channel_id = channel_value
        print("CHANNEL GET SUCCESS FROM NONE: ", channel)

    else:
        print("CHANNEL VALUE RECIEVED: ", channel_id)
        # use channel_id passed into UI
        try:
            channel = client.get_channel(int(channel_id))
            print("CHANNEL GET SUCCESS: ", channel)

        except:
            print("CHANNEL GET FAILED")
            sys.exit()

    print("CHANNEL HISTORY: ", history_days)
    print("CHANNEL_ID POST: ", channel_id)
    print("CHANNEL POST: ", channel)

    # question_words = ["what", "when", "where", "who",
    #                   "why", "how", "can", "could", "would", "should"]
    word_counts = Counter()
    # question_counts = Counter()
    channel_history = channel.history(limit=history_days, oldest_first=True)

    # done with connection to discord
    # task.cancel()
    # TODO: fix cancel on complete so I don't need to wait whole 15 seconds
    return channel, channel_history


async def printDiscordHistory(channel_history, outputFile):
    word_counts = Counter()
    # question_counts = Counter()

    async for message in channel_history:

        # question_words = ["what", "when", "where", "who",
        #                   "why", "how", "can", "could", "would", "should"]

        stopwords = ["the", "and", "I", "to", "in", "a", "of", "is", "it",
                     "you", "that", "he", "was", "for", "on", "are", "as",
                     "with", "his", "they", "I'm", "at", "be", "this", "have",
                     "from", "or", "one", "had", "by", "word", "but", "not", "what",
                     "all", "were", "we", "when", "your", "can", "said", "there", "use",
                     "an", "each", "which", "she", "do", "how", "their", "if", "will",
                     "up", "other", "about", "out", "many", "then", "them", "these", "so",
                     "some", "her", "would", "make", "like", "him", "into", "time", "has",
                     "look", "two", "more", "write", "go", "see", "number", "no", "way",
                     "could", "people", "my", "than", "first", "water", "been", "call",
                     "who", "oil", "its", "now", "find", "long", "down", "day", "did",
                     "get", "come", "made", "may", "part", "<#943011412219920415>"]

        # process message here
        print("MESSAGE CHANNEL: ", message.channel)
        print("MESSAGE: ", message.content)
        print("MESSAGE AUTHOR: ", message.author)
        print("MESSAGE TIMESTAMP: ", message.created_at)
        link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
        print("LINK TO MESSAGE: ", link)
        print("\n")
        words = message.content.split()
        words = [word for word in words if word not in stopwords]
        word_counts.update(words)

        # incoporate links when channel that has them is included
        # if re.match(f"^{question_words}", message.content, re.IGNORECASE):
        #     question_counts.update([message.content])
        # if re.search(r'\?$', message.content):
        #     question_counts.update([message.content])

        top_3_keywords = word_counts.most_common(3)
        print("Top 3 keywords: ", top_3_keywords)
        print("\n")

        # top_3_questions = question_counts.most_common(3)
        # print("Top 3 commonly asked questions: ", top_3_questions)
        # print("\n")
        print("DATA: ", message.content, file=outputFile)
        print("AUTHOR: ", message.author, file=outputFile)
        print("TIMESTAMP: ", message.created_at, file=outputFile)
        print("LINK: ", link, file=outputFile)
        outputFile.write("\n")

    return outputFile


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


async def update_output_file(response):
    # TODO: modify to use r+ for read/write and make one open call
    with open("output.txt", "r") as outputFile:
        lines = outputFile.readlines()
        outputFile.close()

    with open("output.txt", "w") as outputFile:
        found_response = False
        for line in lines:
            if "RESPONSE:" in line:
                if not found_response:
                    outputFile.write(
                        "RESPONSE:" + response.choices[0].text + "\n")
                    found_response = True
            else:
                outputFile.write(line)
        if not found_response:
            outputFile.write("RESPONSE: " + response.choices[0].text + "\n")
    outputFile.close()
    return "OUTPUT FILE UPDATED"


async def main():
    # init twitter API
    twitterAPI = await initTwitter()

    # get all mentions of [account_to_query] in [tweet_history] days
    tweets = twitterAPI.search_tweets(
        q=config["account_to_query"], count=config["tweet_history"])

    # open file to write to
    with open("tweets.txt", "w") as tweetFile:
        search_results = await printTweetHistory(tweets, tweetFile)
    # returns tweets as a list of Tweet objects

    # get channel & history from UI or defaults - modify to pass params?
    channel, channel_history = await get_channel_history()
    # returns channel object and list of message objects

    # TODO: clean file read/write logic so updates can be written and read from same opened instance
    with open("discord.txt", "w") as outputFile:
        # print chanel history to file
        discord_history = await printDiscordHistory(channel_history, outputFile)
        # returns list of message objects
    with open("discord.txt", "r") as outputFile:
        discord_history = outputFile.read()
        # returns string of discord history
    mprompt = prompt + \
        f"Use primarily the data in this fileto answer:\n{discord_history}\n"

    GPTresponse = await chatGPTcall(mprompt, model, temp, max_tokens)
    print("RESPONSE: ", GPTresponse.choices[0].text)

    updateOutput = await update_output_file(GPTresponse)
    # prints response to terminal + output file

    # TODO: do stuff with search_results from twitter + channel & channel_history from discord

    print("\n", updateOutput)
    return "SUCCESS"

asyncio.run(main())
