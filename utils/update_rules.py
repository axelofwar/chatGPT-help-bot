import filtered_stream as fs
import yaml

with open("utils/yamls/rules.yml", "r") as file:
    axel_rules = yaml.load(file, Loader=yaml.FullLoader)


def main():
    fs.update_rules()
    return


main()
