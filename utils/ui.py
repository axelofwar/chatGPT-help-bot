import tkinter as tk
import yaml
import twitter_tools as th
import requests
import asyncio
import json
'''
UI for user to input channel ID and history days - this contains functions for:
    - making the window
    - updating the history days
    - updating the channel ID
    - canceling the UI
    - running the UI
    
This interacts with the config file for the channel ID and history days in default cases
'''
with open("utils/yamls/config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


class gpt_UI:
    file = open("utils/yamls/config.yml", "r+")
    config = yaml.load(file, Loader=yaml.FullLoader)

    def __init__(self):
        self.history_days = 30
        self.channel_id = ""
        self.cancelFlag = False

    def make_window(self):
        self.window = tk.Tk()

        # resize and center UI window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = 200
        height = 200

        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)

        self.window.geometry("%dx%d+%d+%d" % (width, height, x, y))

        label = tk.Label(self.window, text="History (Days):")
        history_slider = tk.Scale(self.window,
                                  from_=0,
                                  to=30,
                                  orient=tk.HORIZONTAL,
                                  resolution=1,
                                  command=self.update_history_days)
        label.pack()
        history_slider.pack()

        label = tk.Label(self.window, text="Channel ID:")
        label.pack()
        self.channel_id = tk.Entry(self.window)
        self.channel_id.pack()

        submit_button = tk.Button(
            self.window, text="Submit", command=self.submit)
        submit_button.pack()

        cancel_button = tk.Button(
            self.window, text="Cancel", command=self.cancel)
        cancel_button.pack()

        stop_button = tk.Button(self.window, text="Stop", command=self.stop)
        stop_button.pack()

    def update_history_days(self, value):
        self.history_days = float(value)

    def submit(self):
        if self.channel_id.get() == "":
            self.channel_id = self.config["data_channel_id"]
            # TODO: add error message instead of defaulting to config
        else:
            self.channel_id = self.channel_id.get()

        self.config["UI_CHANNEL_ID"] = self.channel_id

        print("CONFIG UPDATED")
        self.close_window()
        # print("WINDOW DESTROYED")
        return "SUBMITTED"

    def cancel(self):
        self.close_window()
        print("CANCELLED")
        self.cancelFlag = True
        return "CANCELLED"

    def stop(self):
        th.running = False
        self.close_window()
        th.closeListener()
        print("STOPPED")
        self.cancelFlag = True
        return self.window.destroy()

    def get_result(self):
        return self.channel_id, self.history_days, self.cancelFlag

    def close_window(self):
        self.window.destroy()


class leaderboard_UI:
    def __init__(self):
        self.database_api = config["DATABASE_API"]

    def make_window(self):
        self.window = tk.Tk()

        self.data = self.get_data()

        self.text = tk.Text(self.window, height=10, width=50)
        self.text.pack(fill="both", expand=True)

        formatted_data = json.dumps(self.data, indent=4)
        self.text.insert("1.0", formatted_data)

        self.window.title("Leaderboard")
        self.window.configure(background="white")

        headers = ["Index", "Name", "Favorites",
                   "Retweets", "Replies", "Impressions"]

        # table = tk.Frame(self.window)
        # table.pack(padx=10, pady=10)

        # for i, header in enumerate(headers):
        #     header_label = tk.Label(table, text=header, font=(
        #         "Arial", 12, "bold"), padx=10, pady=5)
        #     header_label.grid(row=0, column=i)
        #     print("Header: " + header)

        # for i, row in enumerate(self.data):
        #     index_label = tk.Label(table, text=row["index"], font=(
        #         "Arial", 12), padx=10, pady=5)
        #     index_label.grid(row=i+1, column=0)
        #     name_label = tk.Label(table, text=row["Name"], font=(
        #         "Arial", 12), padx=10, pady=5)
        #     name_label.grid(row=i+1, column=1)
        #     favorites_label = tk.Label(
        #         table, text=row["Favorites"], font=("Arial", 12), padx=10, pady=5)
        #     favorites_label.grid(row=i+1, column=2)
        #     retweets_label = tk.Label(
        #         table, text=row["Retweets"], font=("Arial", 12), padx=10, pady=5)
        #     retweets_label.grid(row=i+1, column=3)
        #     replies_label = tk.Label(
        #         table, text=row["Replies"], font=("Arial", 12), padx=10, pady=5)
        #     replies_label.grid(row=i+1, column=4)
        #     impressions_label = tk.Label(
        #         table, text=row["Impressions"], font=("Arial", 12), padx=10, pady=5)
        #     impressions_label.grid(row=i+1, column=5)

        stop_button = tk.Button(
            self.window, text="Stop", command=self.stop)
        stop_button.grid(row=1, column=0)
        stop_button.pack()

    def get_data(self):
        response = requests.get(self.database_api)
        data = response.json()
        return data

    def close_window(self):
        self.window.destroy()
        return "Destroyed"

    def stop(self):
        self.close_window()
        print("STOPPED")

        # resize and center UI window
        # screen_width = self.window.winfo_screenwidth()
        # screen_height = self.window.winfo_screenheight()
        # width = 200
        # height = 200

        # x = (screen_width / 2) - (width / 2)
        # y = (screen_height / 2) - (height / 2)

        # self.window.geometry("%dx%d+%d+%d" % (width, height, x, y))


# async def main():
def main():
    # ui = gpt_UI()
    ui = leaderboard_UI()
    ui.make_window()
    ui.window.mainloop()
    # channel_id, history, cancelFlag = ui.get_result()
    # return channel_id, history, cancelFlag
    return "DONE"


# asyncio.run(main())
main()
