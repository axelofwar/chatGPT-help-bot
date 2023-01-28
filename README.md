# Setup - Axelofwar Python Bot

1. If you don’t have Python installed, [install it from here](https://www.python.org/downloads/)

2. Install OpenAI

- `pip install openai`

3. Clone this repository

4. Navigate into the project directory

   ```bash
   $ cd chatGPT-help-bot
   ```

5. Create a new virtual environment

   ```bash
   $ python -m venv venv
   $ . venv/bin/activate
   ```

6. Install the requirements

   ```bash
   $ pip install -r requirements.txt
   ```

7. Make a copy of the example environment variables file

   ```bash
   $ cp .env.example .env
   ```

8. Add your [OpenAI API key](https://beta.openai.com/account/api-keys) to the newly created `.env` file

9. Add your [Twitter API keys](https://developer.twitter.com/en/portal/dashboard) to the `.env` file

10. Add your [Discord token](https://discord.com/developers/applications) to the `.env` file

11. Edit config.yml with desired run parameters - the most important are:

- account_to_query = twitter account to track mentions of
- discord_channel_id = default channel if none is entered in UI or permissions not be attained (lower case)
- prompt = details of what question you want to ask chatGPT
- tweet_history = number of tweets from archive you want to pull (more = longer process time)

12. Run the app

```bash
$ python3 app.py
```

You should now see three .txt files as well as terminal outputs, the .txt files are labeled appropriately:

> - tweets.txt holds tweet history info
> - discord.txt holds discord channel history info
> - output.txt that will hold the chatGPT responses.

Currently only one resposne is stored and replaced each time. This may be changed to preserve response history for better future answering depending on database decisions.

## OpenAI API Quickstart - Python example app

Here is an example pet name generator app used in the OpenAI API [quickstart tutorial](https://beta.openai.com/docs/quickstart). It uses the [Flask](https://flask.palletsprojects.com/en/2.0.x/) web framework. Check out the tutorial or follow the instructions below to get set up. This example was stripped as a starting place for this project.
