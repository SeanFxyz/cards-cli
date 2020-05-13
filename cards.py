import requests, json, time, textwrap
from enum import Enum

class State(Enum):
    LOBBY = 0
    PROMPT = 1
    SELECT = 2
    DISPLAY = 3

def success(text):
    lines = text.splitlines()
    if lines.pop(0) == "SUCCESS":
        return (True, "\n".join(lines))
    return (False, "\n".join(lines))

def checkIntInput(int_str, min_val, max_val):
    try:
        int(int_str)
        if int(int_str) >= min_val and int(int_str) <= max_val:
            return True
        return False
    except ValueError:
        return False

def getIntInput(prompt, min_val, max_val):
    print(prompt)
    i = input()
    while checkIntInput(i, min_val, max_val) == False:
        print("Invalid")
        print(prompt)
        i = input()
    return int(i)

def qryGame(url, session_id):
    data = {
            "game_id": game_id,
            "session_id": session_id}

    r = requests.post(url + "/qry", data=data)
    text = success(r.text)
    if text[0]:
        return json.loads(text[1])
    print("Query failed:")
    print(text[1])
    return None

def joinGame(url, game_id, player_id, password=""):
    data = {
            "game_id": game_id,
            "player_id": player_id,
            "password": password}
    r = requests.post(url + "/join", data=data)
    text = success(r.text)
    if text[0]:
        return text[1]
    print("Join failed:")
    print(text[1])
    return False

def login(url, nick=""):
    r = requests.post(url + "/login", data={"player_name":nick})
    rlines = r.text.splitlines()
    if rlines[0] == "SUCCESS":
        return rlines[1]
    return None

def getGames(url):
    r = requests.get(url + "/games")
    rlines = r.text.splitlines()
    if rlines.pop(0) == "SUCCESS":
        return json.loads("\n".join(rlines))
    return None


def isGame(url, game_id):
    games = getGames(url)
    if games:
        for g in games:
            if g["game_id"] == game_id:
                return True
        
        return False

def createGame(url, game_name, player_id, hidden=False, max_players=2):
    data={
            "game_name": game_name,
            "player_id": player_id,
            "hidden": int(hidden),
            "password": "",
            "max_players": max_players
            }

    r = requests.post(url + "/create", data=data)

    text = success(r.text)
    if text[0]:
        return text[1].splitlines()
    print("Failed to create game:")
    print(text[1])
    return None

def startGame(url, session_id):
    data = {"session_id":session_id, "cmd":"start", "args":"[]"}
    r = requests.post(url + "/cmd", data=data)
    text = success(r.text)
    if text[0]:
        return True
    print("Failed to start game:")
    print(text[1])
    return False

def submit(url, session_id, sub):
    sub_json = json.dumps(sub)
    data = {"session_id":session_id, "cmd":"submit", "args":sub_json}
    r = requests.post(url + "/cmd", data=data)
    text = success(r.text)
    if text[0]:
        return text[1]
    print("Failed to submit:")
    print(text[1])
    return False

def select(url, session_id, sel_id):
    sel_json = json.dumps([sel_id])
    data = {"session_id":session_id, "cmd":"select", "args":sel_json}
    r = requests.post(url + "/cmd", data=data)
    text = success(r.text)
    if text[0]:
        return text[1]
    print("Selection failed:")
    print(text[1])
    return False

def unpackCardText(text):
    text = json.loads(text)
    text = " _____ ".join(text)
    return "\n".join(textwrap.wrap(text, width=50))


if __name__ == "__main__":
    print("Connect to server:")
    url = input()
    print("Desired nickname:")
    nick = input()
    player_id = login(url, nick)
    if player_id == None:
        print("login failed")
        exit(1)

    game_id = ""
    session_id = ""

    print("1: Create game")
    print("2: Enter game code")
    print("3: Get game list")
    print("4: Cancel")
    g = input()
    while g != "1" and g != "2" and g != "3" and g != "4":
        print("invalid option")
        print("1: Create game")
        print("2: Enter game code")
        print("3: Get game list")
        print("4: Cancel")
        g = input()

    if g == "1":
        print("Game hidden? [y/N]:")
        hidden = input()
        while(hidden != "y" and hidden != "n" and
                hidden != "Y" and hidden != "N" and
                hidden != ""):
            print("Game hidden? [y/N]:")
            hidden = input()
        if hidden == "y" or hidden == "Y":
            hidden = True
        else:
            hidden = False
        print("Game name:")
        game_name = input()
        max_players = getIntInput("Max Players: ", 1, 8)
        game_id, session_id = createGame(url, game_name,
                player_id, hidden, max_players)
    elif g == "2":
        g = input()
        if g in [row["game_id"] for row in getGames(url)]:
            game_id = g
        else:
            print("failed to query requested game")
            exit(1)

    elif g == "3":
        games = getGames(url)
        if games == None:
            print("failed to get game list")
            exit(1)
        for game in range(len(games)):
            print(str(game) + ": " + games[game]["game_name"])

        print("Select a game: ")
        g = input()

        game_id = games[int(g)]['game_id']

    elif g == "4":
        exit(0)

    # game_id set, attempt join
    # print("Enter password:")
    # password = input()
    password = ""
    if bool(session_id) == False:
        session_id = joinGame(url, game_id, player_id, password)
    if session_id == False:
        print("Failed to join game")
        exit(1)

    # game joined, commence gameplay loop
    quit = False
    while quit == False:
        
        qry = qryGame(url, session_id)
        if bool(qry) == False:
            print("Initial query failed.")
            exit(1)
        while State(qry["state"]) == State.LOBBY:
            print("Waiting for game start.")
            print("Game ID: " + qry["game_id"])
            print("Players: ",
                    (str(qry["player_count"]) + "/" + str(qry["max_players"])),
                    sep="")
            for p in qry["players"].keys():
                print(qry["players"][p])
            if qry["host"] == player_id:
                print("1: Refresh")
                print("2: Start game")
                i = getIntInput("?", 1, 2)
                if i == 2:
                    strtgame = startGame(url, session_id)
                    if strtgame != True:
                        print(strtgame)

            else:
                time.sleep(2)

            qry = qryGame(url, session_id)

        print("Game has started.")
        qry = qryGame(url, session_id)
        call = unpackCardText(qry["current_prompt"])
        cards_req = qry["cards_req"]
        cards = qry["cards"]
        czar = qry["czar"]
        cards_submitted = 0
        sub = []
        sub_text = []
        print("Czar: ", qry["players"][czar], sep="")
        print("Prompt: ", call, sep="")
        if czar != player_id:
            while cards_submitted < cards_req:

                print("-------------------------")
                
                print("Current submission (" + 
                        str(cards_submitted) + "/" + str(cards_req) + "):")
                for c in range(len(sub_text)):
                    print(str(c) + ": " + sub_text[c])

                print("-------------------------")

                print("Your cards:")
                for c in range(len(cards)):
                    print(str(c + 1) + '. ' + unpackCardText(cards[c]["text"]))

                c = getIntInput("Submit a card:",
                        1, len(cards) + 1) - 1
                sub.append(cards[c]["response_id"])
                sub_text.append(unpackCardText(cards[c]["text"]))
                del cards[c]
                cards_submitted += 1

            submit(url, session_id, sub)

        print("Waiting for submissions...")
        while State(qry["state"]) == State.PROMPT:
            qry = qryGame(url, session_id)
            time.sleep(2)

        print("Submission stage complete")

        print("Waiting for ", qry["players"][czar], 
                " to pick a favorite...", sep="")
        while State(qry["state"]) == State.SELECT:
            if qry["czar"] == player_id:
                print("Prompt: ", call, sep="")
                subs = qry["subs"]
                input_prompt = ""
                for n in range(len(subs)):
                    sub = subs[n]
                    sub_player_id = sub["player_id"]
                    sub_player_name = qry["players"][sub_player_id]
                    input_prompt += str(n + 1) + ". " + sub_player_name + ":\n"
                    for m in range(len(sub["cards"])):
                        card = sub["cards"][m]
                        input_prompt += " * " + unpackCardText(card["text"])+'\n'

                input_prompt += "Select a submission:"
                sel_input = getIntInput(input_prompt, 1, len(subs)) - 1
                sel_id = subs[sel_input]["player_id"]
                select(url, session_id, sel_id)
            else:
                time.sleep(2)

            qry = qryGame(url, session_id)

        subs = qry["subs"]
        czar_name = qry["players"][qry["czar"]]
        losers = []
        for sub in qry["subs"]:
            if sub["player_id"] == qry["selection"]:
                print("Czar " + czar_name + "'s pick:")
                for card in sub["cards"]:
                    print(" * " + unpackCardText(card["text"]))
            else:
                losers.append(sub)
        print("Other submissions:")
        for sub in losers:
            print(qry["players"][sub["player_id"]] + ":")
            for card in sub["cards"]:
                print(" * " + unpackCardText(card["text"]))
            

        while State(qry["state"]) == State.DISPLAY:
            time.sleep(2)
            qry = qryGame(url, session_id)
