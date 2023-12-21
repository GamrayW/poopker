function draw_hand(cards) {
	if (cards.length != 2) {
		document.getElementById('hand_left_card').children[0].src = "/static/img/cards/card_bg.png"
		document.getElementById('hand_right_card').children[0].src = "/static/img/cards/card_bg.png"
	} else {
		document.getElementById('hand_left_card').children[0].src = "/static/img/cards/" + cards[0] + ".png"
		document.getElementById('hand_right_card').children[0].src = "/static/img/cards/" + cards[1] + ".png"
	}
}


function update_profile(money, bet) {
	document.getElementById("user_money").innerHTML = money + "€"
	let bet_token = document.getElementsByClassName('user_bet')[0]
	let bet_amount = bet_token.getElementsByClassName('amount')[0]

	if (bet != 0) {
		bet_token.style = "display: flex;"
		bet_amount.innerHTML = bet
	} else {
		bet_token.style = "display: none;"
	}
}

function draw_user_profile(username, avatar) {
	let username_html = document.getElementById("username")

	user_avatar.src = avatar
}

function draw_board(board, pot) {
	for (var i = 0; i < 5; i++) {
		let curr_card = document.getElementById('board' + i)
		
		if (board[i] == undefined || board[i] == "") {
			curr_card.src = ""
			curr_card.style = "display: none;"
		} else {
			curr_card.src = "/static/img/cards/" + board[i] + ".png"
			curr_card.style = "display: block;"
		}
	}

	document.getElementById("pot_value").innerHTML = pot + "€"
}


function draw_ennemies(ennemies, my_seat) {
	let ennemy_seats = [ennemies[0], ennemies[1], ennemies[2], ennemies[3], ennemies[4]]
	rotate_seats(ennemy_seats, my_seat-1)

	for (var i = 0; i < 5; i++) {
		let profile = document.getElementById('ennemy' + i)
		let name = profile.getElementsByClassName('ennemy_name')[0]
		let avatar = profile.getElementsByClassName('avatar')[0]
		let money = profile.getElementsByClassName('money')[0]
		let bet_token = profile.getElementsByClassName('ennemy_bet')[0]
		let bet_amount = bet_token.getElementsByClassName('amount')[0]

		let seat_for = (i + 1) // seat = 1...

		if (ennemy_seats[i] == undefined) {
			profile.style = "display: none;"
			continue;
		}

		profile.style = "display: block;"
		name.innerHTML = ennemy_seats[i].username
		avatar.src = ennemy_seats[i].avatar_url
		money.innerHTML = ennemy_seats[i].money + "€"

		if (ennemy_seats[i].folded) {
			profile.classList.add('folded')
		} else {
			profile.classList.remove('folded')
		}

		if (ennemy_seats[i].bet != 0) {
			bet_token.style = "display: flex;"
			bet_amount.innerHTML = ennemy_seats[i].bet
		} else {
			bet_token.style = "display: none;"
		}
	}
}


function draw_playing(username, me) {
	for (let i = 0; i < 5; i++) {
		let profile = document.getElementById('ennemy' + i)
		let name = profile.getElementsByClassName('ennemy_name')[0]
		if (name.innerHTML == username) {
			profile.classList.add("playing")
		} else {
			profile.classList.remove("playing")
		}
	}

	let profile_buttons = document.getElementsByClassName('choice')

	for (let i = 0; i < profile_buttons.length; i++) {
		if (username == me['username']) {
			profile_buttons[i].disabled = false
		} else {
			profile_buttons[i].disabled = true
		}
	}

	let user_profile = document.getElementById("user_choices")

	if (username == me['username']) {
		user_profile.style.boxShadow = "0 0 20px 10px rgba(255, 255, 255, 0.8)"
		user_profile.style.border = "0 0 10px 5px rgba(255, 255, 255, 0.8)"
	} else {
		user_profile.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.1)"
		user_profile.style.border = "2px solid #555;"
	}


	if (me['folded'] == true) {
		document.getElementById("user_choices").classList.add("folded")
	} else {
		document.getElementById("user_choices").classList.remove("folded")
	}
}

function change_main_hand_card(card1, card2) {
    document.getElementById(card1).style.zIndex = "1";
    document.getElementById(card2).style.zIndex = "0";
}


function rotate_seats(arr, n) {
	for (let i = 0; i < n; i++) {
		arr.push(arr.shift());
	}
	return arr;
}