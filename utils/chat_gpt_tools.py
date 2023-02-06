import openai
import os
import yaml

from dotenv import load_dotenv
load_dotenv()

with open("utils/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)


# POPULATE OPENAI PARAMETERS
openai.api_endpoint = config["OPENAI_ENDPOINT"]

openai.api_key = os.environ['OPENAI_API_KEY']
if not openai.api_key:
    openai.api_key = ""
    print("OPENAI API KEY NOT FOUND")


# CHAT GPT REPONSE CALL
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
