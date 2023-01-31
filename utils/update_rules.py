import filtered_stream as fs
import asyncio
import yaml

# with open("utils/config.yml", "r") as file:
#     config = yaml.load(file, Loader=yaml.FullLoader)


def main():
    fs.update_rules()
    return


main()
