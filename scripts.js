const apiBaseUrl = 'http://127.0.0.1:5000';

async function fetchScoreboard() {
    console.log("Fetching scoreboard...");
    try {
        const response = await fetch(`${apiBaseUrl}/scoreboard`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        console.log("Scoreboard data received:", data);
        displayScoreboard(data);
    } catch (error) {
        console.error("Error fetching scoreboard:", error);
        displayError("Failed to fetch scoreboard.");
    }
}

async function fetchRoleLeaderboard() {
    const role = prompt("Enter role (e.g., TOP, JUNGLE):").trim().toUpperCase();
    if (!role) return;
    console.log(`Fetching role leaderboard for role: ${role}`);
    try {
        const response = await fetch(`${apiBaseUrl}/role_leaderboard?role=${role}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        console.log(`Role leaderboard data received for ${role}:`, data);
        displayRoleLeaderboard(data, role);
    } catch (error) {
        console.error("Error fetching role leaderboard:", error);
        displayError(`Failed to fetch role leaderboard for ${role}.`);
    }
}

async function fetchPlayerStats() {
    const playerName = prompt("Enter player name:").trim();
    if (!playerName) return;
    console.log(`Fetching stats for player: ${playerName}`);
    try {
        const response = await fetch(`${apiBaseUrl}/stats?player_name=${encodeURIComponent(playerName)}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        console.log(`Player stats received for ${playerName}:`, data);
        displayPlayerStats(data);
    } catch (error) {
        console.error("Error fetching player stats:", error);
        displayError(`Failed to fetch stats for ${playerName}.`);
    }
}

async function fetchComparePlayers() {
    const player1 = prompt("Enter the first player's name:").trim();
    const player2 = prompt("Enter the second player's name:").trim();
    if (!player1 || !player2) return;
    console.log(`Comparing players: ${player1} vs ${player2}`);
    try {
        const response = await fetch(`${apiBaseUrl}/compare?player1=${encodeURIComponent(player1)}&player2=${encodeURIComponent(player2)}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        console.log(`Comparison data received for ${player1} and ${player2}:`, data);
        displayComparePlayers(data);
    } catch (error) {
        console.error("Error comparing players:", error);
        displayError(`Failed to compare ${player1} and ${player2}.`);
    }
}

function displayScoreboard(data) {
    const contentDiv = document.getElementById('content');
    if (!data || data.length === 0) {
        contentDiv.innerHTML = "<p>No data available.</p>";
        return;
    }
    let table = `
        <table>
            <thead>
                <tr>
                    <th>Player</th>
                    <th>Wins</th>
                    <th>Games</th>
                    <th>Win Rate</th>
                    <th>Avg KDA</th>
                    <th>Avg CS/m</th>
                    <th>DPM</th>
                    <th>Score</th>
                    <th>Roles</th>
                </tr>
            </thead>
            <tbody>
    `;
    data.forEach(player => {
        table += `
            <tr>
                <td>${player.Player}</td>
                <td>${player.Wins}</td>
                <td>${player.Games}</td>
                <td>${player["Win Rate"]}</td>
                <td>${player["Avg KDA"]}</td>
                <td>${player["Avg CS/m"]}</td>
                <td>${player.DPM}</td>
                <td>${player.Score}</td>
                <td>${player.roles}</td>
            </tr>
        `;
    });
    table += '</tbody></table>';
    contentDiv.innerHTML = table;
}

function displayRoleLeaderboard(data, role) {
    const contentDiv = document.getElementById('content');
    if (!data || data.length === 0) {
        contentDiv.innerHTML = `<p>No data available for role ${role}.</p>`;
        return;
    }
    let table = `
        <h2>Role Leaderboard: ${role}</h2>
        <table>
            <thead>
                <tr>
                    <th>Player</th>
                    <th>Wins</th>
                    <th>Games</th>
                    <th>Win Rate</th>
                    <th>Avg KDA</th>
                    <th>Avg CS/m</th>
                    <th>DPM</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
    `;
    data.forEach(player => {
        table += `
            <tr>
                <td>${player.Player}</td>
                <td>${player.Wins}</td>
                <td>${player.Games}</td>
                <td>${player["Win Rate"]}</td>
                <td>${player["Avg KDA"]}</td>
                <td>${player["Avg CS/m"]}</td>
                <td>${player.DPM}</td>
                <td>${player.Score}</td>
            </tr>
        `;
    });
    table += '</tbody></table>';
    contentDiv.innerHTML = table;
}

function displayPlayerStats(data) {
    const contentDiv = document.getElementById('content');
    const stats = `
        <h2>Stats for ${data.Player}</h2>
        <p><strong>Wins:</strong> ${data.Wins}</p>
        <p><strong>Games:</strong> ${data.Games}</p>
        <p><strong>Win Rate:</strong> ${data["Win Rate"]}</p>
        <p><strong>Average KDA:</strong> ${data["Avg KDA"]}</p>
        <p><strong>Average CS/m:</strong> ${data["Avg CS/m"]}</p>
        <p><strong>DPM:</strong> ${data.DPM}</p>
        <p><strong>Roles:</strong> ${data.roles}</p>
    `;
    contentDiv.innerHTML = stats;
}

function displayComparePlayers(data) {
    const contentDiv = document.getElementById('content');
    const stats = `
        <h2>Comparison: ${data.player1} vs ${data.player2}</h2>
        <p><strong>Wins:</strong> ${data.stats.Wins.player1} vs ${data.stats.Wins.player2}</p>
        <p><strong>Games:</strong> ${data.stats.Games.player1} vs ${data.stats.Games.player2}</p>
        <p><strong>Win Rate:</strong> ${data.stats["Win Rate"].player1} vs ${data.stats["Win Rate"].player2}</p>
        <p><strong>Average KDA:</strong> ${data.stats["Avg KDA"].player1} vs ${data.stats["Avg KDA"].player2}</p>
        <p><strong>Score:</strong> ${data.stats.Score.player1} vs ${data.stats.Score.player2}</p>
    `;
    contentDiv.innerHTML = stats;
}

function displayError(message) {
    const contentDiv = document.getElementById('content');
    contentDiv.innerHTML = `<p style="color: red;">${message}</p>`;
}
