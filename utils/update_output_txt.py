from utils import twitter_tools as th


# PRINT GPT RESPONSE TO FILE
async def update_output_file(response):
    # TODO: modify to use r+ for read/write and make one open call
    with open("outputs/output.txt", "r") as outputFile:
        lines = outputFile.readlines()
        outputFile.close()

    with open("outputs/output.txt", "w") as outputFile:
        found_response = False
        for line in lines:
            if "RESPONSE: " in line:
                if not found_response:
                    outputFile.write(
                        "RESPONSE: " + response.choices[0].text + "\n")
                    found_response = True
            else:
                outputFile.write(line)
        if not found_response:
            outputFile.write("RESPONSE: " + response.choices[0].text + "\n")
    outputFile.close()
    th.running = False
    return th.running
