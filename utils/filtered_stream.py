import requests
import os
import json
from dotenv import load_dotenv
import yaml
load_dotenv()

bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
update_flag = False
remove_flag = False


with open("utils/yamls/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
# To set your enviornment variables in your terminal run the following line:


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r


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
        with open("utils/config.yml", "w") as file:
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


def get_likes_retweets_impressions(tweet_id):
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


def get_stream(update_flag, remove_flag):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream", auth=bearer_oauth, stream=True,
    )
    print(response.status_code)
    if response.status_code != 200:
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
                update_rules()
                update_flag = False
            if remove_flag:
                print("REMOVING RULES")
                remove_rules(get_rules())
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
            tweet_data = get_data_by_id(id)

            # print raw data dump
            # print("\nDATA BY ID: ", json.dumps(
            #     tweet_data, indent=4, sort_keys=True))
            # print("\nPublic Metrics: ", tweet_data["data"]["public_metrics"])

            if "author_id" in tweet_data["data"]:
                author_id = tweet_data["data"]["author_id"]
                author = get_username_by_author_id(
                    tweet_data["data"]["author_id"])
                author_username = author["data"]["username"]
                author_name = author["data"]["name"]
                print("\nAuthor ID: ", author_id)
                print("\nAuthor Name: ", author_name)
                print("\nAuthor Username: ", author_username)
            else:
                print("Author ID not found")

            # improve wait/sleep to make sure rules GET call has returned json respones
            # once this is done, remove the nested if checks

            if "referenced_tweets" in tweet_data["data"]:
                if tweet_data["data"]["referenced_tweets"]:
                    referenced = tweet_data["data"]["referenced_tweets"]
                print("\nReferenced Tweets: ", referenced)

            if "tweets" in tweet_data["includes"]:
                if tweet_data["includes"]["tweets"]:
                    included_tweets = tweet_data["includes"]["tweets"]
                    included_users = tweet_data["includes"]["users"]

            engagement_metrics = get_likes_retweets_impressions(id)
            print("\nTweet Favorites: ", engagement_metrics["favorite_count"])
            print("\nTweet Retweets: ", engagement_metrics["retweet_count"])

            # print raw data dump
            # print("\nIncludes: ", json.dumps(
            #     included_tweets, indent=4, sort_keys=True))
            # print("\nIncludes Users: ", json.dumps(
            #     included_users, indent=4, sort_keys=True))

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

                    print("\nIncluded Tweet ID: ", included_id)
                    print("\nIncluded/Parent Tweet Author ID: ",
                          included_author_id)

                    # try:
                    #     inclued_name = get_username_by_author_id(
                    #         included_author_id)
                    #     included_author_name = inclued_name["data"]["name"]
                    #     included_author_username = inclued_name["data"]["username"]
                    #     print("\nIncluded/Parent Tweet Author Name: ",
                    #           included_author_name)
                    #     print("\nIncluded/Parent Tweet Author Username: ",
                    #           included_author_username)
                    # except:
                    #     print("ERROR ON GET USERNAME BY AUTHOR ID")

                    if included_author_id == author_id:
                        print(
                            "AUTHOR OF INCLUDED/PARENT TWEET MATCHES ORIGINAL AUTHOR")
                        # try:
                        #     included_author_name = get_username_by_author_id(
                        #         included_author_name)
                        #     print("\nMatching Tweet Author Name: ",
                        #           included_author_name)
                        # except:
                        #     print("ERROR ON GET USERNAME BY AUTHOR ID")

                    # comment becuase we are printing the members below
                    # print("\nIncluded Tweet Public Metrics: ",
                    #       included_pub_metrics)

                    print("\nIncluded/Parent Likes: ", included_likes)
                    print("\nIncluded/Parent Replies: ", included_reply_count)
                    print("\nIncluded/Parent Retweets: ", included_retweets)
                    print("\nIncluded/Parent Quotes: ", included_quote_count)
                    print("\nIncluded/Parent Impressions: ",
                          included_impressions)

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
                        name = engager_user["name"]
                        username = engager_user["username"]
                        print("\nMatching Mentioned Author Name: ", name)
                        print(
                            "\nMatching Mentioned Author Username: ", username)
                    if engager_id == included_author_id:
                        print("\nTweet's Mentioned UserID: ", engager_id,
                              "matches included/parent author ID: ", included_author_id)
                        engager_name = engager_user["name"]
                        engager_username = engager_user["username"]
                        print("\nMatching Included/Parent Author Name: ",
                              engager_name)
                        print(
                            "\nMatching Included/Parent Author Username: ", engager_username)

                # TODO: add logic to compare metrics for author and included/parent author
                # aggregate stats for participating author + stats for included/parent author
                # compare to current dataabase and push changes? or overwrite?


def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete, update_flag)
    get_stream(update_flag, remove_flag)


if __name__ == "__main__":
    main()
