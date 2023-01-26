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
    print("TRY UI.MAIN() IN APP.PY")
    try:
        channel_id, history_days = await asyncio.create_task(ui.main())
        print("UI CHANNEL_ID: ", channel_id)
    except:
        channel_id = config["discord_channel_id"]
        print("EXCEPT CHANNEL_ID: ", channel_id)
        history_days = 30

    prompt = config["prompt"]
    model = config["davinci"]

    print("DISCORD BOT ENTERED")

    # Create a Discord client
    discord_token = os.getenv("DISCORD_TOKEN")  # if using python .env file
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    if client.is_closed():
        print("Client is closed")
    else:
        print("Client is open")

    @client.event
    async def on_ready():
        print("The bot is ready!")

    @client.event
    async def on_disconnect():
        print("The bot is disconnected!")

    try:
        # print("DISCORD TOKEN: ", discord_token)
        await asyncio.wait_for(client.start(discord_token), timeout=10)
        print("Client User: ", client.user)
        print("CLIENT STARTED SUCCESSFULLY", client.status)
    except asyncio.TimeoutError:
        print("CLIENT TIMEOUT ERROR")
    except discord.errors.LoginFailure as exc:
        print(f'Error: {exc}')
    except discord.errors.ClientException as exc1:
        print(f'Error: {exc1}')
    except discord.errors.HTTPException as exc2:
        print(f'Error: {exc2}')
    except discord.errors.DiscordException as exc4:
        print(f'Error: {exc4}')

    # print("DISCORD_TOKEN: ", discord_token) # to confirm operational

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
        except:
            print("CHANNEL GET FAILED")

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


# asyncio.get_event_loop().run_until_complete(main())
asyncio.run(main())
