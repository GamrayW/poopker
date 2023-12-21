
async function get_games() {
	const response = await fetch('/api/game_list');
    
    if (!response.ok) {
        return ""
    }

    const data = await response.json();
    return data;
}


function current_avatar() {
	let avatar = document.getElementById("avatar")
	return parseInt(avatar.src.split('avatar_')[1].split('.')[0])
}

function next_avatar() {
	let avatar = document.getElementById("avatar")
	let curr_avatar_num = current_avatar()

	if (curr_avatar_num >= 10) {
		avatar.src = "/static/img/avatars/avatar_1.png"
		document.getElementById("avatar_choice").value = 1
	} else {
		avatar.src = "/static/img/avatars/avatar_" + (curr_avatar_num + 1) + ".png"
		document.getElementById("avatar_choice").value = curr_avatar_num + 1
	}
}

function previous_avatar() {
	let avatar = document.getElementById("avatar")
	let curr_avatar_num = current_avatar()

	if (curr_avatar_num <= 1) {
		avatar.src = "/static/img/avatars/avatar_10.png"
		document.getElementById("avatar_choice").value = 10
	} else {
		avatar.src = "/static/img/avatars/avatar_" + (curr_avatar_num - 1) + ".png"
		document.getElementById("avatar_choice").value = curr_avatar_num - 1
	}
}



function show_register(game_id) {
	let register_form = document.getElementById("register")
	register_form.style = "display: flex;"
	register_form.getElementsByClassName("game_choice")[0].value = game_id
	console.log(game_id)
}