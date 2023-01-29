import discord
import os
from collections import Counter
import sys


async def printDiscordHistory(channel_history, outputFile):
    word_counts = Counter()
    # question_counts = Counter()
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

    async for message in channel_history:

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


async def init_discord(cancel):
    print("DISCORD BOT ENTERED")

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
