import stream_tools as st
import yaml

with open("utils/yamls/rules.yml", "r") as file:
    axel_rules = yaml.load(file, Loader=yaml.FullLoader)


# Standalone file to add rules from the rules.yml file
# Then run update_rules.py to update the rules on the Twitter API
# Then reset the ADD_RULE in the config.yml file to ""

def main():
    st.update_rules()
    return


main()
