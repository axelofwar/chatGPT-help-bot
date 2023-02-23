import asyncio
import discord
import os
import re
import sys
# import urllib.parse # for links in channel messages
import yaml
from collections import Counter

'''
Tools for interacting with the Discord API - contains functions for:
    - Setting up the Discord client
    - Getting the channel history of a channel
    - Getting the messages from a channel history
    - Getting the content of a message
    - Getting the questions and keywords from messages
'''

with open("utils/yamls/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)


# INITIALIZE DISCORD CLIENT
async def init_discord(cancel):
    # Create a Discord client
    if not cancel:
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

    return client


# GET CHANNEL HISTORY BY ACCOUNT FOR DAYS PASSED IN
async def get_channel_history(channel_id, history_days, cancel):

    print("DISCORD BOT ENTERED")
    # # Create a Discord client
    if not cancel:
        client = await init_discord(cancel)
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

    # UI LOGIC TO PROCESS CHANNEL ID USER INPUT
    # if channel_id == None:
    #     # use channel_id from config id
    #     channel_value = int(config["data_channel_id"])
    #     print("CHANNEL_VALUE: ", channel_value)
    #     channel = client.get_channel(channel_value)
    #     channel_id = channel_value
    #     print("CHANNEL GET SUCCESS FROM NONE: ", channel)

    # else:
    #     print("CHANNEL VALUE RECIEVED: ", channel_id)
    #     # use channel_id passed into UI
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


# GET DISCORD MESSAGES IN LOOP AND WRITE TO FILE
async def get_discord_messages(channel_history, outputFile):

    async for message in channel_history:
        # process message here
        # print("MESSAGE CHANNEL: ", message.channel)
        # print("MESSAGE: ", message.content)
        # print("MESSAGE AUTHOR: ", message.author)
        # print("MESSAGE TIMESTAMP: ", message.created_at)
        link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
        # print("LINK TO MESSAGE: ", link)
        # print("\n")
        messages = []
        messages.append(message.content)
        print("DATA: ", message.content, file=outputFile)
        print("AUTHOR: ", message.author, file=outputFile)
        print("TIMESTAMP: ", message.created_at, file=outputFile)
        print("LINK: ", link, file=outputFile)
        outputFile.write("\n")

    return messages, outputFile

messages = []
questions = []


# GET POTENTIAL QUESTIONS FROM DISCORD MESSAGES
async def get_questions(chat_history):
    async for message in chat_history:
        messages.append(message.content)
        # print("MESSAGE: ", message.content)
        question_counts = Counter()
        question_words = ["what", "when", "where", "who",
                          "why", "how", "can", "could", "would", "should"]
        for word in question_words:
            if word in message.content:
                questions.append(message.content)
            question_counts[word] += message.content.lower().count(word)
        # print("QUESTION COUNTS: ", question_counts)
        # print("QUESTIONS: ", questions)
        # top_3_questions = question_counts.most_common(3)
        # return print("Top 3 commonly asked questions: ", top_3_questions)
    return messages


# FIND KEYWORDS IN DISCORD MESSAGES
async def get_keywords(channel_history):
    async for message in channel_history:
        word_counts = Counter()
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
        words = message.content.split()
        words = [word for word in words if word not in stopwords]
        word_counts.update(words)
        top_3_keywords = word_counts.most_common(3)

        # incoporate links when channel that has them is included
        # if re.match(f"^{question_words}", message.content, re.IGNORECASE):
        #     question_counts.update([message.content])
        # if re.search(r'\?$', message.content):
        #     question_counts.update([message.content])

        # print("Top 3 keywords: ", top_3_keywords)
        # print("\n")

        return top_3_keywords
