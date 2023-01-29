import os
import openai
import asyncio
import sys
import yaml
import discord
import tweepy
import urllib.parse
import re
# from collections import Counter
from dotenv import load_dotenv

from utils import ui
from utils import twitter_tools as th
from utils import discord_tools as dh
from utils import update_output_txt as uout

load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")  # if using python .env file
# if using replit Secrets function
openai.api_key = os.environ['OPENAI_API_KEY']
if not openai.api_key:
    openai.api_key = ""
    print("OPENAI API KEY NOT FOUND")

with open("utils/config.yml", "r") as file:
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


# function for intializing Discord client and getting desired channel history
async def get_channel_history(channel_id, history_days, cancel):

    print("DISCORD BOT ENTERED")
    # # Create a Discord client
    if not cancel:
        client = await dh.init_discord(cancel)
        discord_token = os.getenv("DISCORD_TOKEN")  # if using python .env file

    else:
        print("CANCELLED")
        return cancel

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

    channel_history = channel.history(limit=history_days, oldest_first=True)

    # done with connection to discord
    # task.cancel()
    # TODO: fix cancel on complete so I don't need to wait whole 15 seconds
    return channel, channel_history


async def main():
    # init twitter API
    twitterAPI = await th.initTwitter()

    # get all mentions of [account_to_query] in [tweet_history] days
    tweets = twitterAPI.search_tweets(
        q=config["account_to_query"], count=config["tweet_history"])

    # open file to write to
    with open("outputs/tweets.txt", "w") as tweetFile:
        search_results = await th.printTweetHistory(tweets, tweetFile)
    # returns tweets as a list of Tweet objects

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

    # get channel & history from UI or defaults - modify to pass params?
    if not cancel:
        channel, channel_history = await get_channel_history(channel_id, history_days, cancel)
    # returns channel object and list of message objects
    else:
        print("CANCELLED")
        sys.exit()

    # TODO: clean file read/write logic so updates can be written and read from same opened instance
    with open("outputs/discord.txt", "w") as outputFile:
        # print chanel history to file
        discord_history = await dh.printDiscordHistory(channel_history, outputFile)
        # returns list of message objects
    with open("outputs/discord.txt", "r") as outputFile:
        discord_history = outputFile.read()
        # returns string of discord history
    mprompt = prompt + \
        f"Use primarily the data in this file to answer:\n{discord_history}\n"

    GPTresponse = await chatGPTcall(mprompt, model, temp, max_tokens)
    print("RESPONSE: ", GPTresponse.choices[0].text)

    updateOutput = await uout.update_output_file(GPTresponse)
    # prints response to terminal + output file

    # TODO: do stuff with search_results from twitter + channel & channel_history from discord

    print("\n", updateOutput)
    return "SUCCESS"

asyncio.run(main())
