from time import sleep
import requests
import pandas as pd


def get_collection_members():
    collection = 'y00ts'
    response = requests.get(
        f"https://www.nftinspect.xyz/api/collections/members/{collection}?limit=7500&onlyNewMembers=false"
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    output = response.json()
    members = output["members"]
    for member in members:
        print("Member :", member)
        print("\n")
    return response.text


def main():
    get_collection_members()


main()
