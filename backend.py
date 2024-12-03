from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
CORS(app)
FOLDER_PATH = r"C:\Users\muham\OneDrive\Desktop\Replay Files"
NAME_SUBSTITUTIONS = {
    "斯基比迪厕所": "Aiden",
    "æ–¯åŸºæ¯”è¿ªåŽ•æ‰€": "Aiden"
}

# Global variables for processed data
processed_data = []
role_specific_data = []
player_game_scores = {}

# Normalization and helper functions
def normalize(value, min_value, max_value):
    if max_value - min_value == 0:
        return 0
    return (value - min_value) / (max_value - min_value)

def calculate_score(metrics, weights):
    score = 0
    for metric, weight in weights.items():
        score += metrics.get(metric, 0) * weight
    return score * 100

def colorize_win_rate(win_rate):
    win_rate_value = float(win_rate.strip('%'))
    if win_rate_value >= 80:
        return f"🟢 {win_rate}"
    elif win_rate_value >= 50:
        return f"🟡 {win_rate}"
    else:
        return f"🔴 {win_rate}"

def process_json_files(folder_path):
    global processed_data, role_specific_data, player_game_scores
    players_data = {}
    player_game_scores = {}  # Reset per-game scores

    # Get a sorted list of JSON files
    json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    json_files.sort()  # Files should be named in a way that sorting reflects chronological order

    # Define metric_ranges and role_weights here or globally
    metric_ranges = {
        "win_rate": (0, 100),
        "kda": (0, 10),
        "csm": (0, 15),
        "gpm": (0, 800),
        "damage_per_minute": (0, 2000),
        "vision_score": (0, 50),
        "building_damage": (0, 50000),
        "kpp": (0, 100),
        "rift_herald_kills": (0, 10),
        "dragons_killed": (0, 10),
        "baron_kills": (0, 10),
    }
    role_weights = {
        "TOP": {
            "win_rate": 1,
            "kpp": 0.6,
            "kda": 1,
            "csm": 0.8,
            "gpm": 0.6,
            "damage_per_minute": 0.4,
            "vision_score": 0.2,
            "building_damage": 1
        },
        "JUNGLE": {
            "win_rate": 1,
            "kpp": 1,
            "kda": 0.8,
            "csm": 0.4,
            "gpm": 0.4,
            "vision_score": 0.2,
            "rift_herald_kills": 0.4,
            "dragons_killed": 1.2,
            "baron_kills": 1
        },
        "MIDDLE": {
            "win_rate": 1,
            "kpp": 0.8,
            "kda": 1,
            "csm": 0.8,
            "gpm": 0.6,
            "damage_per_minute": 0.6,
            "vision_score": 0.2,
            "building_damage": 0.2
        },
        "BOTTOM": {
            "win_rate": 1,
            "kpp": 0.6,
            "kda": 0.8,
            "csm": 1,
            "gpm": 0.6,
            "damage_per_minute": 0.8,
            "vision_score": 0.2,
            "building_damage": 0.2
        },
        "UTILITY": {
            "win_rate": 1,
            "kpp": 1,
            "kda": 0.8,
            "gpm": 0.2,
            "vision_score": 1,
            "building_damage": 0.4
        }
    }

    for file_name in json_files:
        with open(os.path.join(folder_path, file_name), 'r') as file:
            data = json.load(file)
            game_length_minutes = data["gameLength"] / 60000
            team_kills = {}
            teams = set(p["TEAM"] for p in data["statsJson"])
            for team in teams:
                team_kills[team] = sum(int(p["CHAMPIONS_KILLED"]) for p in data["statsJson"] if p["TEAM"] == team)
            for player in data["statsJson"]:
                name = NAME_SUBSTITUTIONS.get(player["RIOT_ID_GAME_NAME"], player["RIOT_ID_GAME_NAME"])
                print(f"Processed player name: {name}")  # Debugging log

                role = player.get("INDIVIDUAL_POSITION", "").upper()
                if not role:
                    continue
                if name not in players_data:
                    players_data[name] = {
                        "wins": 0,
                        "games": 0,
                        "scores": [],
                        "roles": [],
                        "role_stats": {},
                        "kda_list": [],
                        "cs_per_minute_list": [],
                        "damage_per_minute_list": [],
                        "gold_per_minute_list": [],
                        "kpp_list": [],
                        "vision": 0,
                        "building_damage": 0,
                        "rift_herald_kills": 0,
                        "dragons_killed": 0,
                        "baron_kills": 0,
                    }
                win = player["WIN"] == "Win"
                kills = int(player["CHAMPIONS_KILLED"])
                deaths = int(player["NUM_DEATHS"]) or 1
                assists = int(player["ASSISTS"])
                minions_killed = int(player["MINIONS_KILLED"])
                jungle_minions_killed = int(player["NEUTRAL_MINIONS_KILLED"])
                total_cs = minions_killed + jungle_minions_killed
                damage = int(player["TOTAL_DAMAGE_DEALT_TO_CHAMPIONS"])
                building_damage = int(player.get("TOTAL_DAMAGE_DEALT_TO_BUILDINGS", 0))
                gold = int(player["GOLD_EARNED"])
                vision = int(player["VISION_SCORE"])
                team = player["TEAM"]
                player_team_kills = team_kills.get(team, 0)
                kda = (kills + assists) / deaths
                cs_per_minute = total_cs / game_length_minutes
                damage_per_minute = damage / game_length_minutes
                gold_per_minute = gold / game_length_minutes
                kpp = ((kills + assists) / player_team_kills) * 100 if player_team_kills > 0 else 0
                dragons_killed = int(player.get("DRAGON_KILLS", 0))
                rift_herald_kills = int(player.get("RIFT_HERALD_KILLS", 0))
                baron_kills = int(player.get("BARON_KILLS", 0))
                metrics = {
                    "win_rate": 100 if win else 0,
                    "kda": kda,
                    "csm": cs_per_minute,
                    "gpm": gold_per_minute,
                    "damage_per_minute": damage_per_minute,
                    "vision_score": vision,
                    "building_damage": building_damage,
                    "kpp": kpp,
                    "rift_herald_kills": rift_herald_kills,
                    "dragons_killed": dragons_killed,
                    "baron_kills": baron_kills,
                }
                normalized_metrics = {}
                for metric, (min_val, max_val) in metric_ranges.items():
                    value = metrics.get(metric, 0)
                    normalized_metrics[metric] = normalize(value, min_val, max_value=max_val)
                weights = role_weights.get(role, {})
                score = calculate_score(normalized_metrics, weights)

                # Append per-game score for the player
                if name not in player_game_scores:
                    player_game_scores[name] = []
                player_game_scores[name].append(score)

                if role not in players_data[name]["role_stats"]:
                    players_data[name]["role_stats"][role] = {
                        "wins": 0,
                        "games": 0,
                        "scores": [],
                        "kda_list": [],
                        "cs_per_minute_list": [],
                        "damage_per_minute_list": [],
                        "gold_per_minute_list": [],
                        "kpp_list": [],
                        "vision": 0,
                        "building_damage": 0,
                        "rift_herald_kills": 0,
                        "dragons_killed": 0,
                        "baron_kills": 0,
                    }
                role_stats = players_data[name]["role_stats"][role]
                role_stats["wins"] += int(win)
                role_stats["games"] += 1
                role_stats["scores"].append(score)
                role_stats["kda_list"].append(kda)
                role_stats["cs_per_minute_list"].append(cs_per_minute)
                role_stats["damage_per_minute_list"].append(damage_per_minute)
                role_stats["gold_per_minute_list"].append(gold_per_minute)
                role_stats["kpp_list"].append(kpp)
                role_stats["vision"] += vision
                role_stats["building_damage"] += building_damage
                role_stats["rift_herald_kills"] += rift_herald_kills
                role_stats["dragons_killed"] += dragons_killed
                role_stats["baron_kills"] += baron_kills
                players_data[name]["roles"].append(role)
                player_stats = players_data[name]
                player_stats["wins"] += int(win)
                player_stats["games"] += 1
                player_stats["scores"].append(score)
                player_stats["kda_list"].append(kda)
                player_stats["cs_per_minute_list"].append(cs_per_minute)
                player_stats["damage_per_minute_list"].append(damage_per_minute)
                player_stats["gold_per_minute_list"].append(gold_per_minute)
                player_stats["kpp_list"].append(kpp)
                player_stats["vision"] += vision
                player_stats["building_damage"] += building_damage
                player_stats["rift_herald_kills"] += rift_herald_kills
                player_stats["dragons_killed"] += dragons_killed
                player_stats["baron_kills"] += baron_kills

    max_games = max(stats["games"] for stats in players_data.values())
    processed_data = []
    role_specific_data = []
    for player, stats in players_data.items():
        games = stats["games"]
        game_penalty = max(0, (max_games - games) / max_games)
        penalty_factor = 1 - (game_penalty ** 2)
        role_scores = []
        penalized_role_scores = []
        for role in set(stats["roles"]):
            role_stats = stats["role_stats"][role]
            role_games = role_stats["games"]
            role_wins = role_stats["wins"]
            role_win_rate = colorize_win_rate(f"{(role_wins / role_games) * 100:.2f}%") if role_games > 0 else "0.00%"
            role_avg_kda = sum(role_stats["kda_list"]) / role_games if role_games > 0 else 0
            role_avg_cs_per_minute = sum(role_stats["cs_per_minute_list"]) / role_games if role_games > 0 else 0
            role_avg_damage_per_minute = sum(role_stats["damage_per_minute_list"]) / role_games if role_games > 0 else 0
            role_avg_gold_per_minute = sum(role_stats["gold_per_minute_list"]) / role_games if role_games > 0 else 0
            role_avg_kpp = sum(role_stats["kpp_list"]) / role_games if role_games > 0 else 0
            role_avg_vision_score = role_stats["vision"] / role_games if role_games > 0 else 0
            role_score = sum(role_stats["scores"]) / role_games if role_games > 0 else 0
            adjusted_role_score = role_score * penalty_factor
            penalized_role_scores.append(adjusted_role_score)
            role_specific_data.append({
                "Player": player,
                "Wins": role_wins,
                "Games": role_games,
                "Win Rate": role_win_rate,
                "Avg KDA": f"{role_avg_kda:.2f}",
                "Avg CS/m": f"{role_avg_cs_per_minute:.2f}",
                "DPM": f"{role_avg_damage_per_minute:.2f}",
                "Avg GPM": f"{role_avg_gold_per_minute:.2f}",
                "KPP": f"{role_avg_kpp:.2f}%",
                "Vision Score": f"{role_avg_vision_score:.2f}",
                "Raw Score": role_score,
                "Score": round(adjusted_role_score, 2),
                "role": role,
            })
            role_scores.append(role_score)
        overall_score = sum(role_scores) / len(role_scores) if role_scores else 0
        adjusted_overall_score = sum(penalized_role_scores) / len(penalized_role_scores) if penalized_role_scores else 0
        avg_kda = sum(stats["kda_list"]) / games if games > 0 else 0
        avg_cs_per_minute = sum(stats["cs_per_minute_list"]) / games if games > 0 else 0
        avg_damage_per_minute = sum(stats["damage_per_minute_list"]) / games if games > 0 else 0
        avg_gold_per_minute = sum(stats["gold_per_minute_list"]) / games if games > 0 else 0
        avg_kpp = sum(stats["kpp_list"]) / games if games > 0 else 0
        avg_vision_score = stats["vision"] / games if games > 0 else 0
        processed_data.append({
            "Player": player,
            "Wins": stats["wins"],
            "Games": games,
            "Win Rate": colorize_win_rate(f"{(stats['wins'] / games) * 100:.2f}%") if games > 0 else "0.00%",
            "Avg KDA": f"{avg_kda:.2f}",
            "Avg CS/m": f"{avg_cs_per_minute:.2f}",
            "DPM": f"{avg_damage_per_minute:.2f}",
            "Avg GPM": f"{avg_gold_per_minute:.2f}",
            "KPP": f"{avg_kpp:.2f}%",
            "Vision Score": f"{avg_vision_score:.2f}",
            "Raw Score": overall_score,
            "Score": round(adjusted_overall_score, 2),
            "building_damage": stats["building_damage"],
            "rift_herald_kills": stats["rift_herald_kills"],
            "dragons_killed": stats["dragons_killed"],
            "baron_kills": stats["baron_kills"],
            "roles": ", ".join(set(stats["roles"])),
        })
    processed_data = sorted(processed_data, key=lambda x: x["Score"], reverse=True)
    role_specific_data = sorted(role_specific_data, key=lambda x: x["Score"], reverse=True)
    return processed_data, role_specific_data

@app.route('/update', methods=['POST'])
def update():
    try:
        process_json_files(FOLDER_PATH)
        return jsonify({"message": "Data updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/scoreboard', methods=['GET'])
def get_scoreboard():
    return jsonify(processed_data)

@app.route('/role_leaderboard', methods=['GET'])
def get_role_leaderboard():
    role = request.args.get('role', '').upper()
    if not role:
        return jsonify({"error": "Role parameter is required"}), 400
    filtered_data = [player for player in role_specific_data if player["role"].upper() == role]
    if not filtered_data:
        return jsonify({"message": f"No players found for role {role}"}), 404
    return jsonify(filtered_data)

@app.route('/stats', methods=['GET'])
def get_player_stats():
    player_name = request.args.get('player_name', '')
    print(f"Looking for stats for player: {player_name}")  # Debug log
    if not player_name:
        return jsonify({"error": "Player name parameter is required"}), 400
    player_stats = next((player for player in processed_data if player["Player"] == player_name), None)
    if not player_stats:
        return jsonify({"message": f"No stats found for player {player_name}"}), 404
    return jsonify(player_stats)




@app.route('/compare', methods=['GET'])
def compare_players():
    player1_name = request.args.get('player1', '')
    player2_name = request.args.get('player2', '')
    if not player1_name or not player2_name:
        return jsonify({"error": "Both player1 and player2 parameters are required"}), 400
    player1 = next((player for player in processed_data if player["Player"] == player1_name), None)
    player2 = next((player for player in processed_data if player["Player"] == player2_name), None)
    if not player1 or not player2:
        return jsonify({"message": "One or both players not found"}), 404
    comparison = {
        "player1": player1_name,
        "player2": player2_name,
        "stats": {
            key: {"player1": player1[key], "player2": player2[key]}
            for key in ["Wins", "Games", "Win Rate", "Avg KDA", "Avg CS/m", "DPM", "Avg GPM", "KPP", "Vision Score", "Score"]
        }
    }
    return jsonify(comparison)


@app.route('/progress', methods=['GET'])
def player_progress():
    player_name = request.args.get('player_name', '')
    scores = player_game_scores.get(player_name, [])
    if not scores:
        return jsonify({"message": f"No progress data for player {player_name}"}), 404

    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(scores) + 1), scores, marker='o')
    plt.title(f"{player_name}'s Progress")
    plt.xlabel("Game Number")
    plt.ylabel("Score")
    plt.grid(True)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    encoded_image = base64.b64encode(buf.getvalue()).decode('utf-8')
    return jsonify({"image": f"data:image/png;base64,{encoded_image}"})

if __name__ == "__main__":
    process_json_files(FOLDER_PATH)
    app.run(debug=True)
