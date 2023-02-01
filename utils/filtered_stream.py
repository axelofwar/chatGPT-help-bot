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
        # axel_rules = file.read()

    # [{"value": ["ADD_RULE"], "tag": "config-rule"}, ]

    print("RULES SAVED TO rules.yml")
    print("UPDATE VALUE IN SET: ", update_flag)
    if update_flag:
        axel_rules = axel_rules + \
            [{"value": config["ADD_RULE"], "tag": config["ADD_TAG"]}, ]
        with open("utils/yamls/rules.yml", "w") as file:
            file.write(str(axel_rules))

        print("RULE VALUE UPDATED:\n", update_flag)
        print(("ADDED RULES USED:\n", axel_rules))

    # with open("utils/rules.txt", "w") as file:
    #     file.write(str(axel_rules))
    #     print("RULES SAVED TO FILE")

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


# TODO: fix remove rule functionality
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
            print("GOT RESPONSE")
            if update_flag:
                print("UPDATING RULES")
                update_rules()
                update_flag = False
            if remove_flag:
                print("REMOVING RULES")
                remove_rules(get_rules())
                remove_flag = False

            json_response = json.loads(response_line)
            print(json.dumps(json_response, indent=4, sort_keys=True))


def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete, update_flag)
    get_stream(set, update_flag, remove_flag)


if __name__ == "__main__":
    main()
