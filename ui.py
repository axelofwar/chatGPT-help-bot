import tkinter as tk
import yaml


class UI:
    file = open("config.yml", "r+")
    # config = yaml.safe_load(file)
    # config = yaml.load(file)
    config = yaml.load(file, Loader=yaml.FullLoader)

    def __init__(self):
        self.history_days = 30
        self.channel_id = ""

    def make_window(self):
        self.window = tk.Tk()

        # resize and center UI window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = 200
        height = 150

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

    def update_history_days(self, value):
        self.history_days = float(value)

    def submit(self):
        if self.channel_id.get() == "":
            self.channel_id = self.config["discord_channel_id"]
            # TODO: add error message instead of defaulting to config
        else:
            self.channel_id = self.channel_id.get()

        self.config["DISCORD_CHANNEL_ID"] = self.channel_id
        with open("config.yml", "w") as file:
            yaml.dump(self.config, file)
        print("CONFIG UPDATED")
        self.close_window()
        print("WINDOW DESTROYED")

    def get_result(self):
        return self.channel_id, self.history_days

    def close_window(self):
        self.window.destroy()


async def main():
    ui = UI()
    ui.make_window()
    ui.window.mainloop()
    channel_id, history = ui.get_result()
    return channel_id, history
