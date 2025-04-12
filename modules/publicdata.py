from Database.connection import connect_db
from fastapi import APIRouter, Depends, status
from fastapi import HTTPException as HTTPStatus
from Auth.auth import verify_token
from aiosqlite import IntegrityError
from fastapi.security import HTTPAuthorizationCredentials
from random import choice
from models import teamModels

# These are public api endpoints. Meaning anyone can use these and it was mostly used for the gox web-app (https://gox.yokaigroup.gg).
# Unlike all other endpoints, these do not require a JSON web token (jwt) authorization header. ( {"Authorization":"Bearer <token>"} )

PublicDataRouter = APIRouter(prefix="/public", tags=["public"])

@PublicDataRouter.get("/leaderboard", description="View the leaderboard")
async def match_leaderboard():
    db = await connect_db()
    return_results = []
    fetch_results =  await db.execute("SELECT team, wins, losses, total FROM scores ORDER BY wins DESC")
    fetch_results_collection = await fetch_results.fetchall()

    for result in fetch_results_collection:
        team = result[0]
        wins = result[1]
        losses = result[2]
        total = result[3]
        return_results.append({"team":team, "wins":wins, "losses":losses, "total":total})
    
    await db.close()
    return return_results

@PublicDataRouter.get("/viewteam")
async def view_team(team_name: str):
    db = await connect_db()

    # Check if team exists
    check_exists = await db.execute("SELECT name, tag, region, is_banned, reason, duration FROM teams WHERE name = ?", (team_name.lower(),))
    check_exists_result = await check_exists.fetchone()
    if not check_exists_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="Team does not exist.")
    else:
        name = str(team_name)
        tag = str(check_exists_result[1])
        region = str(check_exists_result[2])
        ban_status = str(check_exists_result[3])
        ban_reason = str(check_exists_result[4])
        ban_duration = str(check_exists_result[5])
        players_data = []
        # Find all players:
        list_players = await db.execute("SELECT userid, gameid, role FROM players WHERE team = ?", (team_name.lower(),))
        list_players_result = await list_players.fetchall()
        team_info = {"name": name, "tag": tag, "region": region, "ban_status":ban_status, "ban_reason":ban_reason, "ban_duration":ban_duration}

        for player in list_players_result:
            players_data += [
                {
                    "userid": player[0],
                    "game_uid": player[1],
                    "role": player[2],
                }
            ]

        print(name)
        print(tag)
        print(region)
        print(players_data)
        await db.close()
        return teamModels.TeamViewResponse(team=team_info, players=players_data)


@PublicDataRouter.get("/viewmatches", description="View all matches played.")
async def view_all_matches():
    
    db = await connect_db()
    matches = []

    list_all_matches_query = await db.execute("SELECT match_id, team_one, team_two, score_team_one, score_team_two FROM matches")
    list_all_matches_result = await list_all_matches_query.fetchall()
    
    for result in list_all_matches_result:
        matchid = result[0]
        team_one = result[1]
        team_two = result[2]
        score_team_one = result[3]
        score_team_two = result[4]
        matches.append({"match_id":matchid, "team_one":team_one, "team_two":team_two, "score_team_one":score_team_one, "score_team_two":score_team_two})

    await db.close()
    return matches 


@PublicDataRouter.get("/blacklist/players", description="Get the public blacklist")
async def get_blacklist():
    db = await connect_db()
    all_bans = []
    # Get ban results
    get_all_bans = await db.execute("SELECT userid, reason, duration FROM players")
    get_all_bans_result = await get_all_bans.fetchall()
    for result in get_all_bans_result:
        userid = result[0]
        reason = result[1]
        end_date = result[2]
        all_bans.append({"userid":userid, "reason":reason, "end_date":end_date})

    if len(all_bans) < 1:
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="No bans.")    
    
    await db.close()
    return all_bans


@PublicDataRouter.get("/blacklist/teams", description="View the public team blacklist.")
async def team_blacklist():
    db = await connect_db()
    all_bans = []
    # Get ban results
    get_all_bans = await db.execute("SELECT name, reason, duration FROM teams")
    get_all_bans_result = await get_all_bans.fetchall()
    for result in get_all_bans_result:
        userid = result[0]
        reason = result[1]
        end_date = result[2]
        all_bans.append({"userid":userid, "reason":reason, "end_date":end_date})

    if len(all_bans) < 1:
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="No bans.")    
    
    await db.close()
    return all_bans
