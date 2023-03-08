from utils import nft_inspect_tools as nft
import pandas as pd
import os
import requests
import yaml

with open("utils/yamls/config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


def get_db_data():
    response = requests.get(config["DATABASE_API"])
    data = response.json()
    return data


def test_function():
    pfp_table_data = get_db_data()
    test_members = nft.get_simple_members("y00ts")
    '''
    Test with nft inspect api for git action because it
    requires no keys or authorization
    '''

    for member in test_members:
        member_name = member["name"]
        member_wearing_pfp = member["isWearingCollectionsPfp"]
        member_pfp_url = member["pfpUrl"]
        member_global_reach = member["globalReach"]
        member_rank = member["rank"]
        member_time_with_token = member["timeWithToken"]
        member_time_with_collection = member["timeWithCollection"]

        member_data_frame = pd.DataFrame(
            {
                "Name": [member_name],
                "Wearing PFP": [member_wearing_pfp],
                "PFP URL": [member_pfp_url],
                "Global Reach": [member_global_reach],
                "Rank": [member_rank],
                "Time With Token": [member_time_with_token],
                "Time With Collection": [member_time_with_collection],
            }
        )
        # print("Member Data Frame: ", member_data_frame)

    for item in pfp_table_data:
        print("PFP Table Item: ", item)


if 'GITHUB_ACTION' in os.environ:
    test_function()
