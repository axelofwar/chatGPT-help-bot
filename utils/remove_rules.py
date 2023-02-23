import stream_tools as st
import yaml

'''
Standalone file to remove rules from the rules.yml file
Then run update_rules.py to update the rules on the Twitter API
Then reset the REMOVE_RULE in the config.yml file to ""
'''

with open("utils/yamls/rules.yml", "r") as file:
    axel_rules = yaml.load(file, Loader=yaml.FullLoader)


def main():
    st.remove_rules(axel_rules)
    return


main()
