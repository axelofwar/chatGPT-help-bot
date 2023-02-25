import json
import os
import pandas as pd
import requests
from dotenv import load_dotenv
import time
import yaml
import stream_tools as st
import postgres_tools as pg

load_dotenv()

'''
This is app for the filtered twitter stream - contains functions for:
    - Setting up the bearer token
    - Getting the username of a tweet author by their author id
    - Getting the rules from the rules.yml file
    - Adding rules to the rules.yml file
    - Removing rules from the rules.yml file
    - Updating the rules on the Twitter API

Currently we are using the filtered stream to get tweets from the following users:
    - @axelofwar
    - @y00tsNFT
    - DeGodsNFT

Status: Working - 2023-02-23 - run the stream and store tweets matching the rules
    - store tweet ID and get info from the stream endpoint
    - get engager metrics from the stream endpoint
    - get author metrics from users endpoint by author ID from stream endpoint included user
    - create dataframes from gathered data and compare to database
    - if tweet ID is not in database, add to database
    - if tweet ID is in database, replace WHOLE database with tweets_df + updated metrics

TODO: update to replace only the row - not the whole database with tweets_df + updated
'''

with open("utils/yamls/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
# To set your enviornment variables in your terminal run the following line:
    config["RECONNECT_COUNT"] = 0

bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
engine = pg.start_db(config["db_name"])
tweetsTable = config["metrics_table_name"]
usersTable = config["aggregated_table_name"]


# check if tables exist and create if not
pg.check_metrics_table(engine, tweetsTable)
pg.check_users_table(engine, usersTable)


update_flag = False
remove_flag = False
author = ""
df = pd.DataFrame()
export_df = pd.DataFrame()
export_include_df = pd.DataFrame()


def get_export_df():
    return export_include_df


def get_stream(update_flag, remove_flag):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream", auth=st.bearer_oauth, stream=True,
    )

    print(response.status_code)

    if response.status_code == 429:
        print("TOO MANY REQUESTS")
        time.sleep(180)  # wait 3 minutes
        # waiting only 60 seconds doesn't seem to solve the problem
        get_stream(update_flag, remove_flag)

    if response.status_code != 200:
        try:
            print("Reconnecting to the stream...")
            with open("utils/yamls/config.yml", "w") as file:
                config["RECONNECT_COUNT"] += 1
                yaml.dump(config, file)
            st.set_rules(st.delete_all_rules(st.get_rules()), update_flag)
        except:
            raise Exception(
                "Cannot get stream (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )
    for response_line in response.iter_lines():
        if response_line:
            print("\n\nGOT RESPONSE!")
            if update_flag:
                print("UPDATING RULES")
                st.update_rules()
                update_flag = False
            if remove_flag:
                print("REMOVING RULES")
                st.remove_rules(st.get_rules())
                remove_flag = False

            json_response = json.loads(response_line)

            # print raw data dump
            # print(json.dumps(json_response, indent=4, sort_keys=True))
            # data_response = json_response["data"]["text"]

            id = json_response["data"]["id"]
            matching_rules = json_response["matching_rules"]
            full_text = json_response["data"]["text"]
            print("\nMATCHING RULES: ", matching_rules)
            print("\nTEXT: ", full_text)

            # TODO: if original tweet or quoted/retweeted
            # aggregate (x/y)*engagement to original author
            # aggregate (x/x)*engagement to quote/retweeter

            print("\nTweet ID: ", id)
            tweet_data = st.get_data_by_id(id)

            # print raw data dump
            # print("\nDATA BY ID: ", json.dumps(
            #     tweet_data, indent=4, sort_keys=True))
            # print("\nPublic Metrics: ", tweet_data["data"]["public_metrics"])

            # improve wait/sleep to make sure rules GET call has returned json respones
            # once this is done, remove the nested if and try checks
            try:
                if tweet_data["data"]["author_id"]:
                    if "author_id" in tweet_data["data"]:
                        author_id = tweet_data["data"]["author_id"]
                        author = st.get_username_by_author_id(
                            tweet_data["data"]["author_id"])
                        author_username = author["data"]["username"]
                        author_name = author["data"]["name"]
                        print("\nAuthor ID: ", author_id)
                        print("\nAuthor Name: ", author_name)
                        print("\nAuthor Username: ", author_username)
                    else:
                        print("Author ID not found")

                if "referenced_tweets" in tweet_data["data"]:
                    if tweet_data["data"]["referenced_tweets"]:
                        referenced = tweet_data["data"]["referenced_tweets"]
                    print("\nReferenced Tweets: ", referenced)

                if "tweets" in tweet_data["includes"]:
                    if tweet_data["includes"]["tweets"]:
                        included_tweets = tweet_data["includes"]["tweets"]
                        included_users = tweet_data["includes"]["users"]
                    else:
                        included_tweets = None
                        included_users = None

            except KeyError as ke:
                print("KeyError occured: ", ke)
                with open("utils/yamls/config.yml", "w") as file:
                    config["RECONNECT_COUNT"] += 1
                    yaml.dump(config, file)
                print("Restarting stream...")
                get_stream(update_flag, remove_flag)

            id = tweet_data["data"]["id"]
            print("\nTweet ID by tweet_data: ", id)
            engagement_metrics = st.get_likes_retweets_impressions(id)
            tweet_favorite_count = int(engagement_metrics["favorite_count"])
            tweet_retweet_count = int(engagement_metrics["retweet_count"])
            print("\nTweet Favorites: ", tweet_favorite_count)
            print("\nTweet Retweets: ", tweet_retweet_count)

            # TODO: remove .csv and .json outputs to local
            # integrate data frames direct to postgress db
            # create a new table for each new rule(?) allows by communtiy tracking

            authors_index = [author_username]
            df0 = pd.DataFrame(
                index=authors_index, data=author_name, columns=["Author"])
            df1 = pd.DataFrame(index=authors_index, data=int(
                tweet_favorite_count), columns=["Favorites"])
            df2 = pd.DataFrame(index=authors_index, data=int(
                tweet_retweet_count), columns=["Retweets"])
            df3 = pd.DataFrame(index=authors_index,
                               data=id, columns=["Tweet ID"])
            df = pd.concat([df0, df1, df2, df3], axis=1)

            export_df = df
            print("\nExport_df:", export_df)

            if tweet_data["includes"] and "tweets" in tweet_data["includes"]:
                # loop to go through all referenced/included tweets
                for iter in range(len(included_tweets)):
                    included = included_tweets[iter]
                    included_id = included["id"]
                    included_author_id = included["author_id"]
                    included_pub_metrics = included["public_metrics"]

                    included_likes = included_pub_metrics["like_count"]
                    included_reply_count = int(
                        included_pub_metrics["reply_count"])
                    included_retweets = included_pub_metrics["retweet_count"]
                    included_quote_count = included_pub_metrics["quote_count"]
                    included_impressions = int(
                        included_pub_metrics["impression_count"])

                    # print("\nIncluded Tweet ID: ", included_id)
                    # print("\nIncluded/Parent Tweet Author ID: ",
                    #       included_author_id)

                    if included_author_id == author_id:
                        included_author_username = author_username
                        # included_user = st.get_username_by_author_id(

                        #     author_id)
                        included_user = author
                        # included_author_name = included_user["data"]["name"]
                        included_author_name = author_name

                    else:
                        try:
                            included_name = st.get_username_by_author_id(
                                included_author_id)
                            included_author_username = included_name["data"]["username"]
                            included_author_name = included_name["data"]["name"]

                            included_author_username = author_username
                            authors_index = [included_author_username]
                            df0 = pd.DataFrame(
                                index=authors_index, data=author_name, columns=["Author"])
                            df1 = pd.DataFrame(
                                index=authors_index, data=int(included_likes), columns=["Favorites"])
                            df2 = pd.DataFrame(
                                index=authors_index, data=int(included_retweets), columns=["Retweets"])
                            df3 = pd.DataFrame(
                                index=authors_index, data=int(included_reply_count), columns=["Replies"])
                            df4 = pd.DataFrame(
                                index=authors_index, data=int(included_impressions), columns=["Impressions"])
                            df5 = pd.DataFrame(
                                index=authors_index, data=included_id, columns=["Tweet ID"])
                            df = pd.concat(
                                [df0, df1, df2, df3, df4, df5], axis=1)

                        except:
                            print("ERROR ON GET USERNAME BY AUTHOR ID")

                    print("\nAUTHOR OF INCLUDED/PARENT TWEET DIFFERENT FROM AUTHOR")

                    print("\nIncluded/Parent Likes: ", included_likes)
                    print("\nIncluded/Parent Replies: ", included_reply_count)
                    print("\nIncluded/Parent Retweets: ", included_retweets)
                    print("\nIncluded/Parent Quotes: ", included_quote_count)
                    print("\nIncluded/Parent Impressions: ",
                          included_impressions)
                    export_include_df = df

                for iter in range(len(included_users)):
                    engager_user = included_users[iter]
                    engager_id = engager_user["id"]
                    # uncomment this and parse each author id if we want to give points to each mentioned user
                    # print("\nMentioned ID #: ", iter, " ", engager_user_id)

                    # use this if we only want to track the original author and the engager
                    # compare mentioned/included parent user id to original author id
                    if engager_id == author_id:
                        print("\nTweet's Mentioned UserID: ", engager_id,
                              "matches original author ID: ", author_id)
                        # engager_name = engager_user["name"]
                        # engager_username = engager_user["username"]
                        # print("\nMatching Mentioned Author Name: ", engager_name)
                        # print(
                        #     "\nMatching Mentioned Author Username: ", engager_username)

                        engager_author_username = author_username

                        # if engager_author_username in outputs_df.index:
                        df0 = pd.DataFrame(
                            index=authors_index, data=engager_user["name"], columns=["Author"])
                        df1 = pd.DataFrame(
                            index=authors_index, data=int(included_likes), columns=["Favorites"])
                        df2 = pd.DataFrame(
                            index=authors_index, data=int(included_retweets), columns=["Retweets"])
                        df3 = pd.DataFrame(
                            index=authors_index, data=int(included_reply_count), columns=["Replies"])
                        df4 = pd.DataFrame(
                            index=authors_index, data=int(included_impressions), columns=["Impressions"])
                        df5 = pd.DataFrame(
                            index=authors_index, data=included_id, columns=["Tweet ID"])
                        df = pd.concat([df0, df1, df2, df3, df4, df5], axis=1)

                    if engager_id == included_author_id:
                        print("\nTweet's Mentioned UserID: ", engager_id,
                              "matches included/parent author ID: ", included_author_id)
                        # engager_name = engager_user["name"]
                        # engager_username = engager_user["username"]
                        # print("\nMatching Included/Parent Author Name: ",
                        #       engager_name)
                        # print(
                        #     "\nMatching Included/Parent Author Username: ", engager_username)
                        engager_author_username = included_author_username

                        authors_index = [engager_author_username]
                        df0 = pd.DataFrame(
                            index=authors_index, data=included_author_name, columns=["Author"])
                        df1 = pd.DataFrame(
                            index=authors_index, data=int(included_likes), columns=["Favorites"])
                        df2 = pd.DataFrame(
                            index=authors_index, data=int(included_retweets), columns=["Retweets"])
                        df3 = pd.DataFrame(
                            index=authors_index, data=int(included_reply_count), columns=["Replies"])
                        df4 = pd.DataFrame(
                            index=authors_index, data=int(included_impressions), columns=["Impressions"])
                        df5 = pd.DataFrame(
                            index=authors_index, data=included_id, columns=["Tweet ID"])
                        df = pd.concat([df0, df1, df2, df3, df4, df5], axis=1)

                export_include_df = df  # FIX THIS EXPORT DF SO USABLE IN POSTGRES_TOOLS.PY
                print("\nExport Include DF: ", export_include_df)
                print("\nExport DF: ", export_df)

                # update to use non-deprecated method
                if engine.has_table(tweetsTable) == False:
                    print("Creating table...")
                    export_include_df.to_sql(
                        tweetsTable, engine, if_exists="replace")
                    print("Table created")

                else:  # if table already exists, update or append to it
                    tweets_df = pd.read_sql_table(tweetsTable, engine)
                    # if tweet is already being tracked, update the values
                    # need to add another table that aggregates the values by user in this table
                    # that aggregated table will be what is used to make metrics based decisions
                    if included_id in tweets_df["Tweet ID"].values:
                        print(
                            f"Tweet #{included_id} already exists in Metrics table")
                        print("Updating Metrics table...")
                        row = tweets_df.loc[tweets_df["Tweet ID"]
                                            == included_id]
                        print("Row Vals: ", row.values)

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
                        print("Favorites: ", favorites)
                        print("Retweets: ", retweets)
                        print("Replies: ", replies)

                        # update the values in the existing table
                        if int(included_likes) > int(favorites):
                            print(f"Metrics Likes updated to {included_likes}")
                            tweets_df.loc[tweets_df["Tweet ID"] == included_id, [
                                "Favorites"]] = included_likes
                        if int(included_retweets) > int(retweets):
                            print(
                                f"Metrics Retweets updated to {included_retweets}")
                            tweets_df.loc[tweets_df["Tweet ID"] == included_id, [
                                "Retweets"]] = included_retweets
                        if int(included_reply_count) > int(replies):
                            print(
                                f"Metrics Replies updated to {included_reply_count}")
                            tweets_df.loc[tweets_df["Tweet ID"] == included_id, [
                                "Replies"]] = included_reply_count
                        if int(included_impressions) > int(impressions):
                            print(
                                f"Metrics Impressions updated to {included_impressions}")
                            tweets_df.loc[tweets_df["Tweet ID"] == included_id, [
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
                        # then how to aggregate metrics from all tweet IDs per user/author
                        # get totals of engagers vs. author and weight them accordingly
                        print("Metrics Table updated")
                    else:
                        print("Appending to Metrics table...")
                        export_include_df.to_sql(
                            tweetsTable, engine, if_exists="append")
                        print("Metrics Table appended")

                # read the table post changes
                tweets_df = pd.read_sql_table(tweetsTable, engine)
                print("DF Metrics Table: ", tweets_df)

                users_df = pd.read_sql_table(usersTable, engine)
                print("USERS DF: ", users_df)
                # if included_author_username in usersTable["index"].values:
                if users_df.empty == False:
                    for user in users_df["index"].values:
                        print("User: ", user)
                        if user == included_author_username:
                            row = users_df.loc[users_df["index"]
                                               == included_author_username]
                            print("Row Vals: ", row.values)
                            row = row.values[0]
                            if len(row) > 6:
                                row = row[1:]
                                if "level_0" in users_df.columns:
                                    print("DAMNIT")
                                    users_df.dropna(inplace=True)
                                    users_df.drop(
                                        columns=["level_0"], axis=1, inplace=True)

                            Username = row[0]
                            Name = row[1]
                            Favorites = row[2]
                            Retweets = row[3]
                            Replies = row[4]
                            Impressions = row[5]
                            print("Username: ", Username)
                            print("Name: ", Name)
                            print("Favorites: ", Favorites)
                            print("Retweets: ", Retweets)
                            print("Replies: ", Replies)
                            print("Impressions: ", Impressions)

                            # get all tweets in tweets_df that have the included_author_username
                            # then get the sum of all the values for each column
                            # then update the values in the users_df table

                            user_rows = pg.get_user_metric_rows(
                                engine, tweetsTable, included_author_username)

                            for row in user_rows:
                                print("Row: ", row)

                            if int(included_likes) > int(Favorites):
                                print(
                                    f"Aggregated Likes updated to {included_likes}")
                                users_df.loc[users_df["index"] == included_author_username, [
                                    "Favorites"]] = included_likes

                            if int(included_retweets) > int(Retweets):
                                print(
                                    f"Aggregated Retweets updated to {included_retweets}")
                                users_df.loc[users_df["index"] == included_author_username, [
                                    "Retweets"]] = included_retweets

                            if int(included_reply_count) > int(Replies):
                                print(
                                    f"Aggregated Replies updated to {included_reply_count}")
                                users_df.loc[users_df["index"] == included_author_username, [
                                    "Replies"]] = included_reply_count

                            if int(included_impressions) > int(Impressions):
                                print(
                                    f"Aggregated Impressions updated to {included_impressions}")
                                users_df.loc[users_df["index"] == included_author_username, [
                                    "Impressions"]] = included_impressions

                            print(
                                f"User {included_author_username} already exists in table")

                            if "level_0" in users_df.columns:
                                print("DAMNIT")
                                users_df.drop(
                                    columns=["level_0"], inplace=True)

                            users_df.to_sql(
                                usersTable, engine, if_exists="replace", index=False)
                    else:
                        print("Appending to users table...")
                        export_users_df = pd.DataFrame(index=[included_author_username], data=[[included_author_username, included_author_name, included_likes, included_retweets, included_reply_count, included_impressions]], columns=[
                            "index", "Name", "Favorites", "Retweets", "Replies", "Impressions"])
                        export_users_df.to_sql(
                            usersTable, engine, if_exists="append", index=False)
                        print("Users table appended")
                        print("DF Users Table: ", users_df)
                    # the index = engager user name (user who interacted with the included user)
                    # the author = included user name (parent tweet author)
                    # need to decide if we want to keep it that way or change it to the author username of the included user
                    # the included user (author) has more mentions and is more likely to be the one we want to track


def main():
    rules = st.get_rules()
    delete = st.delete_all_rules(rules)
    set = st.set_rules(delete, update_flag)
    get_stream(update_flag, remove_flag)


if __name__ == "__main__":
    main()
