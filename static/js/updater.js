async function get_user_data() {
    let response = await fetch("/api/me");
    if (!response.ok) {
        return ""
    }
    let user_data = await response.json();
    return user_data
}

async function get_game_data() {
    // user info
    let response = await fetch("/api/me");
    if (!response.ok) {
        return undefined
    }
    let user_data = await response.json();


    // game info
    response = await fetch('/api/game/' + user_data['game_id'])
    if (!response.ok) {
        return undefined
    }
    let game_data = await response.json();

    // merge dicts
    return { ...{ 'me': user_data }, ...game_data };
}