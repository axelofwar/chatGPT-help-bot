import os
import openai
import asyncio
import tkinter as tk

#openai.api_key = os.getenv("OPENAI_API_KEY") #if using python .env file
openai.api_key = os.environ['OPEN_API_KEY']  #if using replit Secrets function
openai.api_endpoint = "https://api.openai.com/v1"

def update_temp(value):
  temper = float(value)
  global temp
  temp = temper


def update_max_tokens(value):
  max_token_count = float(value)
  global max_token
  max_token = int(max_token_count)


def submit():
  window.destroy()

window = tk.Tk()

screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

width = 300  #window.winfo_width()
height = 200  #window.winfo_height()

x = (screen_width / 2) - (width / 2)
y = (screen_height / 2) - (height / 2)

window.geometry("%dx%d+%d+%d" % (width, height, x, y))

label = tk.Label(window, text="Temperature Slider")
temp_slider = tk.Scale(window,
                       from_=0,
                       to=2,
                       orient=tk.HORIZONTAL,
                       resolution=0.1,
                       command=update_temp)
label.pack()
temp_slider.pack()

label = tk.Label(window, text="Max Tokens Slider")
max_token_slider = tk.Scale(window,
                            from_=0,
                            to=150,
                            orient=tk.HORIZONTAL,
                            resolution=0.1,
                            command=update_max_tokens)
label.pack()
max_token_slider.pack()

submit_button = tk.Button(window, text="Submit", command=submit)
submit_button.pack()

#function for ChatGPT call
async def ChatGPTCall(mPrompt, mModel, mTemp, mTokens):
  response = openai.Completion.create(
    model=mModel,
    prompt=mPrompt,
    #amount of uniqueness for each response params below
    temperature=mTemp,
    max_tokens=mTokens,  #bounds on the response token - TODO: clamp user input
    top_p=1,
    frequency_penalty=0.0,
    presence_penalty=0.6,
    stop=[" Human:", " AI:"])
  return response

#function for doing main chatGPT logic
async def main():
  if 'temp' != globals() and 'max_token' != globals():
    temp = 0.9
    max_token = 100

  print("TEMP: ", temp)
  print("MAX TOKENS: ", max_token)
  HelloWorld = await ChatGPTCall(
    "Hey, hope you're well today. Teach me something new about python or react!", temp, max_token)

  print(HelloWorld.choices[0].text)

  filename = 'output.txt'

  if os.path.exists(filename):
    outputFile = open(filename, mode='r+')
  else:
    outputFile = open(filename, 'x')

  #Here we store all the response data in an output file instead of just returning the text member
  print(HelloWorld.choices[0].text, file=outputFile)
  outputFile.close()


window.mainloop()
asyncio.run(main())

'''
#OpenAI Example Query using Flask App
from flask import Flask, redirect, render_template, request, url_for
app = Flask(__name__)
@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        animal = request.form["animal"]
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_prompt(animal),
            temperature=0.6,
        )
        return redirect(url_for("index", result=response.choices[0].text))

    result = request.args.get("result")
    return render_template("index.html", result=result)


def generate_prompt(animal):
    return """Suggest three names for an animal that is a superhero.

Animal: Cat
Names: Captain Sharpclaw, Agent Fluffball, The Incredible Feline
Animal: Dog
Names: Ruff the Protector, Wonder Canine, Sir Barks-a-Lot
Animal: {}
Names:""".format(
        animal.capitalize()
    )
'''
