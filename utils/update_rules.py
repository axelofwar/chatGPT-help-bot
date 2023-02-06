import stream_tools as st
import yaml

with open("utils/yamls/rules.yml", "r") as file:
    axel_rules = yaml.load(file, Loader=yaml.FullLoader)


def main():
    st.update_rules()
    return


main()
