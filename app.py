import os
import json
import requests
from datetime import datetime, timedelta

from flask import Flask, request

app = Flask(__name__)

# Triggering a rebuild count: 1

team_info = {
    os.getenv("GROUP_ID_APITEST") : { # apitest group, mirrors volleybots info
        "team_name" : os.getenv("MONDAY_TEAM_NAME"),
        "division_uid" : os.getenv("MONDAY_DIVISION_UID"),
        "bot_id" : os.getenv("GROUPME_BOT_ID_API_TEST"),
    },
    os.getenv("GROUP_ID_APITEST2") : { # apitest2 group, mirrors dollar store athletes info
        "team_name" : os.getenv("TUESDAY_TEAM_NAME"),
        "division_uid" : os.getenv("TUESDAY_DIVISION_UID"),
        "bot_id" : os.getenv("GROUPME_BOT_ID_API_TEST_2")
    },
    os.getenv("GROUP_ID_VOLLEYBOTS") : { # volleybots, monday
        "team_name": os.getenv("MONDAY_TEAM_NAME"),
        "division_uid": os.getenv("MONDAY_DIVISION_UID"),
        "bot_id": os.getenv("GROUPME_BOT_ID_VOLLEYBOTS"),
        "team_id": os.getenv("MONDAY_TEAM_ID")
    },
    os.getenv("GROUP_ID_DOLLAR_STORE_ATHLETES") : { # dollar store athletes, tuesday
        "team_name": os.getenv("TUESDAY_TEAM_NAME"),
        "division_uid": os.getenv("TUESDAY_DIVISION_UID"),
        "bot_id": os.getenv("GROUPME_BOT_ID_DOLLAR_STORE_ATHLETES"),
        "team_id": os.getenv("TUESDAY_TEAM_ID")
    },
    # Need to add sunday and wednesday if they ever get a groupme going
}

def get_current_season():
    url = "https://flan1-lms-pub-api.league.ninja/nav/seasons/"
    today = datetime.now()
    current_season = "There's either no active season right now or something went wrong with the code, who knows?"
    r = requests.get(url)
    for item in r.json()["Data"]:
        dt_start_string = item["startDate"].replace("T", " ")
        dt_end_string = item["endDate"].replace("T", " ")
        dt_format = "%Y-%m-%d %H:%M:%S"
        dt_start_object = datetime.strptime(dt_start_string, dt_format)
        dt_end_object = datetime.strptime(dt_end_string, dt_format)
        if dt_start_object < today < dt_end_object:
            current_season = f"The current season is {item['name']} and it ends on {dt_end_string}"
    return current_season


def get_next_season():
    url = "https://flan1-lms-pub-api.league.ninja/nav/seasons/"
    today = datetime.now()
    next_season = "There's either no next season date or something went wrong with the code, who knows?"
    r = requests.get(url)
    for item in r.json()["Data"]:
        dt_start_string = item["startDate"].replace("T", " ")
        dt_end_string = item["endDate"].replace("T", " ")
        dt_format = "%Y-%m-%d %H:%M:%S"
        dt_start_object = datetime.strptime(dt_start_string, dt_format)
        dt_end_object = datetime.strptime(dt_end_string, dt_format)
        if today < dt_end_object and today < dt_start_object:
            next_season = f"The next season is {item['name']} and it starts on {dt_start_string}"
            break  # if there's more than 2 seasons, skips checking by just stopping after the first "next season"
    return next_season


def get_matches(team_name, division_uid):
    url = f"https://flan1-lms-pub-api.league.ninja/divisions/{division_uid}/schedule/"
    r = requests.get(url)
    matches = []
    for item in r.json()["Data"]:
        if item["homeTeam"] and item["awayTeam"]:  # lazy null check
            if item["homeTeam"]["name"] == team_name or item["awayTeam"]["name"] == team_name:
                dt_format = "%Y-%m-%d %H:%M:%S"
                matches.append(datetime.strptime(item["matchStart"].replace("T", " "), dt_format) - timedelta(hours=4)) # Matches are 4 hours ahead for whatever reason
    return matches


def check_upcoming_matches(team_id): # just a different way to check upcoming matches
    url = f"https://flan1-lms-pub-api.league.ninja/teams/{team_id}"
    r = requests.get(url)
    next_game = datetime(9999, 9, 9)
    try:
        game_check = r.json()["Data"]["upcomingMatches"][0]["matchStart"]
        dt_format = "%Y-%m-%d %H:%M:%S"
        next_game = datetime.strptime(game_check.replace("T", " "), dt_format) - timedelta(hours=4)
    except:
        next_game = datetime(9999, 9, 9) # yeah, it's redundant, I just don't know if this can be empty
    return next_game





def get_next_match(matches):
    today = datetime.now()
    next_game = datetime(9999, 9, 9)
    for game in matches:
        if game > today:
            if game - today < next_game - today:
                next_game = game
    return next_game


def get_standings(team_name, division_uid):
    url = f"https://flan1-lms-pub-api.league.ninja/divisions/{division_uid}/standings/"
    r = requests.get(url)
    standing = "bugging out, not sure"
    for item in r.json()["Data"]:
        if item["teamName"] == team_name:
            standing = f"Our team is ranked {item['ranking']}"
    return standing


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


def add_question_mark(question_array):
    temp_array = []
    for question in question_array:
        temp_array.append(question + "?")
    final_array = question_array + temp_array
    return final_array


def get_command_questions(questions_map):
    reply = "I know the following commands: \n"
    for question in questions_map:
        reply = reply + questions_map[question][0] + "\n"
    return reply


def get_all_command_questions(questions_map):
    reply = "Get ready for a wall of text, here's all the commands I know: \n"
    for question in questions_map:
        for each_question in questions_map[question]:
            reply = reply + each_question + "\n"
        reply = reply + "----------------------\n"
    return reply


def determine_response(message, team_name, division_uid, team_id):

    next_game_questions = [
        "hey milo whens the next game",
        "hey milo whens our next game",

        "hey milo when’s the next game",
        "hey milo when’s our next game",

        "hey milo when's the next game",
        "hey milo when's our next game",

        "hey milo when is our next game",
        "hey milo when is the next game",

        "hey milo next game",
    ]

    current_season_questions = [
        "hey milo whats the current season",
        "hey milo what's the current season",
        "hey milo what’s the current season",
        "hey milo what is the current season",
    ]

    next_season_start_questions = [
        "hey milo whens the next season start",
        "hey milo whats the next season",

        "hey milo when’s the next season start",
        "hey milo what’s the next season",

        "hey milo when's the next season start",
        "hey milo what's the next season",

        "hey milo when does the next season start",
        "hey milo what is the next season",
    ]

    standings_questions = [
        "hey milo whats our current standing",
        "hey milo whats our standing",
        "hey milo whats our current rank",
        "hey milo whats our rank",
        "hey milo whats our current ranking",
        "hey milo whats our ranking",

        "hey milo what's our current standing",
        "hey milo what's our standing",
        "hey milo what's our current rank",
        "hey milo what's our rank",
        "hey milo what's our current ranking",
        "hey milo what's our ranking",

        "hey milo what’s our current standing",
        "hey milo what’s our standing",
        "hey milo what’s our current rank",
        "hey milo what’s our rank",
        "hey milo what’s our current ranking",
        "hey milo what’s our ranking",
    ]

    command_questions = [
        "hey milo what commands do you know",
        "hey milo help",
        "hey milo, help",
    ]

    all_command_questions = [
        "hey milo what are ALL the commands you know",
    ]

    wake_up_questions = [ # I guess these aren't really questions, haven't found a use yet so I haven't added it to the questions map
        "hey milo wake up",
        "hey milo wake up!",
        "hey milo, wake up",
        "hey milo, wake up!",
        "hey milo are you awake",
        "hey milo, are you awake",
        "hey milo are you up",
        "hey milo, are you up",
    ]

    questions_map = {
        "next_game_questions": next_game_questions,
        "current_season_questions": current_season_questions,
        "standings_questions": standings_questions,
        "command_questions": command_questions,
        "next_season_start_questions": next_season_start_questions,
        "all_command_questions": all_command_questions,
        # "wake_up_questions": wake_up_questions,
    }

    for question in questions_map:
        questions_map[question] = add_question_mark(questions_map[question])

    if message in questions_map["next_game_questions"]:
        matches = get_matches(team_name, division_uid)
        next_match = get_next_match(matches)
        link = f"https://flannagans.league.ninja/leagues/division/{division_uid}/schedule"
        reply = f"No time found, probably a tournament or something. Here's the link to the schedule: {link}"
        if next_match == datetime(9999, 9, 9):
            next_match = check_upcoming_matches(team_id)
        if not next_match == datetime(9999, 9, 9): # yeah this is redundant, I'll fix it later
            reply = next_match.strftime("The next game is on %B %dth at %I:%M %p")
            
        return reply

    if message in questions_map["current_season_questions"]:
        return get_current_season()

    if message in questions_map["next_season_start_questions"]:
        return get_next_season()

    if message in questions_map["standings_questions"]:
        return get_standings(team_name, division_uid)

    if message in questions_map["command_questions"]:
        return get_command_questions(questions_map)

    if message in questions_map["all_command_questions"]:
        return get_all_command_questions(questions_map)

    return "idk that command yo" # for if all those "if" statements don't go through

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()

    # We don't want to reply to ourselves!
    if should_reply(data):
        division_uid = team_info[data["group_id"]]["division_uid"]
        bot_id = team_info[data["group_id"]]["bot_id"]
        team_name = team_info[data["group_id"]]["team_name"]
        team_id = team_info[data["group_id"]]["team_id"]
        response = determine_response(data["text"].lower(), team_name, division_uid, team_id)
        send_message(response, bot_id)

    return "OK", 200
