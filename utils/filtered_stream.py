import requests
import os
import json
from dotenv import load_dotenv
import yaml
load_dotenv()

bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
update_flag = False
remove_flag = False  # TODO: fix remove rule functionality


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
    # You can adjust the rules if needed
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
        # update_flag = False

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
    return response.json()  # ["username"]


def get_stream(set, update_flag, remove_flag):
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
            print("\nGOT RESPONSE!")
            if update_flag:
                print("UPDATING RULES")
                update_rules()
                update_flag = False
            if remove_flag:
                print("REMOVING RULES")
                remove_rules(get_rules())
                remove_flag = False

            json_response = json.loads(response_line)
            # print(json.dumps(json_response, indent=4, sort_keys=True))
            # data_response = json_response["data"]["text"]
            id = json_response["data"]["id"]
            matching_rules = json_response["matching_rules"]
            full_text = json_response["data"]["text"]
            print("\nMATCHING RULES: ", matching_rules)
            print("\nFULL TEXT: ", full_text)

            # TODO: if original tweet or quoted/retweeted
            # aggregate (x/y)*engagement to original author
            # aggregate (x/x)*engagement to quote/retweeter

            print("\nTweet ID: ", id)
            tweet_data = get_data_by_id(id)

            # print("\nDATA BY ID: ", json.dumps(
            #     tweet_data, indent=4, sort_keys=True))

            print("\nAuthor ID: ", tweet_data["data"]["author_id"])
            author = get_username_by_author_id(tweet_data["data"]["author_id"])
            print("\nAuthor: ", author)
            print("\nPublic Metrics: ", tweet_data["data"]["public_metrics"])

            referenced = tweet_data["data"]["referenced_tweets"]
            print("\nReferenced Tweets: ", referenced)
            included_tweets = tweet_data["includes"]["tweets"]
            included_users = tweet_data["includes"]["users"]

            engagement_metrics = get_likes_retweets_impressions(id)
            print("\nFavorites: ", engagement_metrics["favorite_count"])
            print("\nRetweets: ", engagement_metrics["retweet_count"])

            # print("\nIncludes: ", json.dumps(
            #     included_tweets, indent=4, sort_keys=True))
            # print("\nIncludes Users: ", json.dumps(
            #     included_users, indent=4, sort_keys=True))

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
                print("\nIncluded Tweet Author ID: ", included_author_id)
                print("\nIncluded Tweet Public Metrics: ", included_pub_metrics)

                print("\nIncluded Tweet Likes: ", included_likes)
                print("\nIncluded Tweet Reply Count: ", included_reply_count)
                print("\nIncluded Tweet Retweets: ", included_retweets)
                print("\nIncluded Tweet Quote Count: ", included_quote_count)
                print("\nIncluded Tweet Impressions: ", included_impressions)

            for iter in range(len(included_users)):
                included1 = included_users[iter]
                included1_id = included1["id"]
                print("\nTweet's Included UserID #", iter, ": ",  included1_id)


def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete, update_flag)
    get_stream(set, update_flag, remove_flag)


if __name__ == "__main__":
    main()
