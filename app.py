import os
import json
import requests
from datetime import datetime

from flask import Flask, request

app = Flask(__name__)


game_times = [
    datetime(2022, 6, 7, 21, 15, 0),
    datetime(2022, 6, 14, 21, 15, 0),
]

def find_next_game(today, game_times):
    next_game = datetime(9999, 9, 9)
    for game in game_times:
        if game > today:
            if game - today < next_game - today:
                next_game = game
    return next_game

def send_message(msg):
	url  = "https://api.groupme.com/v3/bots/post"
	data = {
		"bot_id": os.getenv('GROUPME_BOT_ID'),
		"text": msg
	}
	resp = requests.post(url, data=json.dumps(data))

def should_reply(data):
	if len(data["text"]) < 8:
		return False
	message_start = data["text"][:8]
	if data["name"] != "Milo" and message_start == "hey milo":
		return True
	else:
		return False

# This should be short since we only got 2 games left lol
def determine_response(message):
	next_game_responses = [
		"hey milo when's the next game",
		"hey milo when's our next game",
		"hey milo whens the next game",
		"hey milo whens our next game",
		"hey milo when is the next game",
		"hey milo next game"
	]

	if message in next_game_responses:
		return find_next_game(datetime.now(), game_times).strftime("The next game is on %B %dth at %I:%M %p")


@app.route('/', methods=['POST'])
def webhook():
  
	data = request.get_json()

	# We don't want to reply to ourselves!
	if should_reply(data):
		response = determine_response(data["text"].lower())
		send_message(response)

	return "OK", 200

