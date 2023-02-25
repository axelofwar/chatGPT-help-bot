# Setup - Axelofwar Python Bot

1. If you don’t have Python installed, [install it from here](https://www.python.org/downloads/) OR

- **LINUX**:

```bash
$ sudo apt-get install python3
```

- **MAC**:

```bash
$ brew install python
```

- **WINDOWS**: gotta use the website + .exe lol

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

11. Add your [postgresql](https://www.postgresql.org/) credentials (use [pgAdmin4](https://www.pgadmin.org/) for gui db interaction) to the `.env` file.
    > - `POSTGRESQL_HOST` -> localhost currently fine to leave
    > - `POSTGRESQL_PORT` -> 5433 currently fine to leave (5432 = postgres def)

- `POSTGRES_USER` -> username of your database table owner
- `POSTGRES_PASSWORD` -> password of your database table owner

12. Edit `config.yml` with desired run parameters - the most important are:

- `ADD_RULE` -> add a mention to track
- `ADD_TAG` -> update the tag for which all tweets matching the rule is stored under
- `REMOVE_RULE` -> remove a mention to track
- `account_to_query` -> primary twitter account to track mentions of on init
- `db_name` -> the name of your database or postgresql server
- `table_name` -> the name of the table in your database or server
- `chat_channel_id` -> default channel if none is entered in UI or permissions not attained (lower case) - this is used to query the questions and user inptus
- `data_channel_id` -> this is the channel to use in order to answer the question
- `tweet_history` -> number of tweets from archive you want to pull (more = longer process time)

> (for `app.py` discord and chatGPT use -> edit `params.yml` as well
>
> - `prompt` -> details of what question you want to ask chatGPT

13. Create db and table (if not present) - use [pgAdmin4](https://www.pgadmin.org/) for easiest interaction OR use [postgresql](https://www.postgresql.org/) if comfortable.

- `config.yml` -> update **db_name** and **table_name** to values from previous step

In pgAdmin4 or postgresql:

- Create server on `localhost:5433/` with your `db name`, `username`, and `password`
- Populate the `metrics_table_name` and `aggregated_table_name` with your database values in `config.yml`

You can follow the pgadmin4 steps to setup your own - or you can import `df_table.csv` to your postgresql server (untested)

#

# Run steps by use case

12. Run the app for discord history based AI responses

```bash
$ python3 app.py
```

You should now see three .txt files as well as terminal outputs, the .txt files are labeled appropriately:

> - `tweets.txt` holds tweet history info
> - `discord.txt` holds discord channel history info
> - `output.txt` that will hold the chatGPT responses

13. Run the app for twitter listener bot + database update

```bash
$ python3 utils/filtered_stream.py
```

14. Update rules while running stream - in
    `config.yml`:

- update `ADD_RULE`: with your @account or #tag to add
- update `ADD_TAG`: with the project name/tag

```bash
$ python3 utils/update_rules.py
```

15. Remove rules while running stream - in
    `config.yml`:

- update `REMOVE_RULE`: with your @account or #tag to remove

```bash
$ python3 utils/remove_rules.py
```

#

## NOTES

### filtered_stream.py notes:

Currently if updated metrics are detected we are updating the entire existing data table. We may want to change this to only update the row for efficiency. Two primary files are:

- `app.py` -> ui + discord + search_tweets() + gpt interaction
- `utils/filtered_stream.py` -> stream for engagement metrics to db
  > this and it's associated files are the current development focus.

Other standalone functions for testing include:

- `update_database.py` to update a specific tweet's metric data
- `ui.py` to run standalone UI for discord + gpt interaction
- `app.py` to run discord + gpt interaction E2E (ui commented - see config.yml)

There are three user's currently identified in the tweet tracking logic of filtered_stream.py

- `author` = originator of the tweet being tracked
- `included` = the author of the tweet included (retweeted, quoted, replied to, mentioned, etc.)
- `engager` = currently should return the same as the above two - as well as any other accounts mentioned in the tweet.
  > _engager_ could be used in the future to reward all users mentioned instead of just author + engager
  > it is currently used to confirm that the author of the included tweet is indeed that author - could be used to reward tweet being engaged more than engager via multiplier as decided.

There are 6 columns in the table - all self explanatory expect:

- `index` = engager @username
- `author` = included author's display name
- `Tweet ID` = id used to track and aggregate metrics per tweet

_TODO_: create another table that holds the users and aggregates all tweet IDs belonging to a user - and their metrics - to user

#

### app.py notes:

Currently only one resposne is stored and replaced each time. This may be changed to preserve response history for better future answering depending on database decisions.

## OpenAI API Quickstart - Python example app

Here is an example pet name generator app used in the OpenAI API [quickstart tutorial](https://beta.openai.com/docs/quickstart). It uses the [Flask](https://flask.palletsprojects.com/en/2.0.x/) web framework. Check out the tutorial or follow the instructions below to get set up. This example was stripped as a starting place for this project.
