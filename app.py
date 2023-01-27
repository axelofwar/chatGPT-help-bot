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
    api = tweepy.API(auth)
    print("TWITTER API INITIALIZED")
    return api


async def get_channel_history():
    print("TRY UI.MAIN() IN APP.PY")
    task = asyncio.create_task(ui.main())
    try:
        channel_id, history_days, cancel = await task
        print("UI CHANNEL_ID: ", channel_id)
        print("CANCEL: ", cancel)
    except:
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
        print("The bot is ready!")
        print(f'{client.user} has connected to Discord!')
        print(f'{client.user} status: {client.status}')
        print(f'{client.user} is connected to the following guild:')
        print(f'{client.user} current activity: {client.activity}')

    @client.event
    async def on_disconnect():
        print(f'{client.user} has disconnected from Discord!')

    try:
        if not cancel:
            task = asyncio.create_task(client.start(discord_token))
            await asyncio.wait_for(task, config["timeout"])
        else:
            print("TASK CANCELLED")
            sys.exit()

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

    filename = 'output.txt'

    if os.path.exists(filename):
        outputFile = open(filename, mode='r+')
    else:
        outputFile = open(filename, 'x')

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
    # question_words = ["what", "when", "where", "who",
    #                   "why", "how", "can", "could", "would", "should"]
    word_counts = Counter()
    # question_counts = Counter()
    async for message in channel.history(limit=history_days, oldest_first=True):
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

        # done with connection to discord
        # task.cancel()
        # TODO: fix cancel on complete so I don't need to wait whole 15 seconds

    prompt = config["prompt"]
    model = config["davinci"]
    temp = config["temp"]
    max_tokens = config["max_tokens"]

    # TODO: clean file read/write logic
    with open("output.txt", "r") as outputFile:
        data = outputFile.read()

    mprompt = prompt + \
        f"Use primarily the data in this fileto answer:\n{data}\n"

    GPTresponse = await chatGPTcall(mprompt, model, temp, max_tokens)
    print("RESPONSE: ", GPTresponse.choices[0].text)
    # outputFile.close()

    with open("output.txt", "r") as outputFile:
        lines = outputFile.readlines()
        outputFile.close()

    with open("output.txt", "w") as outputFile:
        for line in lines:
            if "RESPONSE:" not in line:
                outputFile.write(line)
        outputFile.write("RESPONSE: " + GPTresponse.choices[0].text + "\n")
    outputFile.close()

    return "SUCCESS"


async def main():
    twitterAPI = await initTwitter()
    channel_history = await get_channel_history()
    return "SUCCESS"

asyncio.run(main())
