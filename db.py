import os
import base64
import sqlite3

import config


# ---------- UTILS FUNCTIONS ---------- #
def format_user_data(raw_user, hide_hand=True):
	"""
	Just check the return to see what it looks like
	If hide_hand=False is not precised, we don't include the user hand to prevent leaking it
	hide_hand=False should only be present in the /api/me endpoint and poker fuctions
	:param raw_user: the output of the sql query
	:return dict: the user
	"""
	return {
		'username': raw_user[1],
		'avatar_url': f"/static/img/avatars/avatar_{raw_user[2]}.png",
		'game_id': raw_user[3],
		'money': int(raw_user[4]),
		'hand': raw_user[6].split(' ') if raw_user[6] is not None and not hide_hand else [],
		'seat': raw_user[7],
		'bet': raw_user[8],
		'folded': bool(raw_user[9])
	}


def generate_cookie():
	"""
	Generate a random cookie by reading 128 chars in /dev/urandom
	and encode them in base16 to avoid eventual issue with http stuff.
	:return str: the cookie
	"""
	with open("/dev/urandom", "rb") as f:
		cookie = f.read(128)
	return base64.b16encode(cookie).decode("utf-8")


def execute(query, params=(), fetchone=False):
	"""
	Execute a SQL query procedure
	:param query str: the SQL query, with '?' as parameters like normally
	:param params list opt: the parameter as an iterable like normally
	:return list: The response from the db (if there's one)
	"""
	connection = sqlite3.connect(config.DB_NAME)
	cursor = connection.cursor()

	response = cursor.execute(query, params)
	response = response.fetchone() if fetchone else response.fetchall()

	connection.commit()
	connection.close()

	return response


# ----------- GAME FUNCTIONS ----------- #
def game_exists(game_id):
	"""
	Verify that the game id provided exist
	:param game_id int: the id of the game
	:return bool: yes
	"""
	return len(execute("SELECT * FROM Games WHERE id=?", [game_id])) != 0


def get_all_games_public_info():
	"""
	Return the public info for all the games in the following format:
		{
			<game_id>: {
				'name': <name>
				'connected': <number of players>
			},
			...
		}
	:return dict: the public info of all the games
	"""
	game_info = execute("SELECT id, name FROM Games")
	result = {}
	for game_id, name in game_info:
		result[game_id] = { 'name': name, 'connected': players_in_game(game_id) }
	
	return result


def is_game_started(game_id):
	"""
	Find if the game has started or not
	:param game_id int: the id of the game
	:return bool: yes
	"""
	return execute("SELECT started FROM Games WHERE id=?", [game_id], fetchone=True)[0]


def start_game(game_id):
	"""
	Start the game
	:param game_id int: the id of the game
	:return void:
	"""
	execute("UPDATE Games SET started=1 WHERE id=?", [game_id])


def stop_game(game_id):
	"""
	Stop the game
	:param game_id int: the id of the game
	:return void:
	"""
	execute("UPDATE Games SET started=0 WHERE id=?", [game_id])


def players_in_game(game_id):
	"""
	Get the number of players connected to the game.
	:param game_id int: the id of the game
	:return int: the number of players
	"""
	return len(execute("SELECT * FROM Users WHERE game_id=?", [game_id]))


def get_all_players(game_id, folded_included=True, hide_hand=True):
	"""
	Get all the player in a game, sorted by their seat place
	:param game_id int: the id of the game
	:param folded_included bool opt: if we also want the folded users or not
	:return list: the players formatted (see format_user_data)
	"""
	if folded_included:
		all_players = execute("SELECT * FROM Users WHERE game_id=? ORDER BY seat_index", [game_id])
	else:
		all_players = execute("SELECT * FROM Users WHERE game_id=? AND folded=0 ORDER BY seat_index", [game_id])

	return [format_user_data(player, hide_hand=hide_hand) for player in all_players]


def get_board(game_id):
	"""
	Get the current board of the game provided
	:param game_id int: the id of the game
	:return list: the board
	"""
	board = execute("SELECT board FROM Games WHERE id=?", [game_id], fetchone=True)[0].split(' ')
	if board == ['']:  # if there's nothing, sqlite will still return '' so we remove it here
		board = []
	return board


def set_board(game_id, value, add=False):
	"""
	Set the board of the game
	:param game_id int: the id of the game
	:param value list: the list of the board ["3_2", "12_1" ... ]
	:param add bool opt: if we want to add to the current board or not
	"""
	current_board = get_board(game_id)
	new_board = current_board + value if add else value
	execute("UPDATE Games SET board=? WHERE id=?", (' '.join(new_board), game_id))


def get_current_player_turn(game_id):
	"""
	Get the current player turn in the specified game
	:param game_id int: the id of the game
	:return str,none: the player turn
	"""
	if not is_game_started(game_id):
		return None
	return execute("SELECT player_turn FROM Games WHERE id=?", [game_id], fetchone=True)[0]


def set_current_player_turn(game_id, username):
	"""
	Set the current player turn in the specified game
	:param game_id int: the id of the game
	:param username str: the name of the player
	:return void:
	"""
	execute("UPDATE Games SET player_turn=? WHERE id=?", (username, game_id))


def get_player_end_round(game_id):
	"""
	Get the player that closes the round
	:param game_id int: the id of the game
	:return str,none: the player username
	"""
	return execute("SELECT player_end_round FROM Games where id=?", [game_id], fetchone=True)[0]


def set_player_end_round(game_id, username):
	"""
	Set the player that will close the current round
	:param game_id int: the id of the game
	:param username str: the player
	"""
	return execute("UPDATE Games SET player_end_round=? WHERE id=?", (username, game_id))


def next_player_seat(game_id):
	"""
	Get the player next to play
	:param game_id int: the id of the game
	:param folded_included bool opt: if we want the folded users or not
	:return player,none: the player turn
	"""
	all_players = get_all_players(game_id)
	if len(all_players) == 0:
		return None  # everyone is folded. (?)

	# get the seat index of the current player
	# (transform all_players to a list of username and get the index of the username passed as param)
	current_index = list(map(lambda el: el["username"], all_players)).index(username)

	# return next player or first if we reached the end of the list
	if current_index + 1 == len(all_players):
		return all_players[0]
	return all_players[current_index + 1]


def get_ennemies(game_id, username):
	"""
	Get all the other players in the room except yourself, sorted by their seat
	:param game_id int: the id of the game
	:param username str: the name of the player to exclude
	:return list: list of users formatted (see format_user_data)
	"""
	all_ennemies = execute("SELECT * FROM Users WHERE game_id=? AND username NOT LIKE ? ORDER BY seat_index", (game_id, username))
	return [format_user_data(user) for user in all_ennemies]


def get_last_bet(game_id):
	"""
	Returns the last bet made in the game.
	:param game_id int: the id of the game
	:return int: the last bet
	"""
	return int(execute("SELECT last_bet FROM Games WHERE id=?", [game_id], fetchone=True)[0])


def set_last_bet(game_id, value):
	execute("UPDATE Games SET last_bet=? WHERE id=?", (value, game_id))


def get_all_bets(game_id):
	"""
	Get the sum of all the bets.
	:param game_id int: the id of the game
	"""
	return sum(list(map(lambda user: user['bet'], get_all_players(game_id))))


def reset_all_bets(game_id):
	"""
	Set all bets to 0
	:param game_id int: the id of the game
	"""
	execute("UPDATE Users SET bet=0 WHERE game_id=?", [game_id])


def get_pot(game_id):
	return int(execute("SELECT current_pot FROM Games WHERE id=?", [game_id], fetchone=True)[0])


def set_pot(game_id, value, add=False):
	new_pot = value + get_pot(game_id) if add else value
	execute("UPDATE Games SET current_pot=? WHERE id=?", (new_pot, game_id))


def unfold_all_players(game_id):
	"""
	Unfold everyone in the game, used when a new match starts
	:param game_id int: the id of the game
	"""
	execute("UPDATE Users SET folded=0 WHERE game_id=?", [game_id])


# ----------- USER FUNCTIONS ----------- #
def get_user_from_cookie(cookie):
	"""
	Get the user from the cookie.
	:return: the user formatted (see format_user_data) or None if user does not exist
	"""
	user = execute("SELECT * FROM Users WHERE cookie LIKE ?", [cookie], fetchone=True)
	return format_user_data(user, hide_hand=False) if user is not None else None


def is_user_folded(username, game_id):
	"""
	Check if user is folded
	:param username str: the name to check
	:param game_id int: the id of the game
	:return bool: True if the user is folded
	"""
	return bool(execute("SELECT folded FROM Users WHERE username=? AND game_id=?", (username, game_id), fetchone=True)[0])


def is_user_in_game(username, game_id):
	"""
	Check if the username provided is actually in the game
	:param username str: the name to check
	:param game_id int: the id of the game
	:return bool: True if user is playing
	"""
	return len(execute("SELECT * FROM Users WHERE username LIKE ? AND game_id=?", (username, game_id))) != 0


def register_user(username, avatar, game_id):
	"""
	Register a new user in the database
	:param username str: the name of the new user (check with is_unique_username first)
	:param avatar int: the id of the avatar [1-10]
	:param game_id int: the id of the game
	:return str: the cookie for the new user 
	"""
	cookie = generate_cookie()
	seat_index = players_in_game(game_id) + 1
	execute("INSERT INTO Users (username, avatar_id, game_id, money, cookie, seat_index, bet, folded) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", 
							 (username, avatar, game_id, config.DEFAULT_MONEY, cookie, seat_index, 0, 0))
	return cookie


#----------- USER ACTIONS -----------#

def set_user_hand(username, game_id, hand):
	"""
	Change the player hand
	:param username str: the name of the player
	:param game_id int: the id of the game
	:param hand list: the hand to set ex: ["1_4", "2_3"]
	:return void:
	"""
	execute("UPDATE Users SET hand=? WHERE username LIKE ? AND game_id=?", (' '.join(hand), username, game_id))


def get_user_money(game_id, username):
	return int(execute("SELECT money FROM Users WHERE username LIKE ? AND game_id=?", (username, game_id), fetchone=True)[0])


def set_user_money(game_id, username, value, add=False):
	current_money = get_user_money(game_id, username)
	new_money = current_money + value if add else value
	execute("UPDATE Users SET money=? WHERE username LIKE ? AND game_id=?", (new_money, username, game_id))


def set_user_bet(game_id, username, value, add=False):
	current_bet = get_user_bet(game_id, username)
	new_bet = current_bet + value if add else value
	execute("UPDATE Users SET bet=? WHERE username LIKE ? AND game_id=?", (new_bet, username, game_id))


def get_user_bet(game_id, username):
	return int(execute("SELECT bet FROM Users WHERE username LIKE ? AND game_id=?", (username, game_id), fetchone=True)[0])


def fold(game_id, username):
	execute("UPDATE Users SET folded=1 WHERE username LIKE ? AND game_id=?", (username, game_id))
	return True


def remove_user(game_id, username):
	"""
	Be sure to check beforehand if removing it will not cause problems
	(current_user, user_end_round etc...)
	"""
	execute("DELETE FROM Users WHERE username LIKE ? AND game_id=?", (username, game_id))


def init():
	"""
	Setup the DB.
	Each restart = wipe of all the data
	"""
	try:
		execute("DROP TABLE Users;")
		execute("DROP TABLE Games;")
	except:
		pass

	execute("""CREATE TABLE IF NOT EXISTS Games (
							id INTEGER PRIMARY KEY,
							name VARCHAR(255) DEFAULT "",
							board VARCHAR(255) DEFAULT "",
							current_pot INTEGER DEFAULT 0,
							started INTEGER DEFAULT 0,
							player_turn VARCHAR(255) DEFAULT "",
							player_end_round VARCHAR(255) DEFAULT "",
							last_bet INTEGER DEFAULT 1);
				 """)

	execute("""CREATE TABLE IF NOT EXISTS Users (
							id INTEGER PRIMARY KEY,
							username VARCHAR(255),
							avatar_id INTEGER,
							game_id INTEGER,
							money VARCHAR(255),
							cookie TEXT,
							hand VARCHAR(255),
							seat_index INTEGER,
							bet INTEGER,
							folded INTEGER,
							FOREIGN KEY (game_id) REFERENCES Games(id));
				 """)

	# TODO: make users able to create new game instead of manually adding them like a pig
	execute("INSERT INTO Games (name) VALUES ('Room 1')")
	execute("INSERT INTO Games (name) VALUES ('Room 2')")
	execute("INSERT INTO Games (name) VALUES ('Room 3')")
	execute("INSERT INTO Games (name) VALUES ('Room 4')")
	execute("INSERT INTO Games (name) VALUES ('Room 5')")
	execute("INSERT INTO Games (name) VALUES ('Room 6')")


	# this is for the challenge, please ignore
	execute("INSERT INTO Users (username, avatar_id, game_id, money, cookie, seat_index, bet, folded) VALUES('Gamray', 6, 1, 1000000, 'NOT_THE_COOKIE', 1, 0, 0)")

