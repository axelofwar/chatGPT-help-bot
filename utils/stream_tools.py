import json
import os
import requests
import yaml
import postgres_tools as pg
import pandas as pd
from dotenv import load_dotenv
if 'GITHUB_ACTION' not in os.environ:
    load_dotenv()

'''
Tools for interacting with the Twitter API in a filtered stream - contains functions for:
    - Setting up the bearer token
    - Getting the username of a tweet author by their author id
    - Getting the rules from the rules.yml file
    - Adding rules to the rules.yml file
    - Removing rules from the rules.yml file
    - Updating the rules on the Twitter API
'''

update_flag = False
with open("utils/yamls/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
# bearer_token = os.environ["TWITTER_BEARER_TOKEN"]
tweetsTable = config["metrics_table_name"]
usersTable = config["aggregated_table_name"]


# SET BEARER TOKEN AUTH
def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r


# CALL USERS ENDPOINT FOR USERNAME OF TWEETER BY TWEET AUTHOR ID
def get_username_by_author_id(author_id):
    response = requests.get(
        f"https://api.twitter.com/2/users/{author_id}",
        auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    return response.json()


# GET RULES OF CURRENT STREAM
def get_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


# DELETE CURRENT SET STREAM SET RULES
def delete_all_rules(rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))


# SET CURRENT STREAM RULES
def set_rules(delete, update_flag):
    # add more error handling for real-time rule adjustment gaps
    with open("utils/yamls/rules.yml", "r") as file:
        axel_rules = yaml.load(file, Loader=yaml.FullLoader)

    print("RULES SAVED TO rules.yml")
    print("UPDATE VALUE IN SET: ", update_flag)
    if update_flag:
        axel_rules = axel_rules + \
            [{"value": config["ADD_RULE"], "tag": config["ADD_TAG"]}, ]
        with open("utils/yamls/rules.yml", "w") as file:
            file.write(str(axel_rules))

        print("RULE VALUE UPDATED:\n", update_flag)
        print(("ADDED RULES USED:\n", axel_rules))

    # Reconnect stream if not active and set rules again
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    rules = get_rules()
    if response.status_code != 200:
        delete_all_rules(rules)
        print("Reconnecting to the stream...")
        with open("utils/yamls/config.yml", "w") as file:
            config["RECONNECT_COUNT"] += 1
            yaml.dump(config, file)

    payload = {"add": axel_rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    print(json.dumps(response.json()))


# UPDATE CURRENT STREAM RULES
def update_rules():
    with open("utils/yamls/config.yml", "r") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    if "ADD_RULE" in config:
        rule = config["ADD_RULE"]
        update_flag = True
        print("UPDATED TO TRUE: ", update_flag)
    else:
        print("No rule to add")

    if rule == "":
        update_flag = False
        print("UPDATED TO FALSE: ", update_flag)
    else:
        print("SETTING NEW RULES")
        delete = delete_all_rules(get_rules())

        set_rules(delete, update_flag)
        update_flag = False
    with open("utils/yamls/config.yml", "w") as file:
        config["ADD_RULE"] = ""
        yaml.dump(config, file)
        print("RULE RESET TO EMPTY")


# REMOVE CURRENT STREAM RULES
def remove_rules(rules):
    remove_it = config["REMOVE_RULE"]
    if remove_it == "":
        print("NO RULE IN CONFIG TO REMOVE")
        return None
    new_rules = []
    for rule in rules:
        if rule["value"] != remove_it:
            new_rules.append(rule)
    print("NEW RULES: ", new_rules)
    with open("utils/yamls/rules.yml", "w") as file:
        file.write(str(new_rules))
    with open("utils/yamls/config.yml", "w") as file:
        config["REMOVE_RULE"] = ""
        yaml.dump(config, file)
        print("REMOVE RULE RESET TO EMPTY")

    delete_all_rules(get_rules())
    set_rules(new_rules, update_flag)
    remove_flag = True
    return remove_flag


# USE TWEETS ENDPOINT TO GET TWEEET DATA BY TWEET ID
def get_data_by_id(tweet_id):
    response = requests.get(
        f"https://api.twitter.com/2/tweets/{tweet_id}?expansions=author_id,entities.mentions.username,geo.place_id,referenced_tweets.id&media.fields=url&poll.fields=options&tweet.fields=public_metrics",
        auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get tweet data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    return response.json()


# GET ENGAGEMENT METRICS FOR TWEET BY TWEET ID
def get_tweet_metrics(tweet_id):
    response = requests.get(
        f"https://api.twitter.com/1.1/statuses/show.json?id={tweet_id}",
        auth=bearer_oauth
    )

    if response.status_code != 200:
        raise Exception(
            "Cannot get tweet data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    return response.json()


def update_aggregated_metrics(engine, author_username, users_df, tweets_df):
    aggregated_likes, aggregated_retweets, aggregated_replies, aggregated_impressions = 0, 0, 0, 0

    for user in tweets_df["index"].values:
        if user == author_username:
            print(
                f"{user} to aggregate found in Metrics Table")

            user_rows = pg.get_all_user_metric_rows(
                engine, tweetsTable, author_username)
            for item in user_rows:
                print("ROW TO AGGREGATE: ", item[0])
                # potential error here if item is None
                if item != None:
                    aggregated_likes += int(item[2])
                    print("AGGREGATED LIKES: ", aggregated_likes)
                    aggregated_retweets += int(item[3])
                    print("AGGREGATED RETWEETS: ", aggregated_retweets)
                    aggregated_replies += int(item[4])
                    print("AGGREGATED REPLIES: ", aggregated_replies)
                    try:
                        aggregated_impressions += int(item[5])
                        print("AGGREGATED IMPRESSIONS: ",
                              aggregated_impressions)
                    except:
                        print("NO IMPRESSIONS TO AGGREGATE")
                        aggregated_impressions = users_df.loc[users_df["index"]
                                                              == author_username]["Impressions"].values[0]

                row = users_df.loc[users_df["index"]
                                   == author_username]
                # print("Row Vals: ", row.values)
                if row.empty == False:
                    row = row.values[0]
                    if len(row) > 6:
                        row = row[1:]
                        if "level_0" in users_df.columns:
                            print("DAMNIT")
                            users_df.dropna(inplace=True)
                            users_df.drop(
                                columns=["level_0"], axis=1, inplace=True)

                if user in users_df["index"].values:
                    print(
                        "Updating aggregated values in Users Table...")
                    users_df.loc[users_df["index"] == author_username, [
                        "Favorites"]] = aggregated_likes
                    print("Aggregated Likes updated: ", aggregated_likes)
                    users_df.loc[users_df["index"] == author_username, [
                        "Retweets"]] = aggregated_retweets
                    print("Aggregated Retweets updated: ",
                          aggregated_retweets)
                    users_df.loc[users_df["index"] == author_username, [
                        "Replies"]] = aggregated_replies
                    print("Aggregated Replies updated: ",
                          aggregated_replies)
                    users_df.loc[users_df["index"] == author_username, [
                        "Impressions"]] = aggregated_impressions
                    print("Aggregated Impressions updated: ",
                          aggregated_impressions)

                    users_df.to_sql(
                        usersTable, engine, if_exists="replace", index=False)
                    print(
                        f"Aggregated values for {author_username} in Users table updated")
                    print("DF Users Table: ", users_df)


def update_tweets_table(engine, id, tweets_df, included_likes, included_retweets, included_replies, included_impressions):
    print(
        f"Tweet #{id} already exists in Metrics table")
    print("Updating Metrics table...")
    row = tweets_df.loc[tweets_df["Tweet ID"]
                        == id]
    # print("Row Vals: ", row.values)

    row = row.values[0]
    # print("Size row: ", len(row))
    if len(row) > 6:
        row = row[1:]
        if "level_0" in tweets_df.columns:
            print("DAMNIT")
            tweets_df.dropna(inplace=True)
            tweets_df.drop(
                columns=["level_0"], axis=1, inplace=True)
    favorites = row[2]
    retweets = row[3]
    replies = row[4]
    impressions = row[5]

    # update the values in the existing table
    if int(included_likes) > int(favorites):
        print(f"Metrics Likes updated to {included_likes}")
        tweets_df.loc[tweets_df["Tweet ID"] == id, [
            "Favorites"]] = included_likes
    if int(included_retweets) > int(retweets):
        print(
            f"Metrics Retweets updated to {included_retweets}")
        tweets_df.loc[tweets_df["Tweet ID"] == id, [
            "Retweets"]] = included_retweets
    if int(included_replies) > int(replies):
        print(
            f"Metrics Replies updated to {included_replies}")
        tweets_df.loc[tweets_df["Tweet ID"] == id, [
            "Replies"]] = included_replies
    if int(included_impressions) > int(impressions):
        print(
            f"Metrics Impressions updated to {included_impressions}")
        tweets_df.loc[tweets_df["Tweet ID"] == id, [
            "Impressions"]] = included_impressions

    if "level_0" in tweets_df.columns:
        print("DAMNIT")
        tweets_df.drop(
            columns=["level_0"], inplace=True)

    # rework this to write only the updated values - not rewrite the whole table
    tweets_df.to_sql(
        tweetsTable, engine, if_exists="replace", index=False)
    # here we are losing the engager on updates in favor of not addding duplicates
    # and also not messing with our existing index values

    # continue here
    # decide how to update only the rows that have changed
    # get totals of engagers vs. author and weight them accordingly
    print("User in Metrics Table updated")


def update_pfp_tracked_table(engine, pfp_table, name, username, agg_likes, agg_retweets, agg_replies, agg_impressions):
    pfp_table_name = config["pfp_table_name"]
    print("Updating PFP Tracked Table...")
    # check if the user is already in the table
    pfp_table = pd.read_sql_table(pfp_table_name, engine)

    if pfp_table.empty == True:
        print("PFP Tracked Table is empty")
        pfp_table = pd.DataFrame(index=[username],
                                 data=[
                                     [username, name, agg_likes, agg_retweets, agg_replies, agg_impressions]],
                                 columns=["index", "Name", "Favorites", "Retweets", "Replies", "Impressions"])
        print("PFP Tracked Table Created: ", pfp_table)
        pfp_table.to_sql(
            pfp_table_name, engine, if_exists="replace", index=False)
        print(f"User {name} added to PFP Tracked Table")

    iter = 0
    if username in pfp_table["index"].values:
        # print(f"User {name} already exists in PFP Tracked Table")
        # update the values in the existing table only if they are greater than the existing values
        if int(agg_likes) > int(pfp_table.loc[pfp_table["index"] == username, "Favorites"].values[iter]):
            print(f"PFP Tracked Likes updated to {agg_likes}")
            pfp_table.loc[pfp_table["index"] == name, [
                "Favorites"]] = agg_likes
        if int(agg_retweets) > int(pfp_table.loc[pfp_table["index"] == username, "Retweets"].values[iter]):
            print(
                f"PFP Tracked Retweets updated to {agg_retweets}")
            pfp_table.loc[pfp_table["index"] == name, [
                "Retweets"]] = agg_retweets
        if int(agg_replies) > int(pfp_table.loc[pfp_table["index"] == username, "Replies"].values[iter]):
            print(
                f"PFP Tracked Replies updated to {agg_replies}")
            pfp_table.loc[pfp_table["index"] == name, [
                "Replies"]] = agg_replies
        if int(agg_impressions) > int(pfp_table.loc[pfp_table["index"] == username, "Impressions"].values[iter]):
            print(
                f"PFP Tracked Impressions updated to {agg_impressions}")
            pfp_table.loc[pfp_table["index"] == username, [
                "Impressions"]] = agg_impressions

        iter += 1

        pfp_table.to_sql(
            pfp_table_name, engine, if_exists="replace", index=False)
    # print("DF PFP Tracked Replaced Table: ", pfp_table)

    if username not in pfp_table["index"].values:
        print(f"User {username} does not exist in PFP Tracked Table")
        # add the user to the table
        pfp_table = pd.DataFrame(index=[name],
                                 data=[[username, name, agg_likes, agg_retweets, agg_replies, agg_impressions]], columns=["index", "Name", "Favorites", "Retweets", "Replies", "Impressions"])
        pfp_table.to_sql(
            pfp_table_name, engine, if_exists="append", index=False)
        print(
            f"User {username} added to PFP Tracked table")
    # print("DF PFP Tracked Appended Table: ", pfp_table)

    return pfp_table


def create_dataFrame(id, author_username, author_name, likes, retweets, replies, impressions):
    authors_index = [author_username]

    df0 = pd.DataFrame(
        index=authors_index, data=author_name, columns=["Author"])
    df1 = pd.DataFrame(
        index=authors_index, data=int(likes), columns=["Favorites"])
    df2 = pd.DataFrame(
        index=authors_index, data=int(retweets), columns=["Retweets"])
    df3 = pd.DataFrame(
        index=authors_index, data=int(replies), columns=["Replies"])
    df4 = pd.DataFrame(
        index=authors_index, data=int(impressions), columns=["Impressions"])
    df5 = pd.DataFrame(
        index=authors_index, data=id, columns=["Tweet ID"])
    df = pd.concat([df0, df1, df2, df3, df4, df5], axis=1)

    return df
