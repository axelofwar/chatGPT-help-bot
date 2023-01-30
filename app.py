import asyncio
import sys
import yaml
from utils import mod as tools
from dotenv import load_dotenv


load_dotenv()

with open("utils/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

# get config params
# TODO: replace with external get prompt: discord vs. twitter
# TODO: on tweet @ mention would require a trigger to call asyncio.run(main())
# TODO: on discord chat would require a webhook to call asyncio.run(main())

prompt = config["prompt"]
model = config["davinci"]
temp = config["temp"]
max_tokens = config["max_tokens"]


async def main():
    # init twitter API
    twitterAPI = await tools.th.init_twitter()

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
    #     print("EXCEPT CANCEL: ", cancel)
    #     history_days = 30

    data_channel_id = config["data_channel_id"]
    history_days = 30
    cancel = False
    # get channel & history from UI or defaults - modify to pass params?
    if not cancel:
        data_channel, data_channel_history = await tools.dh.get_channel_history(data_channel_id, history_days, cancel)
        chat_channel, chat_channel_history = await tools.dh.get_channel_history(config["chat_channel_id"], 5, cancel)

    # while th.running:
        tweets = await tools.th.call_once(
            twitterAPI, config["account_to_query"], cancel)

        # open file to write to
        with open("outputs/tweets.txt", "w") as tweetFile:
            search_results = await tools.th.print_tweet_history(tweets, tweetFile)

        # myStream, runner = await th.init_listener(twitterAPI, config["account_to_query"], cancel)

        # TODO: clean file read/write logic so updates can be written and read from same opened instance
        with open("outputs/discord.txt", "w") as outputFile:
            # print chanel history to file for DATA channel
            data_messages, discord_history = await tools.dh.get_discord_messages(data_channel_history, outputFile)
            # returns list of message objects

        with open("outputs/discord.txt", "r") as outputFile:
            discord_history = outputFile.read()
            # returns string of discord history

        question_chat = await tools.dh.get_questions(chat_channel_history)
        # print("QUESTION_CHAT: ", question_chat[0])

        prompt_tag = f" Use primarily the data in this file to answer it:\n{discord_history}\n"
        mprompt = prompt + prompt_tag

        GPTresponse = await tools.gpt.chatGPTcall(mprompt, model, temp, max_tokens)
        print("RESPONSE: ", GPTresponse.choices[0].text)

        running = updateOutput = await tools.uout.update_output_file(GPTresponse)
        # prints response to terminal + output file

        # TODO: do stuff with search_results from twitter + channel & channel_history from discord

        # print("\n", "RUNNING: ", running)
        # return "SUCCESS"

    if cancel or not tools.th.running:
        print("\nRUNNING = FALSE -> PROGRAM ENDED")
        # await th.close_listener(myStream)
        sys.exit()
    return running

asyncio.run(main())
