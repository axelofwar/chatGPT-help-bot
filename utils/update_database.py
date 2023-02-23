import os
import pandas as pd
from dotenv import load_dotenv

import stream_tools as st
import postgres_tools as pg

load_dotenv()

bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
engine = pg.start_db("test")

# test data
included_id = "1626330087913127937"
included_likes = 54
included_retweets = 44
included_reply_count = 27


def main():
    existing_df = pd.read_sql_table("df_table", engine)
    if included_id in existing_df["Tweet ID"].values:
        print(f"Tweet #{included_id} already exists in table")
        print("Updating table...")
        row = existing_df.loc[existing_df["Tweet ID"]
                              == included_id]
        print("Row Vals: ", row.values)
        row = row.values[0]
        favorites = row[1]
        retweets = row[2]
        replies = row[5]
        print("Favorites: ", favorites)
        print("Retweets: ", retweets)
        print("Replies: ", replies)

        # update the values in the existing table
        if str(included_likes) > favorites:
            print(f"Likes updated to {included_likes}")
            existing_df.loc[existing_df["Tweet ID"] == included_id, [
                "Favorites"]] = int(included_likes)
        if included_retweets > retweets:
            print(f"Retweets updated to {included_retweets}")
            existing_df.loc[existing_df["Tweet ID"] == included_id, [
                "Retweets"]] = int(included_retweets)
        if str(included_reply_count) > replies:
            print(f"Replies updated to {included_reply_count}")
            existing_df.loc[existing_df["Tweet ID"] == included_id, [
                "Replies"]] = int(included_reply_count)
        print("DF Table: ", existing_df)

        # rework this to write only the updated values - not rewrite the whole table
        existing_df.to_sql(
            "df_table", engine, if_exists="replace")

    else:
        print("Tweet does not exist in table or metrics up to date")


main()
