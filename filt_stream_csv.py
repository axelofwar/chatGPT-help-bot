import json
import os
import pandas as pd
import requests
from dotenv import load_dotenv
import time
import yaml
import csv
import stream_tools as st
load_dotenv()

bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
update_flag = False
remove_flag = False
author = ""
df = pd.DataFrame()
export_df = pd.DataFrame()


with open("utils/yamls/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
# To set your enviornment variables in your terminal run the following line:
    config["RECONNECT_COUNT"] = 0


def get_export_df():
    return export_df


def get_stream(update_flag, remove_flag):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream", auth=st.bearer_oauth, stream=True,
    )

    print(response.status_code)

    if response.status_code == 429:
        print("TOO MANY REQUESTS")
        time.sleep(60)
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

            engagement_metrics = st.get_likes_retweets_impressions(id)
            tweet_favorite_count = int(engagement_metrics["favorite_count"])
            tweet_retweet_count = int(engagement_metrics["retweet_count"])
            print("\nTweet Favorites: ", tweet_favorite_count)
            print("\nTweet Retweets: ", tweet_retweet_count)

            # TODO: remove .csv and .json outputs to local
            # integrate data frames direct to postgress db
            # create a new table for each new rule(?) allows by communtiy tracking

            try:
                outputs_df = pd.read_csv(
                    "outputs/df.csv", index_col=0, on_bad_lines="skip")
                # outputs_json = pd.read_json("outputs/df.json")
                # improve this if handling to actually catch when the author is not in the df
                if author_username not in outputs_df.index:
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

                    outputs_df = outputs_df.append(df)
                    # outputs_json = outputs_json.append(df)
                    export_df = df
                else:
                    outputs_df.loc[author_username, "Author"] = author_name
                    outputs_df.loc[author_username, "Favorites"] = int(
                        tweet_favorite_count)
                    outputs_df.loc[author_username, "Retweets"] = int(
                        tweet_retweet_count)
                    outputs_df.loc["Tweet ID"] = id

                    author = df['Author']
                    export_df = df
                    print("\nauthor_username found in outputs_df.index: ", author)

                # READ FROM JSON TESTS
                # TODOO: if I can get this working better than .csv I will use this instead

                # author_dict = outputs_json['Author'].to_dict()
                # author_json = list(author_dict.values())[0]
                # print("\nAUTHOR JSON: ", author_json)

                # outputs_json = outputs_df.to_json(
                #     "outputs/df.json", orient="records")
                # author_dict = outputs_json.to_dict()
                # for key, value in author_dict.items():
                #     if key == author_username:
                #         author_json = value
                #         break
                #    print("\nAUTHOR JSON: ", author_json)

            except FileNotFoundError:
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
                outputs_df = df
                export_df = df

            except pd.errors.EmptyDataError:
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
                outputs_df = df
                export_df = df

            # ,
            # outputs_df.to_csv("outputs/df.csv", sep="\t")
            #   quoting=csv.QUOTE_NONNUMERIC, index=False)

            if tweet_data["includes"]:
                # loop to go through all referenced/included tweets
                for iter in range(len(included_tweets)):
                    included = included_tweets[iter]
                    included_id = included["id"]
                    included_author_id = included["author_id"]
                    included_pub_metrics = included["public_metrics"]

                    included_likes = included_pub_metrics["like_count"]
                    included_reply_count = included_pub_metrics["reply_count"]
                    included_retweets = included_pub_metrics["retweet_count"]
                    included_quote_count = included_pub_metrics["quote_count"]
                    included_impressions = included_pub_metrics["impression_count"]

                    # print("\nIncluded Tweet ID: ", included_id)
                    # print("\nIncluded/Parent Tweet Author ID: ",
                    #       included_author_id)

                    if included_author_id == author_id:
                        included_author_username = author_username
                        included_user = st.get_username_by_author_id(

                            included_author_id)
                        included_author_name = included_user["data"]["name"]
                        outputs_df = pd.read_csv(
                            "outputs/df.csv", index_col=0)
                        if included_author_username in outputs_df.index:
                            outputs_df.loc[included_author_username,
                                           "Author"] = included_author_name
                            outputs_df.loc[included_author_username,
                                           "Favorites"] = int(included_likes)
                            outputs_df.loc[included_author_username,
                                           "Retweets"] = int(included_retweets)
                            outputs_df.loc["Tweet ID"] = included_id
                            # outputs_df.to_csv("outputs/df.csv", sep="\t")

                    else:
                        try:
                            inclued_name = st.get_username_by_author_id(
                                included_author_id)
                            included_author_username = inclued_name["data"]["username"]
                            outputs_df = pd.read_csv(
                                "outputs/df.csv", index_col=0, on_bad_lines="skip")

                            if included_author_username in outputs_df.index:
                                outputs_df.loc[included_author_username,
                                               "Author"] = included_author_name
                                outputs_df.loc[included_author_username,
                                               "Favorites"] = int(included_likes)
                                outputs_df.loc[included_author_username,
                                               "Retweets"] = int(included_retweets)
                                outputs_df.loc["Tweet ID"] = included_id
                                # outputs_df.to_csv("outputs/df.csv", sep="\t")

                            else:
                                included_author_username = author_username
                                authors_index = [included_author_username]
                                df0 = pd.DataFrame(
                                    index=authors_index, data=author_name, columns=["Author"])
                                df1 = pd.DataFrame(
                                    index=authors_index, data=int(included_likes), columns=["Favorites"])
                                df2 = pd.DataFrame(
                                    index=authors_index, data=int(included_retweets), columns=["Retweets"])
                                df3 = pd.DataFrame(
                                    index=authors_index, data=included_id, columns=["Tweet ID"])
                                df = pd.concat([df0, df1, df2, df3], axis=1)
                            outputs_df = outputs_df.append(df)
                            export_df = df
                        except:
                            print("ERROR ON GET USERNAME BY AUTHOR ID")

                    print("\nAUTHOR OF INCLUDED/PARENT TWEET DIFFERENT FROM AUTHOR")
                    outputs_df.to_csv("outputs/df.csv", sep="\t")

                    print("\nIncluded/Parent Likes: ", included_likes)
                    print("\nIncluded/Parent Replies: ", included_reply_count)
                    print("\nIncluded/Parent Retweets: ", included_retweets)
                    print("\nIncluded/Parent Quotes: ", included_quote_count)
                    print("\nIncluded/Parent Impressions: ",
                          included_impressions)
                    export_df = df

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
                        outputs_df = pd.read_csv(
                            "outputs/df.csv", index_col=0)

                        if engager_author_username in outputs_df.index:
                            try:
                                outputs_df.loc[engager_author_username,
                                               "Author"] = engager_user["name"]
                                outputs_df.loc[engager_author_username,
                                               "Favorites"] = int(included_likes)
                                outputs_df.loc[engager_author_username,
                                               "Retweets"] = int(included_retweets)
                                outputs_df.loc["Tweet ID"] = included_id

                            except:
                                authors_index = [engager_author_username]
                                df0 = pd.DataFrame(
                                    index=authors_index, data=engager_user["name"], columns=["Author"])
                                df1 = pd.DataFrame(
                                    index=authors_index, data=int(included_likes), columns=["Favorites"])
                                df2 = pd.DataFrame(
                                    index=authors_index, data=int(included_retweets), columns=["Retweets"])
                                df3 = pd.DataFrame(
                                    index=authors_index, data=included_id, columns=["Tweet ID"])
                                df = pd.concat([df1, df2, df3], axis=1)

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
                        outputs_df = pd.read_csv(

                            "outputs/df.csv", index_col=0)

                        if engager_author_username in outputs_df.index:
                            try:
                                outputs_df.loc[engager_author_username,
                                               "Author"] = included_author_name
                                outputs_df.loc[engager_author_username,
                                               "Favorites"] = int(included_likes)
                                outputs_df.loc[engager_author_username,
                                               "Retweets"] = int(included_retweets)
                                outputs_df.loc[engager_author_username]["Tweet ID"] = included_id

                                # print("Double call worked: ", s)

                            except:
                                authors_index = [engager_author_username]
                                df0 = pd.DataFrame(
                                    index=authors_index, data=included_author_name, columns=["Author"])
                                df1 = pd.DataFrame(
                                    index=authors_index, data=int(included_likes), columns=["Favorites"])
                                df2 = pd.DataFrame(
                                    index=authors_index, data=int(included_retweets), columns=["Retweets"])
                                df3 = pd.DataFrame(
                                    index=authors_index, data=included_id, columns=["Tweet ID"])
                                df = pd.concat([df1, df2, df3], axis=1)

                outputs_df.to_csv("outputs/df.csv", sep="\t")
                nameString = 'Jimmy_Grow'
                outputs_df = pd.read_csv(
                    "outputs/df.csv", index_col=0)
                # s = outputs_df.loc[nameString]

                export_df = df  # FIX THIS EXPORT DF SO USABLE IN POSTGRES_TOOLS.PY
                print("\nExport DF: ", export_df)
                outputs_df.to_csv("outputs/df.csv", sep="\t")
                # outputs_json.to_json("outputs/df.json", orient="index")


def main():
    rules = st.get_rules()
    delete = st.delete_all_rules(rules)
    set = st.set_rules(delete, update_flag)
    get_stream(update_flag, remove_flag)


if __name__ == "__main__":
    main()
