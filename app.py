import os
import requests
import json
from flannagans import determine_response

from flask import Flask, request

app = Flask(__name__)

"""
TODO (in no specific order of importance): 
1. find a way to use fewer environment variables cause it takes forever to setup
    1-1. I think maybe just 1 env variable per team? team-id,division-uid,group-id,etc...
    1-2. Or maybe just the entire team_info map? So if someone else uses this bot they can fill in what they need
2. add functionality to display the records of the team we're playing against
"""

# team_info is a map of maps containing information for each of the volleyball teams.
# The keys for the outside map are the ids for the GroupMe groups.
team_info = {
    os.getenv("GROUP_ID_APITEST0"): {  # apitest0 group, mirrors sunday info
        "team_name": os.getenv("SUNDAY_TEAM_NAME"),
        "division_uid": os.getenv("SUNDAY_DIVISION_UID"),
        "bot_id": os.getenv("GROUPME_BOT_ID_API_TEST_0"),
        "team_id": os.getenv("SUNDAY_TEAM_ID")
    },
    os.getenv("GROUP_ID_APITEST1"): {  # apitest group, mirrors monday info
        "team_name": os.getenv("MONDAY_TEAM_NAME"),
        "division_uid": os.getenv("MONDAY_DIVISION_UID"),
        "bot_id": os.getenv("GROUPME_BOT_ID_API_TEST_1"),
        "team_id": os.getenv("MONDAY_TEAM_ID"),
    },
    os.getenv("GROUP_ID_APITEST2"): {  # apitest2 group, mirrors tuesday info
        "team_name": os.getenv("TUESDAY_TEAM_NAME"),
        "division_uid": os.getenv("TUESDAY_DIVISION_UID"),
        "bot_id": os.getenv("GROUPME_BOT_ID_API_TEST_2"),
        "team_id": os.getenv("TUESDAY_TEAM_ID")
    },
    os.getenv("GROUP_ID_APITEST3"): {  # apitest3 group, mirrors wednesday info
        "team_name": os.getenv("WEDNESDAY_TEAM_ID"),
        "division_uid": os.getenv("WEDNESDAY_TEAM_ID"),
        "bot_id": os.getenv("GROUPME_BOT_ID_API_TEST_3"),
        "team_id": os.getenv("WEDNESDAY_TEAM_ID")
    },
    os.getenv("GROUP_ID_VOLLEYBOTS"): {  # volleybots, monday
        "team_name": os.getenv("MONDAY_TEAM_NAME"),
        "division_uid": os.getenv("MONDAY_DIVISION_UID"),
        "bot_id": os.getenv("GROUPME_BOT_ID_VOLLEYBOTS"),
        "team_id": os.getenv("MONDAY_TEAM_ID"),
    },
    os.getenv("GROUP_ID_DOLLAR_STORE_ATHLETES"): {  # dollar store athletes, tuesday
        "team_name": os.getenv("TUESDAY_TEAM_NAME"),
        "division_uid": os.getenv("TUESDAY_DIVISION_UID"),
        "bot_id": os.getenv("GROUPME_BOT_ID_DOLLAR_STORE_ATHLETES"),
        "team_id": os.getenv("TUESDAY_TEAM_ID"),
    },
    # Need to add sunday and wednesday if they ever get a groupme going
}

def send_message(msg, bot_id):
    url = "https://api.groupme.com/v3/bots/post"
    data = {
        "bot_id": bot_id,
        "text": msg
    }
    requests.post(url, data=json.dumps(data))


def should_reply(data):
    if len(data["text"]) < 8:  # the length of "hey milo"
        return False
    message_start = data["text"][:8].lower()
    if data["name"] != "Milo" and message_start == "hey milo":
        return True
    else:
        return False

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()

    # Avoid milo bot replying to milo bot by accident
    if should_reply(data):
        division_uid = team_info[data["group_id"]]["division_uid"]
        bot_id = team_info[data["group_id"]]["bot_id"]
        team_name = team_info[data["group_id"]]["team_name"]
        team_id = team_info[data["group_id"]]["team_id"]
        response = determine_response(data["text"].lower().strip(), team_name, division_uid, team_id)
        send_message(response, bot_id)

    return "OK", 200
