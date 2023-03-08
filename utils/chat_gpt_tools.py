import openai
import os
import yaml
import asyncio

from dotenv import load_dotenv
load_dotenv()

'''
Tools for interacting with the OpenAI API - contains functions for:
    - Setting up the OpenAI API key
    - Getting the response from the Chat GPT API
'''

# LOAD PARAMETERS
with open("utils/yamls/params.yml", "r") as paramFile:
    params = yaml.load(paramFile, Loader=yaml.FullLoader)


# POPULATE OPENAI PARAMETERS
openai.api_endpoint = params["openai_endpoint"]

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


async def main():
    with open("outputs/filt_stream.txt", "r") as promptFile:
        prompt = promptFile.read()
        promptFile.close()
    prompt = "Simplify this code: " + prompt
    response = await chatGPTcall(prompt, params["davinci"], params["temp"], 5000)
    print(response.choices[0].text)

asyncio.run(main())
