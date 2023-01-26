import os
import openai
import asyncio
import ui
import yaml
import discord
from dotenv import load_dotenv

load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")  # if using python .env file
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
        print('Closed client: ', client.status)
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
        task = asyncio.create_task(client.start(discord_token))
        await asyncio.wait_for(task, timeout=30)
        # done, pending = await asyncio.wait([task, client.close()], return_when=asyncio.FIRST_COMPLETED)
        # for t in pending:
        #     t.cancel()

        print("Client User: ", client.user)
        print(f'{client.user} status: {client.status}')
        print(f'{client.user} is connected to the following guild:')
        print(f'{client.user} current activity: {client.activity}')
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
            print("CHANNEL GET SUCCESS: ", channel)
        except:
            print("CHANNEL GET FAILED")

    print("History: ", history_days)
    print("CHANNEL_ID POST: ", channel_id)
    print("CHANNEL POST: ", channel)

    filename = 'output.txt'

    if os.path.exists(filename):
        outputFile = open(filename, mode='r+')
    else:
        outputFile = open(filename, 'x')

    async for message in channel.history(limit=history_days, oldest_first=True):
        # process message here
        print("MESSAGE: ", message.content)
        outputFile.write(message.content)
        outputFile.write("\n")

    outputFile.close()


# asyncio.get_event_loop().run_until_complete(main())
asyncio.run(main())
