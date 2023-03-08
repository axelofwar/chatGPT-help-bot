import os
import yaml
import pandas as pd
import postgres_tools as pg
from dotenv import load_dotenv
load_dotenv()

'''
Standalone file to update the db with new tweet data - contains functions for:
    - adding new tweets to the db
    - updating existing tweets in the db

The db is updated by comparing the tweet id of the new tweet to the tweet ids in the db
We are using postgresql for the db and engine is our connection to the 'test' db
For use -> change # test data to the data you want to test against the db
'''

bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
engine = pg.start_db("test")

with open("utils/yamls/config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

table_name = config["metrics_table_name"]

# test data
included_id = "1628657154742792197"
included_likes = 36
included_retweets = 4
included_reply_count = 7


def main():
    existing_df = pd.read_sql_table(table_name, engine)
    indexes = existing_df.index.values
    print("Indexes: ", indexes)
    print("FIRST READ DF: ", existing_df)
    print("Size of Cols: ", len(existing_df.columns))
    print("existing_df.columns: ", existing_df.columns)
    if len(existing_df.columns) > 6:
        existing_df.drop("level_0", axis=1, inplace=True)
        print("Dropped it")
        existing_df.to_sql(table_name, engine, if_exists="replace")
        print("Replaced it")
        print("New columns: ", existing_df.columns)
    if included_id in existing_df["Tweet ID"].values:
        print(f"Tweet #{included_id} already exists in table")
        print("Updating table...")
        row = existing_df.loc[existing_df["Tweet ID"]
                              == included_id]
        print("Row Vals: ", row.values)
        row = row.values[0]
        favorites = row[2]
        retweets = row[3]
        replies = row[4]
        print("Favorites: ", favorites)
        print("Retweets: ", retweets)
        print("Replies: ", replies)

        # update the values in the existing table
        if int(included_likes) > int(favorites):
            print(f"Likes updated to {included_likes}")
            existing_df.loc[existing_df["Tweet ID"] == included_id, [
                "Favorites"]] = int(included_likes)
        if int(included_retweets) > int(retweets):
            print(f"Retweets updated to {included_retweets}")
            existing_df.loc[existing_df["Tweet ID"] == included_id, [
                "Retweets"]] = int(included_retweets)
        if int(included_reply_count) > int(replies):
            print(f"Replies updated to {included_reply_count}")
            existing_df.loc[existing_df["Tweet ID"] == included_id, [
                "Replies"]] = int(included_reply_count)
        print("POST REPLACE: ", existing_df)

        # rework this to write only the updated values - not rewrite the whole table
        existing_df.to_sql(
            table_name, engine, if_exists="replace", index=False)
        existing_df = pd.read_sql_table(table_name, engine)
        print("POST WRITE:", existing_df)

    else:
        print("Tweet does not exist in table or metrics up to date")


main()
