import json
import requests
from datetime import datetime, timedelta
from dalle import draw_image

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


# Get all the upcoming matches for our team and returns a list of matches
# old way of getting the next upcoming match (in conjunction with get_next_match), replaced by get_upcoming_match.
def get_matches_list(team_name, division_uid):
    url = f"https://flan1-lms-pub-api.league.ninja/divisions/{division_uid}/schedule/"
    r = requests.get(url)
    matches = []
    for item in r.json()["Data"]:
        if item["homeTeam"] and item["awayTeam"]:  # lazy null check
            if item["homeTeam"]["name"] == team_name or item["awayTeam"]["name"] == team_name:
                dt_format = "%Y-%m-%d %H:%M:%S"
                matches.append(datetime.strptime(item["matchStart"].replace("T", " "), dt_format) - timedelta(
                    hours=5))  # Matches are 4 hours ahead for whatever reason, 5 when DST is happening (fall back).
    return matches


# new way to get our team's next match
def get_upcoming_match(team_id):
    url = f"https://flan1-lms-pub-api.league.ninja/teams/{team_id}"
    r = requests.get(url)
    next_game = datetime(9999, 9, 9)
    try:
        game_check = r.json()["Data"]["upcomingMatches"][0]["matchStart"]
        dt_format = "%Y-%m-%d %H:%M:%S"
        next_game = datetime.strptime(game_check.replace("T", " "), dt_format) - timedelta(
            hours=5)  # Matches are 4 hours ahead for whatever reason, 5 when DST is happening (fall back).
    except:  # Pretty sure this is supposed to catch an IndexError or KeyError on game_check, but not 100% sure.
        pass  # no need to do anything
    return next_game

# new way to get our team's next match
def get_court(team_id):
    url = f"https://flan1-lms-pub-api.league.ninja/teams/{team_id}"
    r = requests.get(url)
    court = ""
    try:
        court_check = " on " + r.json()["Data"]["leagueInfo"]["divisionName"]
    except:  # Pretty sure this is supposed to catch an IndexError or KeyError on game_check, but not 100% sure.
        pass  # no need to do anything
    return court_check


# taking a list of our team's matches then looking for the closest one
# old way of getting the next upcoming match (in conjunction with get_matches_list), replaced by get_upcoming_match.
def select_next_match_from_list(matches, team_id):
    today = datetime.now()
    next_game = datetime(9999, 9, 9)
    for game in matches:
        if game > today:
            if game - today < next_game - today:
                next_game = game
    if next_game == datetime(9999, 9, 9):
        next_game = check_upcoming_matches(team_id)
    return next_game


# Gets the ranking for our team. Currently, it doesn't know the total number of teams in the division.
def get_standings(team_name, division_uid):
    url = f"https://flan1-lms-pub-api.league.ninja/divisions/{division_uid}/standings/"
    r = requests.get(url)
    standing = "bugging out, not sure"
    for item in r.json()["Data"]:
        if item["teamName"] == team_name:
            standing = f"Our team is ranked {item['ranking']}"
    return standing

# Method just to append a question mark to all the possible questions in case someone wants to be grammatically correct
def add_question_mark(question_array):
    temp_array = []
    for question in question_array:
        temp_array.append(question + "?")
    final_array = question_array + temp_array
    return final_array


# Displays one version of all the questions you can ask milo
def get_command_questions(questions_map):
    reply = "I know the following commands: \n"
    for question in questions_map:
        reply = reply + questions_map[question][0] + "\n"
    return reply


# Displays all the questions you can ask milo
def get_all_command_questions(questions_map):
    reply = "Get ready for a wall of text, here's all the commands I know: \n"
    for question in questions_map:
        for each_question in questions_map[question]:
            reply = reply + each_question + "\n"
        reply = reply + "----------------------\n"
    return reply


def is_dalle_question(message):
    start_check = "hey milo draw:" # start of a dalle question, the rest should be the prompt to draw
    return message.startswith(start_check)

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
        "hey milo what are all the commands you know"
    ]

    questions_map = {
        "next_game_questions": next_game_questions,
        "current_season_questions": current_season_questions,
        "standings_questions": standings_questions,
        "command_questions": command_questions,
        "next_season_start_questions": next_season_start_questions,
        "all_command_questions": all_command_questions,
    }

    for question in questions_map:
        questions_map[question] = add_question_mark(questions_map[question])

    if message in questions_map["next_game_questions"]:
        next_match = get_upcoming_match(team_id)
        court = get_court(team_id)
        link = f"https://flannagans.league.ninja/leagues/division/{division_uid}/schedule"
        reply = next_match.strftime("The next game is on %B %dth at %I:%M %p") + court
        if next_match == datetime(9999, 9, 9):
            reply = f"No time found. Go figure it out yourself. Here's the link to the schedule: {link}"
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

    if is_dalle_question(message):
        prompt = message[message.index(":") + 1:].strip()  # The "+1" is to get the stuff after the semi colon
        if len(prompt) > 0:  # No need for a function call if the prompt is empty
            image_url = draw_image(prompt)
        else:  # Well, well, well, you sent an empty prompt huh?
            image_url = "couldn't read your prompt, try again or ask ed(mond) to fix whatever bug is causing this"  # Might as well reuse the variable name
        return image_url

    return "idk that command yo"  # for if all those "if" statements don't go through

