import requests, json, enum, time, textwrap

class State(Enum):
    LOBBY = 0
    PROMPT = 1
    SELECT = 2

def success(text):
    lines = text.splitlines()
    if lines.pop(0) == "SUCCESS":
        return "\n".join(lines)
    return None


def qryGame(url, game_id, player_id):
    data = {
            "game_id": game_id
            "player_id": player_id}

    r = requests.post(url + "/qry", data=data)
    rlines = r.text.splitlines()
    if rlines.pop(0) == "SUCCESS":
        return json.loads("\n".join(rlines))
    return None

def joinGame(url, game_id, player_id, password=""):
    data = {
            "game_id": game_id,
            "player_id": player_id,
            "password": password}
    r = requests.post(url + "/join", data=data)
    if r.splitlines()[0] == "SUCCESS":
        return True
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

def createGame(url, game_name, player_id, hidden=False):
    data={
            "game_name": game_name,
            "player_id": player_id,
            "hidden": int(hidden)}

    r = requests.post(url + "/create", data=data)

    rlines = r.text.splitlines()
    if rlines[0] == "SUCCESS":
        return rlines[1]
    return None

def startGame(url, game_id, player_id):
    data = {"game_id":game_id, "player_id":player_id}
    r = requests.post(url + "/start", data=data)
    text = success(r.text)
    if text:
        return True
    return False

def checkIntInput(int_str):
    try:
        int(int_str)
        return True
    except ValueError:
        return False

def getIntInput(prompt, min_val, max_val):
    print(prompt)
    i = input()
    while(checkIntInput(i) == False and
            int(i) < 1 and int(c) > max_val):
        print("Invalid")
        print(prompt)
        i = input()
    return int(i)

def submit(url, game_id, player_id, sub):
    sub_json = json.dumps(sub)
    data = {"game_id":game_id, "player_id":player_id, "sub":sub_json}
    r = requests.post(url + "/submit", data=data)
    text = success(r.text)
    if text:
        return text
    return False

def unpackCardText(text):
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
        game_id = createGame(url, game_id, player_id, hidden)
    elif g == "2":
        g = input()
        if g in [row["game_id"] for row in getGames(url)]
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
            print(game + ": " + games[game])

        print("Select a game: ")
        g = input()

        game_id = games[int(g)]['game_id']

    elif g == "4":
        exit(0)

    # game_id set, attempt join
    print("Enter password:")
    password = input()
    if joinGame(url, game_id, player_id, password) == False:
        print("Failed to join game")
        exit(1)

    # game joined, commence gameplay loop
    quit = False
    while quit == False:
        
        print("Waiting for game to begin...")
        qry = qryGame(url, game_id, player_id)
        while State(qry["state"]) == State.LOBBY:
            qry = qryGame(url, game_id, player_id)
            print("Waiting for game start.")
            print("Players: ",
                    (str(qry["player_count"]) + "/" + str(qry["max_players"])),
                    sep="")
            for p in qry["players"].keys()
                print(qry["players"][p])
            if qry["host"] = player_id:
                print("1: Refresh players")
                print("2: Start game")
                i = getIntInput("?", 1, 2)
                if i == 2:
                    startGame(url, game_id, player_id)

            else:
                time.sleep(2)

        print("Game has started.")
        qry = qryGame(url, game_id, player_id)
        prompt = qry["current_prompt"]
        cards_req = qry["cards_req"]
        cards = qry["cards"]
        czar = qry["czar"]
        cards_submitted = 0
        sub = []
        while cards_submitted < cards_req:
            print("Czar: ", czar, sep="")
            print("Prompt: ", prompt, sep="")

            print("-------------------------")
            
            print("Current submission:")
            for c in range(len(sub)):
                print(str(c) + sub[c])

            print("-------------------------")

            print("Your cards:")
            for c in range(len(cards)):
                print(str(c) + ' ' + unpackCardText(cards[c]["text"]))

            c = getIntInput("Submit a card:",
                    1, len(cards) + 1) - 1
            sub.append(cards[c]["id"])

        submit(url, game_id, player_id, sub)

        while State(qry["state"]) == State.PROMPT:
            qry = qryGame(url, game_id, player_id)
            time.sleep(2)

        print("Submission stage complete")

        print("Waiting for " + qry["czar"] + " to pick a favorite...")
        while State(qry["state"]) == State.SELECT:
            qry = qryGame(url, game_id, player_id)
            if qry["czar"] == player_id:
                # pick a favorite
                pass
            else:
                time.sleep(2)
