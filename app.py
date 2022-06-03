import os
import json
import logging

import requests, urllib
from flask import Flask, request

app = Flask(__name__)

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


@app.route('/', methods=['POST'])
def webhook():
  
	data = request.get_json()

	# We don't want to reply to ourselves!
		if should_reply(data):
			msg = data["name"]
			send_message(msg)

	return "OK", 200

