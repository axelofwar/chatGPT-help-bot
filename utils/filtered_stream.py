import json
import os
import pandas as pd
import requests
from dotenv import load_dotenv
import time
import yaml
import stream_tools as st
import postgres_tools as pg
import nft_inspect_tools as nft

if 'GITHUB_ACTION' not in os.environ:
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
    - create users table for with aggregated metrics from tweets table
    - if user ID is not in database, add to database
    - if user ID is in database, replace WHOLE database with users_df + updated aggregated metrics

TODO:
    - update to replace only the row - not the whole table with replace calls when updating metrics
    - add time based functionality that resets the db every 30 days
    - adding nft-inspect api to get pfp status and holder rank
    - do we want one app instance deploy with dynamic table and rule creation?
    - or do we want to have multiple instances for each project connecting to our same database that can modify their own rules?
'''

with open("utils/yamls/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
# To set your enviornment variables in your terminal run the following line:
    config["RECONNECT_COUNT"] = 0

# Twitter API constants
# bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
# bearer_token = os.environ["TWITTER_BEARER_TOKEN"]
# Postgres constants
engine = pg.start_db(config["db_name"])
tweetsTable = config["metrics_table_name"]
usersTable = config["aggregated_table_name"]
pfpTable = config["pfp_table_name"]


# check if tables exist and create if not
pg.check_metrics_table(engine, tweetsTable)
pg.check_users_table(engine, usersTable)
pg.check_pfp_table(engine, pfpTable)

# Init flags and empty frames for those used throughout the app
update_flag = False
remove_flag = False
author = ""
df = pd.DataFrame()
export_df = pd.DataFrame()
export_include_df = pd.DataFrame()
# pfp_df = pd.DataFrame()

# def get_export_df():
#     return export_include_df


def get_stream(update_flag, remove_flag):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream", auth=st.bearer_oauth, stream=True,
    )

    print(response.status_code)

    if response.status_code == 429:
        print("TOO MANY REQUESTS")
        time.sleep(300)  # wait 5 minutes
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
            '''
            We can use this matching rules object in the future to determine which project's table we should add the data to
            '''
            print("\nTEXT: ", full_text)

            # TODO: if original tweet or quoted/retweeted
            # aggregate (x/y)*engagement to original author
            # aggregate (x/x)*engagement to quote/retweeter

            print("\nTweet ID: ", id)
            tweet_data = st.get_data_by_id(id)

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
            engagement_metrics = st.get_tweet_metrics(id)
            tweet_favorite_count = int(engagement_metrics["favorite_count"])
            tweet_retweet_count = int(engagement_metrics["retweet_count"])
            # print("\nTweet Favorites: ", tweet_favorite_count)
            # print("\nTweet Retweets: ", tweet_retweet_count)

            # TODO: create a new table for each new rule(project?) allows by communtiy tracking
            # do we want to deploy a new instance of the app for each project?
            # or do we want to have a single instance of the app that can track multiple projects?

            # TODO: index by tweetID on metrics table instead of author username in order to prevent duplicate rows
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
            # print("\nExport_df:", export_df)

            if tweet_data["includes"] and "tweets" in tweet_data["includes"]:
                # loop to go through all referenced/included tweets
                for iter in range(len(included_tweets)):
                    included = included_tweets[iter]
                    included_id = included["id"]
                    included_author_id = included["author_id"]
                    included_pub_metrics = included["public_metrics"]

                    included_likes = included_pub_metrics["like_count"]
                    included_replies = int(
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
                        included_author_name = author_name
                    else:
                        try:
                            included_name = st.get_username_by_author_id(
                                included_author_id)
                            included_author_username = included_name["data"]["username"]
                            included_author_name = included_name["data"]["name"]

                            df = st.create_dataFrame(included_id, included_author_username, author_name, included_likes,
                                                     included_retweets, included_replies, included_impressions)
                        except:
                            print("ERROR ON GET USERNAME BY AUTHOR ID")

                    print("\nAUTHOR OF INCLUDED/PARENT TWEET DIFFERENT FROM AUTHOR")
                    print("\nIncluded/Parent Likes: ", included_likes)
                    print("\nIncluded/Parent Replies: ", included_replies)
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

                        df = st.create_dataFrame(included_id, engager_author_username,
                                                 engager_user["name"], included_likes, included_retweets,
                                                 included_replies, included_impressions)

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

                        df = st.create_dataFrame(included_id, engager_author_username, included_author_name, included_likes,
                                                 included_retweets, included_replies, included_impressions)

                export_include_df = df
                # print("\nExport Include DF: ", export_include_df)
                # print("\nExport DF: ", export_df)

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
                    if engine.has_table(tweetsTable) == True and tweets_df.empty:
                        print("Table exists but is empty. Appending data...")
                        export_include_df.to_sql(
                            tweetsTable, engine, if_exists="append")
                        print("Data appended to table")

                    tweets_df = pd.read_sql_table(tweetsTable, engine)
                    if included_id in tweets_df["Tweet ID"].values:
                        st.update_tweets_table(engine, included_id, tweets_df, included_likes,
                                               included_retweets, included_replies, included_impressions)
                    else:
                        print("Appending to Metrics table...")
                        export_include_df.to_sql(
                            tweetsTable, engine, if_exists="append")
                        print("New user in Metrics Table appended")
                    # except:

                # read the table post changes
                tweets_df = pd.read_sql_table(tweetsTable, engine)
                print("DF Metrics Table: ", tweets_df)

                users_df = pd.read_sql_table(usersTable, engine)

                if users_df.empty:
                    print("Users table exists but is empty. Appending data...")
                    export_users_df = pd.DataFrame(index=[included_author_username],
                                                   data=[[included_author_username, included_author_name,
                                                          included_likes, included_retweets, included_replies,
                                                          included_impressions]],
                                                   columns=["index", "Name", "Favorites",
                                                            "Retweets", "Replies", "Impressions"])
                    export_users_df.to_sql(
                        usersTable, engine, if_exists="append", index=False)
                    print("Data appended to table")

                # if user is already being tracked, update the values in our aggregated table
                if included_author_username in users_df["index"].values:
                    st.update_aggregated_metrics(
                        engine, included_author_username, users_df, tweets_df)
                else:
                    # FIXED AUTHOR AND USERNAME NOT MATCHING FROM ROW 32 ON IN USERS_TABLE UNTIL RESET
                    print("Appending to users table...")
                    export_users_df = pd.DataFrame(index=[included_author_username],
                                                   data=[[included_author_username, included_author_name,
                                                          included_likes, included_retweets, included_replies,
                                                          included_impressions]],
                                                   columns=["index", "Name", "Favorites",
                                                            "Retweets", "Replies", "Impressions"])
                    export_users_df.to_sql(
                        usersTable, engine, if_exists="append", index=False)
                    print(
                        f"New user {included_author_name} in Users table appended (fs comment)")
                    print("DF Users Table: ", users_df)
                    if users_df.empty == True:
                        print("Users table is empty, appending...")
                        export_users_df.to_sql(
                            usersTable, engine, if_exists="append")
                        print("Table appended")

                '''
                DONE: search this members df to determine if the user has the pfp - which should be one of the columns
                if they do, then search the aggregated metrics table
                and put their metrics into a dataframe that is appended with each member that both:
                - has the pfp
                - has been tracked in the aggregated metrics table
                if they don't - don't add them to the final haspfp + tracked table

                TODO: determine what we want to do with rank and reach stats
                - do we want to add them to the pfp table?
                These are stored in lists and each index corresponds to the same 
                index in the wearing_list - so we can use that to match the user
                to their rank and reach and add them to the pfp table
                '''

                # if user is already being tracked, add them to the users table
                members_df = nft.get_db_members_collections_stats(
                    engine, config["collections"], usersTable)

                # print("MEMBERS DF: ", members_df)
                # members_df.to_csv("outputs/current_member.csv")

                wearing_list, rank_list, global_reach_list = nft.get_wearing_list(
                    members_df)

                # we can create and idx and add the user's rank and reach to pfp_df

                for user in wearing_list:
                    # ensure we update existing tables that will be used each loop
                    pfp_df = pd.read_sql_table(pfpTable, engine)
                    users_df = pd.read_sql_table(usersTable, engine)

                    # row = pfp_df.loc[pfp_df["Name"] == user]
                    # print("ROW: ", row)
                    try:
                        likes = pfp_df.loc[pfp_df["Name"]
                                           == user, "Favorites"].values[0]
                        retweets = pfp_df.loc[pfp_df["Name"]
                                              == user, "Retweets"].values[0]
                        replies = pfp_df.loc[pfp_df["Name"]
                                             == user, "Replies"].values[0]
                        impressions = pfp_df.loc[pfp_df["Name"]
                                                 == user, "Impressions"].values[0]
                    except:
                        likes = 0
                        retweets = 0
                        replies = 0
                        impressions = 0

                    if user in users_df["Name"].values:
                        # print("USER NAME ENDPOINT RESPONSE: ", response.json())
                        try:
                            response = requests.get(
                                f'https://api.twitter.com/1.1/users/search.json?q={user}&count=1', auth=st.bearer_oauth)

                            username = response.json()[0]["screen_name"]
                            if response.status_code != 200:
                                print("User name endpoint failed")
                                print(response.json())
                                print(response.text)
                            if response.text == "ERROR":
                                username = users_df.loc[users_df["Name"]
                                                        == user, "index"].values[0]
                            pass
                            # continue
                        except:
                            username = users_df.loc[users_df["Name"]
                                                    == user, "index"].values[0]
                            # this could be the engager so we need to handle this better in the case the api doesnt return data
                            # OR we need to preserve the included_author_username in the users table
                            # instead of the engager as the index and propogate that change throughout the code
                            # this should help reduce api endpoint call stress as well

                        agg_likes = users_df.loc[users_df["Name"]
                                                 == user, "Favorites"].values[0]
                        agg_retweets = users_df.loc[users_df["Name"]
                                                    == user, "Retweets"].values[0]
                        agg_replies = users_df.loc[users_df["Name"]
                                                   == user, "Replies"].values[0]
                        agg_impressions = users_df.loc[users_df["Name"]
                                                       == user, "Impressions"].values[0]

                        if likes < agg_likes or retweets < agg_retweets or replies < agg_replies or impressions < agg_impressions:
                            print("Updating PFP table...")
                            pfp_updated_table = st.update_pfp_tracked_table(
                                engine, pfp_df, user, username, agg_likes, agg_retweets, agg_replies, agg_impressions
                            )
                            print(
                                f"User {user} iterated through and updated if required")

                    else:
                        new_pfp_user = pd.DataFrame(index=[username],
                                                    data=[
                                                        [username, user, agg_likes, agg_retweets, agg_replies, agg_impressions]],
                                                    columns=["index", "Name", "Favorites",
                                                             "Retweets", "Replies", "Impressions"])
                        new_pfp_user.to_sql(
                            pfpTable, engine, if_exists="append", index=False)

                        print(
                            f"User {user} appended to PFP table (fs comment)")
                if wearing_list != []:
                    print("PFP DF UPDATED: ", pfp_df)


def main():
    rules = st.get_rules()
    delete = st.delete_all_rules(rules)
    set = st.set_rules(delete, update_flag)
    get_stream(update_flag, remove_flag)


if __name__ == "__main__":
    main()
