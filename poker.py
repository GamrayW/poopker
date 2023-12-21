from deuces import Evaluator, Card
import random

import db



class IllegalMove(Exception):
	pass


def random_card():
	value = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
	kind = ["c", "d", "h", "s"]
	return f"{random.choice(value)}{random.choice(kind)}"


def random_hand():
	return [random_card(), random_card()]


def random_board():
	return [random_card() for _ in range(random.randint(0, 5))]


def find_winner(players, board):
	"""
	Find the winner from players for the current board
	:param players list: the list of players dict object
	:param board list: the current board
	:return str: the username of the winner
	"""
	board = [Card.new(card) for card in board]
	poker_engine = Evaluator()

	current_winner = [7463, ""]  # 7462 is the maximum score possible (lowest = better)
	for player in players:
		hand = [Card.new(card) for card in player['hand']]

		try:
			score = poker_engine.evaluate(board, hand)
		except:
			score = 1  # since we don't remove cards from the deck, the poker_engine can crash, if it happens someone random will win
					   # this is a somewhat intended logic flaw but it's not part of the challenge, i'm just too lazy to fix it.
		if score < current_winner[0]:
			current_winner = [score, player['username']]
		

	return current_winner[1]


def start(game_id):
	"""
	Start a poker game
	:param game_id int: the id of the game
	"""
	db.start_game(game_id)

	all_players = list(map(lambda player: player["username"], db.get_all_players(game_id)))
	for player in all_players:
		# if the player has no money left, he get kicked out
		if db.get_user_money(game_id, player) <= 0:
			db.kick_player(game_id, player)

		db.set_user_hand(player, game_id, random_hand())

	
	first_seat = all_players[0]
	db.set_current_player_turn(game_id, first_seat)
	db.set_player_end_round(game_id, all_players[0])
	db.set_last_bet(game_id, 1)


def play(game_id, username, action, value):
	"""
	Play an action
	:param game_id int: the id of the game
	:param username str: the username
	:param action str: the action
	:param value int: not used except for 'raise' action
	"""
	last_bet = db.get_last_bet(game_id)
	user_bet = db.get_user_bet(game_id, username)
	money = int(db.get_user_money(game_id, username))

	if action == "flop":
		db.fold(game_id, username)

	elif action == "call":
		# if the bet to match is higher than our money, we all-in
		# else we match it
		if last_bet > money:
			new_bet = money
		else:
			new_bet = last_bet - user_bet

		# minimum call is 1
		if last_bet == 0 and money != 0:
			new_bet = 1

		db.set_user_bet(game_id, username, new_bet, add=True)
		db.set_user_money(game_id, username, money - new_bet)
		db.set_last_bet(game_id, new_bet)

	elif action == "check":
		if user_bet == last_bet:
			return
		raise(IllegalMove)

	elif action == "raise":
		if value < last_bet or value <= 0:
			raise(IllegalMove)

		if value > money:
			value = money

		db.set_user_bet(game_id, username, value, add=True)
		db.set_user_money(game_id, username, money - value)

		db.set_player_end_round(game_id, username)
		db.set_last_bet(game_id, value)

	else:
		raise(IllegalMove)


def match_win(game_id, username):
	winnings = db.get_pot(game_id)
	db.set_user_money(game_id, username, winnings, add=True)
	db.set_pot(game_id, 0)

	db.unfold_all_players(game_id)
	db.set_board(game_id, [""])  # empty the board

	all_players = db.get_all_players(game_id)

	for player in all_players:
		db.set_user_hand(player['username'], game_id, "") # empty his hand

		# if the player has no money left, he get kicked out
		if db.get_user_money(game_id, player['username']) <= 0:
			kick_player(game_id, player['username'])


	if len(all_players) < 2:
		db.stop_game(game_id)
		return

	# restart the game
	start(game_id)


def new_round(game_id):
	total_bets = db.get_all_bets(game_id)
	db.reset_all_bets(game_id)
	db.set_last_bet(game_id, 0)
	db.set_pot(game_id, total_bets, add=True)

	current_board = db.get_board(game_id)

	if len(current_board) == 0:
		new_board = [random_card() for _ in range(3)]
		db.set_board(game_id, new_board)
	elif len(current_board) < 5:
		db.set_board(game_id, [random_card()], add=True)
	else:
		winner = find_winner(db.get_all_players(game_id, folded_included=False, hide_hand=False), current_board)
		match_win(game_id, winner)


def next_player(game_id, curr_player):
	all_players = db.get_all_players(game_id)
	curr_index = next((index for (index, d) in enumerate(all_players) if d["username"] == curr_player), None)
	end_round = db.get_player_end_round(game_id)

	all_players = all_players[curr_index:] + all_players[:curr_index]

	for player in all_players[1:]:
		if player['username'] == end_round:
			new_round(game_id)
			break
		if not player['folded']:
			break

	db.set_current_player_turn(game_id, player['username'])


def kick_player(game_id, player):
	"""
	Kick a player from a game.
	:param game_id int: the id of the game
	:param player str: the name of the player to kick
	"""
	if not db.is_game_started(game_id):
		db.remove_user(game_id, player)
		return

	if player == db.get_current_player_turn(game_id):
		next_player(game_id, player)

	if player == db.get_player_end_round(game_id):
		new_round(game_id)

	db.remove_user(game_id, player)

	players_left = db.get_all_players(game_id)
	if len(players_left) < 2:
		db.set_pot(game_id, 0)
		db.set_board(game_id, [""])
		for player in players_left:
			db.set_user_hand(player['username'], game_id, "") # empty his hand

		db.stop_game(game_id)
