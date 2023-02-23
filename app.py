import asyncio
import sys
import yaml
# from utils import mod as tools
# from utils import postgres_tools as pg
# from utils import stream_tools as st
from utils import twitter_tools as th
from utils import discord_tools as dh
from utils import chat_gpt_tools as gpt
from dotenv import load_dotenv

load_dotenv()

'''
This is the main file for the bot - contains functions for:
    - One time twitter call search_tweets()
    - discord channel history search on discords bot is added to (TNT-HQ atm)
    - UI for user to input channel ID and history days - currently commented out
    - GPT-3 call to generate response
'''

with open("utils/yamls/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

with open("utils/yamls/params.yml", "r") as paramFile:
    params = yaml.load(paramFile, Loader=yaml.FullLoader)

# get config params
# TODO: replace with external get prompt: discord vs. twitter
# TODO: on tweet @ mention would require a trigger to call asyncio.run(main())
# TODO: on discord chat would require a webhook to call asyncio.run(main())


# Hardset params for main init
prompt = params["prompt"]
model = params["davinci"]
temp = params["temp"]
max_tokens = params["max_tokens"]

data_channel_id = config["data_channel_id"]
history_days = 30
cancel = False


# PRINT GPT RESPONSE TO FILE
async def update_output_file(response):
    # TODO: modify to use r+ for read/write and make one open call
    with open("outputs/output.txt", "r") as outputFile:
        lines = outputFile.readlines()
        outputFile.close()

    with open("outputs/output.txt", "w") as outputFile:
        found_response = False
        for line in lines:
            if "RESPONSE: " in line:
                if not found_response:
                    outputFile.write(
                        "RESPONSE: " + response.choices[0].text + "\n")
                    found_response = True
            else:
                outputFile.write(line)
        if not found_response:
            outputFile.write(
                "RESPONSE: " + response.choices[0].text + "\n")
    outputFile.close()
    th.running = False
    return th.running


async def main():
    # init twitter API
    twitterAPI = await th.init_twitter()

    # UNCOMMENT FOR UI INTERACTION
    # try:
    #     task = asyncio.create_task(tools.ui.main())
    #     data_channel_id, history_days, cancel = await task
    #     print("UI SUCCESS: APP.PY USED UI VALUES")
    #     print("UI CHANNEL_ID: ", data_channel_id)
    #     print("CANCEL: ", cancel)

    #     # myStream, runner = await th.init_listener(twitterAPI, config["account_to_query"], cancel)

    #     # open file to write to
    #     with open("outputs/tweets.txt", "w") as tweetFile:
    #         search_results = await tools.th.print_tweet_history(tweets, tweetFile)
    #     # print("RUNNER: ", runner)
    # except:
    #     print("UI FAILED/EMPTY: APP.PY USED DEFAULTS")
    #     data_channel_id = config["data_channel_id"]
    #     print("EXCEPT CHANNEL_ID: ", data_channel_id)
    #     print("EXCEPT CANCEL VALUE: ", cancel)
    #     history_days = 30

    # get channel & history from UI or defaults - modify to pass params?
    if not cancel:
        data_channel, data_channel_history = await dh.get_channel_history(data_channel_id, history_days, cancel)
        chat_channel, chat_channel_history = await dh.get_channel_history(config["chat_channel_id"], 5, cancel)

    # while th.running:
        tweets = await th.call_once(
            twitterAPI, config["account_to_query"], cancel)

        # open file to write to
        with open("outputs/tweets.txt", "w") as tweetFile:
            search_results = await th.print_tweet_history(tweets, tweetFile)

        # myStream, runner = await th.init_listener(twitterAPI, config["account_to_query"], cancel)

        # TODO: clean file read/write logic so updates can be written and read from same opened instance
        with open("outputs/discord.txt", "w") as outputFile:
            # print chanel history to file for DATA channel
            data_messages, discord_history = await dh.get_discord_messages(data_channel_history, outputFile)
            # returns list of message objects

        with open("outputs/discord.txt", "r") as discFile:
            discord_history = discFile.read()
            # returns string of discord history
        with open("outputs/tweets.txt", "r") as tweetFile:
            tweet_history = tweetFile.read()
            # returns string of tweet history

        question_chat = await dh.get_questions(chat_channel_history)
        # print("QUESTION_CHAT: ", question_chat[0])

        prompt_tag = f" Use primarily the data in these files to answer it: File#1: \n{discord_history}\n File#2: \n{tweet_history}\n"
        mprompt = prompt + prompt_tag

        GPTresponse = await gpt.chatGPTcall(mprompt, model, temp, max_tokens)
        print("RESPONSE: ", GPTresponse.choices[0].text)

        running = updateOutput = await update_output_file(GPTresponse)
        # prints response to terminal + output file

        # TODO: do stuff with search_results from twitter + channel & channel_history from discord

        # print("\n", "RUNNING: ", running)
        # return "SUCCESS"

    if cancel or not th.running:
        print("\nRUNNING = FALSE -> PROGRAM ENDED")
        # await th.close_listener(myStream)
        sys.exit()
    return running

asyncio.run(main())
