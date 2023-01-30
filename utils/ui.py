import tkinter as tk
import yaml

from utils import twitter_tools as th


class UI:
    file = open("utils/config.yml", "r+")
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

        self.config["DISCORD_CHANNEL_ID"] = self.channel_id

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


async def main():
    ui = UI()
    ui.make_window()
    ui.window.mainloop()
    channel_id, history, cancelFlag = ui.get_result()
    return channel_id, history, cancelFlag
