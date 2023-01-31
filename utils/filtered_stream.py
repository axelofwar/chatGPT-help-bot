import requests
import os
import json
from dotenv import load_dotenv
import yaml
load_dotenv()

with open("utils/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
# To set your enviornment variables in your terminal run the following line:

global update_rule
update_rule = False
bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")


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


def set_rules(delete, update_rule):
    # You can adjust the rules if needed
    axel_rules = [
        {"value": "@"+config["account_to_query"], "tag": "accounts"},
        {"value": "@y00tsNFT", "tag": "accounts"},
    ]
    print("UPDATE VALUE IN SET: ", update_rule)
    if update_rule:
        axel_rules = axel_rules + \
            [{"value": config["ADD_RULE"], "tag": "config-rule"}, ]
        print("RULE VALUE UPDATED: ", update_rule)
        print(("ADDED RULES USED: ", axel_rules))
    else:
        axel_rules = [
            {"value": "@"+config["account_to_query"], "tag": "accounts"},
            {"value": "@y00tsNFT", "tag": "accounts"},
        ]
        print("DEFAULT RULES USED: ", axel_rules)

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
    with open("utils/config.yml", "r") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    if "ADD_RULE" in config:
        rule = config["ADD_RULE"]
        update_rule = True
        print("UPDATED TO TRUE: ", update_rule)
    else:
        print("No rule to add")

    if rule == "":
        update_rule = False
        print("UPDATED TO FALSE: ", update_rule)
    else:
        print("SETTING NEW RULES")
        delete = delete_all_rules(get_rules())
        set_rules(delete, update_rule)
        # update_rule = False

    with open("utils/config.yml", "w") as file:
        config["ADD_RULE"] = ""
        yaml.dump(config, file)
        print("RULE RESET TO EMPTY")


def get_stream(set, update_rule):
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
            print("GOT RESPONSE")
            if update_rule:
                print("UPDATING RULES")
                update_rules(config["ADD_RULE"])
                update_rule = False

            json_response = json.loads(response_line)
            print(json.dumps(json_response, indent=4, sort_keys=True))


def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete, update_rule)
    get_stream(set, update_rule)


if __name__ == "__main__":
    main()
