import asyncio
import yaml
from utils import twitter_tools as th
# from tweepy import StreamingClient
from dotenv import load_dotenv
load_dotenv()

with open("utils/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)


async def main():
    twitterAPI = await th.init_twitter()
    myStream, runner = await th.init_listener(twitterAPI, config["account_to_query"])
    return print("STREAM: ", myStream, "RUNNER: ", runner)
    # TODO: FIX SO THAT RIGHT ACCOUNTS ARE TRACKED WHEN STREAMING CLIENT RUNNING

asyncio.run(main())
