from flask import (
		Flask,
		request,
		redirect,
		Response,
		make_response,
		render_template
	)

import time
import string
import threading

import db
import poker
import config



db.init()
app = Flask(__name__)

# dict keeping track of timeouts (if player doesnt play in 30s, he has to be kicked out)
timeout_users = {}


# ---------- NORMAL ENDPOINTS ---------- #
@app.route("/", methods=['GET'])
def home():
	# if user already registered in a game, we make him go play
	player_cookie = request.cookies.get('player')
	if player_cookie and db.get_user_from_cookie(player_cookie):
		return redirect('/play')

	return render_template("home.html")


@app.route("/play", methods=['GET'])
def game():
	# if user is not playing a game, we make him go home
	player_cookie = request.cookies.get('player')
	if not player_cookie or not db.get_user_from_cookie(player_cookie):
		return redirect('/')

	return render_template("game.html")


# ---------- API ENDPOINTS ---------- #
@app.route("/api/me", methods=['GET'])
def user_info():
	"""
	Get all the info about yourself
	"""
	player_cookie = request.cookies.get('player')
	user = db.get_user_from_cookie(player_cookie)
	if not player_cookie or not user:
		return make_response("Not auth.", 403)

	# <THIS SHOULD NOT BE CONSIDERED AS PART OF APPLICATION, IT'S HERE TO MAKE THE CHALL WORK>
	if db.get_user_money(user['game_id'], user['username']) >= 1000000:
		user['flag'] = config.FLAG

	return user


@app.route("/api/game/<int:game_id>", methods=['GET'])
def game_state(game_id):
	"""
	Returns the current state of the game,
		- the current board
		- the ennemies present
		- the player actually playing (player turn)
		- and the current value of the common pot
	"""
	# auth check
	player_cookie = request.cookies.get('player')
	user = db.get_user_from_cookie(player_cookie)
	if not player_cookie or not user:
		return make_response("Not auth.", 403)

	# check if the user is in the game_id provided
	username = user["username"]
	if not db.is_user_in_game(username, game_id):
		return make_response("You're not in this game !", 403)

	ennemies = db.get_ennemies(game_id, username)
	# the player currently playing
	playing = db.get_current_player_turn(game_id)
	return {
			'board': db.get_board(game_id),
			'ennemies': ennemies,
			'playing': playing if playing is not None else "",
			'pot': db.get_pot(game_id)
			}


@app.route("/api/game_list", methods=['GET'])
def game_list():
	data = {}
	for game in db.get_all_games_public_info().values():
		data[game['name']] = game['connected']

	return data


@app.route("/api/join", methods=['POST'])
def join():
	"""
	Try to join a game, a check is made to be sure no one has the same username
	"""
	# Not afraid of directly checking keys because 
	# if exception is raised -> server simply returns 500 
	username = request.form['username']
	avatar_id = int(request.form['avatar'])
	game_id = int(request.form['game_choice'])

	# verify user input
	if 10 < avatar_id <= 0:
		return Response(f"avatar id must be in range [1; 10], can't be {avatar_id}.", status=400)

	if not db.game_exists(game_id):
		return Response(f"Game n°{game_id} does not exist.", status=400)

	if db.players_in_game(game_id) >= 6:
		return Response(f"Too many players, choose another game.", status=400)

	if len(username) > 12:
		return Response(f"{username} is too long, please chose something shorter.", status=400)

	# todo: make a fucking regex instead [0-9a-zA-Z]
	for letter in username:
		if letter not in string.printable[:-38]:
			return Response(f"Please do not choose an username with any special characters.")

	if db.is_user_in_game(username, game_id):
		return Response(f"{username} already exists in the game {game_id}.", status=400)

	# if everything good, we make the user and set it's cookie
	cookie = db.register_user(username, avatar_id, game_id)

	# We start the game if there's enough players
	if db.is_game_started(game_id):
		db.fold(game_id, username)
	else:
		if (db.players_in_game(game_id) >= 2):
			poker.start(game_id)
		

	response = make_response(redirect('/play'), 301)
	response.set_cookie('player', cookie, httponly=True)
	return response


@app.route("/api/game/<int:game_id>/action", methods=["POST"])
def action(game_id):
	"""
	Make an action when it's your turn
	"""
	# auth check
	player_cookie = request.cookies.get('player')
	user = db.get_user_from_cookie(player_cookie)
	if not player_cookie or not user:
		return make_response("Not auth.", 403)

	# check if the user is in the game_id provided
	username = user["username"]
	if not db.is_user_in_game(username, game_id):
		return make_response("You're not in this game !", 403)

	if not db.is_game_started(game_id):
		return make_response("Game haven't started !", 403)

	if username != db.get_current_player_turn(game_id):
		return make_response("It's not your turn yet!", 403)


	action = request.json['action']
	value = 0
	if action == "raise":
		value = int(request.json['value'])

	try:
		poker.play(game_id, username, action, value)
	except poker.IllegalMove:
		return make_response("Illegal Move", 400)


	# Reset the timeout of the user
	timeout_users[f"{game_id},{username}"] = False

	poker.next_player(game_id, username)

	users_left = db.get_all_players(game_id, folded_included=False)
	if len(users_left) == 1:
		poker.match_win(game_id, users_left[0]['username'])

	new_player = db.get_current_player_turn(game_id)
	threading.Thread(target=create_timeout_process, args=(game_id, new_player)).start()
	print(timeout_users)
	return "ok"


@app.route("/api/leave", methods=['POST'])
def leave():
	player_cookie = request.cookies.get('player')
	user = db.get_user_from_cookie(player_cookie)
	if not player_cookie or not user:
		return make_response("Not auth.", 403)

	poker.kick_player(user['game_id'], user['username'])
	return "ok"


def create_timeout_process(game_id, username):
	"""
	Wait 30s and kick the player if it's still it's turn to play.
	:param username str: the player currently playing
	:param game_id int: the corresponding game_id
	"""
	timeout_key = f"{game_id},{username}"
	# it's ugly, but I don't have time to think about doing it better
	timeout_users[timeout_key] = True
	print(f"Starting timeout #{timeout_key} counter")
	time.sleep(60)
	# if timeout_users is still True after 1m, we kick the player
	# it becames False if the player does an action (=> func action)
	if timeout_users[timeout_key]:
		poker.kick_player(game_id, username)


# Running the server
if __name__ == "__main__":
	app.run(host="0.0.0.0")
