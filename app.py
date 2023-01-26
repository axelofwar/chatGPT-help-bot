import os
import openai
import asyncio
import ui
import yaml
import discord
from dotenv import load_dotenv

load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")  # if using python .env file
# openai.api_key = os.environ.get("OPENAI_API_KEY")  # if using python .env m2
# if using replit Secrets function
openai.api_key = os.environ['OPENAI_API_KEY']
if not openai.api_key:
    openai.api_key = ""

with open("config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

openai.api_endpoint = config["OPENAI_ENDPOINT"]

# function for ChatGPT call


async def chatGPTcall(mPrompt, mModel, mTemp, mTokens):
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


async def main():
    print("TRY TO OPEN UI.MAIN() IN APP.PY")
    print("CHANNEL PRE UI: ", config["discord_channel_id"])
    try:
        channel_id, history_days = await asyncio.create_task(ui.main())
        print("TRY CHANNEL_ID: ", channel_id)
    except:
        channel_id = config["discord_channel_id"]
        history_days = 30

    print("ENTERING MAIN + CONFIG READ")

    prompt = config["prompt"]
    model = config["davinci"]

    print("CHANNEL_ID PRE: ", channel_id)
    print("DISCORD BOT ENTERED")

    # Create a Discord client
    discord_token = os.getenv("DISCORD_TOKEN")  # if using python .env file

    client = discord.Client(
        intents=discord.Intents.default())

    # print("DISCORD_TOKEN: ", discord_token) # to confirm operational

    try:
        await client.start(discord_token)
    except Exception as exc:
        print(exc)
        raise discord.errors.LoginFailure(
            'Improper token has been passed.') from exc

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
        channel = client.get_channel(int(channel_id))

    print("History: ", history_days)
    print("CHANNEL_ID POST: ", channel_id)
    print("CHANNEL POST: ", channel)

    messages = await channel.history(limit=history_days, oldest_first=True).flatten()

    print("MESSAGES: ", messages)

    filename = 'output.txt'

    if os.path.exists(filename):
        outputFile = open(filename, mode='r+')
    else:
        outputFile = open(filename, 'x')

    for message in messages:
        outputFile.write(message.content)

    outputFile.close()


asyncio.get_event_loop().run_until_complete(main())
