from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
import random
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from settings import ACCOUNT_SID, AUTH_TOKEN


# https://www.unicode.org/emoji/charts/full-emoji-list.html#1f7e5
NOT_EXIST = '\U0001f7e5'  # red
EXIST = '\U0001f7e8'  # yellow
CORRECT = '\U0001f7e9'  # green
SECRET_KEY = 'TotallyNotASecretKey'
app = Flask(__name__)
app.config.from_object(__name__)

callers = {
    "+16463610599": "Yu",
    "+19179685330": "Daniel",
}

def print_legend():
    return ("" + NOT_EXIST+" = Not Exists\n"+EXIST+" = Exists\n"+CORRECT+" = Correct\n")

def print_arr(arr):
    if len(arr) == 0:
        return "[]"
    build = "["
    for k in range(0, len(arr)-1):
        build += arr[k] + ','
    build += arr[len(arr)-1]
    build += "]"
    return build

def print_guess(guess):
    build = ""
    for letter in guess:
        build += " "+letter + "  "
    return build

def print_grid(attempt_arr, guess_arr):
    build = ""
    for k in range(0, len(attempt_arr)):
        build += print_guess(guess_arr[k]) + "\n"
        for c in attempt_arr[k]:
            build += c
        build += "\n"
    return build

words_5 = open("words_5.txt", "r")
words_5_arr = []
for word in words_5:
    words_5_arr.append(word.lower().replace("\r", "").replace("\n", ""))

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    """Send a dynamic reply to an incoming text message"""
    # Get the message the user sent our Twilio number
    if (request.values.get('From') not in session):
        session['user'] = request.values.get('From')
    body = request.values.get('Body', None).rstrip()
    name = callers[session['user']]

    # Start our TwiML response
    resp = MessagingResponse()

    # Determine the right reply for this message
    if name in session:
        if body == 'Commands':
            resp.message('Reply:\n' + "Please use the following commands: \n" + 
            "\'Try [word]\' - To make a guess with a word in the place of [word] without brackets (E.g. Try apple)\n" + 
            "\'Reset\' - To start of a new game of Wordle\n" + 
            "\'Exit\' - To quit Wordle")
        elif body == 'Reset':
            word = words_5_arr[int(random.random()*len(words_5_arr))]
            session[name] = [word, 6, [], [], ['_', '_', '_', '_', '_'], [], []]
            resp.message('Reply:\n' + "A new random word had been seleted. Type 'Commands' to list the available commands.") 
        elif body == 'Exit':
            session.pop(name, None)
            resp.message('Reply:\n' + "Thank you for playing. Goodbye!")
        elif session[name][1] == 0:
            resp.message('Reply:\n' + "Game Ended:\n" + 
            "Use \'Reset\' to start of a new game of Wordle\n" +
            "OR \'Exit\' - To quit Wordle")
        elif len(body.split()) == 2 and body.split()[0] == "Try":
            guess = body.split()[1]
            guess = guess + "_____"
            return_hint = ""
            guess = guess[0:5].lower()
            index = 0
            attempt = []
            if guess in words_5_arr:
                for x in guess:
                    # Letter does not exist
                    if x not in session[name][0]:
                        attempt.append(NOT_EXIST)
                        if x not in session[name][2]:
                            session[name][2].append(x)
                    # Letter does exist but not in place
                    else:
                        # Letter is in right position
                        if x == session[name][0][index]:
                            session[name][4][index] = x
                            attempt.append(CORRECT)
                            if x in session[name][3]:
                                session[name][3].remove(x)
                        else:
                            attempt.append(EXIST)
                            if x not in session[name][3] and x not in session[name][3]:
                                session[name][3].append(x)
                    index += 1
                session[name][1] -= 1
                session[name][6].append(guess)
                session[name][5].append(attempt)
                session[name][2].sort()
                session[name][3].sort()
                if guess == session[name][0] and session[name][1] >= 0:
                    session[name][1] = 0
                    resp.message('Reply:\n' + print_grid(session[name][5],session[name][6]) + "\nYou Won! You had guessed the word correctly.\n Use \'Reset\' for a new game of Wordle\n" + 
                    "OR \'Exit\' - To quit Wordle")
                elif session[name][1] == 0:
                    resp.message('Reply:\n' + "You Lose :(" + print_grid(session[name][5],session[name][6]) + "\nThe hidden word is [" + session[name][0] + "].\n Use \'Reset\' for a new game of Wordle\n" + 
                    "OR \'Exit\' - To quit Wordle")
                else:
                    return_hint = 'Reply:\n' + str(print_legend()) + "Not Exist: " + print_arr(session[name][2]) + "\n" + "Exists:    " + print_arr(
                    session[name][3]) + "\n" + "Correct:   " + print_arr(session[name][4]) + "\n" + str(print_grid(session[name][5],session[name][6]))
                    resp.message(return_hint + "\nAttempt Left: " + str(session[name][1]))
            else:
                resp.message('Reply:\n' + "Invalid word. Please try another word using \'Try [word]\' command.")
        else:
            resp.message('Reply:\n' + "Invalid command. Type 'Commands' to list the available commands.")
    elif body == 'Play Wordle':
        word = words_5_arr[int(random.random()*len(words_5_arr))]
        session[name] = [word, 6, [], [], ['_', '_', '_', '_', '_'], [], []]
        resp.message('Reply:\n' + "Hello! A random word had been seleted. Please use the following commands: \n" + 
        "\'Try [word]\' - To make a guess with a word in the place of [word] without brackets (E.g. Try apple)\n" + 
        "\'Reset\' - To start of a new game of Wordle\n" + 
        "\'Exit\' - To quit Wordle")
    else:
        resp.message('Reply:\n' + "Please reply with the following phases: \n" + 
        "\'Play Wordle\' - To start a game of Wordle\n")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, host='localhost', port=5000)
