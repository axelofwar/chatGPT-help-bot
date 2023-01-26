import tkinter as tk
import asyncio


class UI:

    def __init__(self):
        self.history_days = 30
        self.channel_id = ""

    def make_window(self):
        self.window = tk.Tk()
        print("WINDOW CREATED")

        # resize and center UI window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = 200
        height = 150

        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)

        self.window.geometry("%dx%d+%d+%d" % (width, height, x, y))

        print("WINDOW POSITIONED")
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

        print("SUBMIT BUTTON MADE")
        submit_button = tk.Button(
            self.window, text="Submit", command=self.submit)
        submit_button.pack()

    def update_history_days(self, value):
        self.history_days = float(value)

    def submit(self):
        if self.channel_id.get() == "":
            self.channel_id = None
        else:
            self.channel_id = self.channel_id.get()
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
