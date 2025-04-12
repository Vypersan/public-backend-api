from Database.connection import connect_db
from fastapi import APIRouter, Depends, status
from fastapi import HTTPException as HTTPStatus
from Auth.auth import verify_token
from aiosqlite import IntegrityError
from fastapi.security import HTTPAuthorizationCredentials
from models import teamModels

teamrouter = APIRouter(prefix="/teams", tags=["TEAMS"])


@teamrouter.post("/create", description="Create a team.")
async def create_team(userid: str, team_name: str, team_tag: str, region: str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # Create table in case it got lost.
    await db.execute("CREATE TABLE IF NOT EXISTS teams (name TEXT, tag TEXT UNIQUE, region TEXT, is_banned TEXT, reason TEXT, duration TEXT)")
    await db.commit()

    # Check if team exists
    check_exists = await db.execute("SELECT * FROM teams WHERE tag = ?", (team_tag.lower(),))
    check_exists_result = await check_exists.fetchone()
    if check_exists_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_302_FOUND, detail="Team already exists.")
    else:
        await db.execute(
            "INSERT INTO teams VALUES (?, ?, ?, ?, ?, ?)",
            (
                team_name.lower(),
                team_tag.lower(),
                region,
                None,
                None,
                None,
            ),
        )
        await db.commit()
        await db.execute(
            "UPDATE players SET team = ?, role = ? WHERE userid =  ?",
            (
                team_name.lower(),
                "OWNER",
                userid,
            ),
        )
        await db.commit()
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Created team {team_name.lower()} with tag {team_tag}")


@teamrouter.get("/view", description="view a team.")
async def view_team(team_name: str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
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
        is_banned = str(check_exists_result[3])
        ban_reason = str(check_exists_result[4])
        ban_duration = str(check_exists_result[5])
        players_data = []
        # Find all players:
        list_players = await db.execute("SELECT userid, gameid, role FROM players WHERE team = ?", (team_name.lower(),))
        list_players_result = await list_players.fetchall()
        team_info = {"name": str(name), "tag": str(tag), "region": str(region),"ban_status":is_banned, "ban_reason":ban_reason, "ban_duration":ban_duration}

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


@teamrouter.delete("/delete", description="Delete a team.")
async def delete_team(userid: str, team_name: str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # Check if the user is the owner:
    check_has_permission = await db.execute(
        "SELECT role FROM players WHERE userid = ? AND team = ?",
        (
            userid,
            team_name.lower(),
        ),
    )
    check_has_permission_result = await check_has_permission.fetchone()
    if not check_has_permission_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_401_UNAUTHORIZED, detail="User does not have the rights to delete the team.")
    else:
        await db.execute("DELETE FROM teams WHERE name = ?", (team_name.lower(),))
        await db.commit()
        await db.execute(
            "UPDATE players SET team = ?, role = ? WHERE team = ?",
            (
                None,
                None,
                team_name.lower(),
            ),
        )
        await db.commit()
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Deleted {team_name.lower()} ")


@teamrouter.post("/addplayer", description="Add a user to the team.")
async def add_user(userid: str, team_name: str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # Chekc if user is registered and in a team
    check_user = await db.execute(
        "SELECT team FROM players WHERE userid = ?",
        (userid,),
    )
    check_user_result = await check_user.fetchone()
    if not check_user_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="User is not registered.")
    if check_user_result[0] is not None:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is already in a team.")
    else:
        print("Updating user")
        await db.execute(
            "UPDATE players SET team = ?, role = ? WHERE userid = ?",
            (
                team_name.lower(),
                "PLAYER",
                userid,
            ),
        )
        await db.commit()
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK)


@teamrouter.delete("/removeplayer", description="Remove a player from the team.")
async def remove_player_from_team(userid: str, team_name: str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # Chekc if user is registered and in a team
    check_user = await db.execute(
        "SELECT team FROM players WHERE userid = ?",
        (userid,),
    )
    check_user_result = await check_user.fetchone()
    if not check_user_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="User is not registered.")
    if check_user_result[0] is not None:
        if not str(check_user_result[0]).lower() == team_name.lower():
            await db.close()
            raise HTTPStatus(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not in the same team.")
        else:
            await db.execute(
                "UPDATE players SET team = ?, role = ? WHERE userid = ?",
                (
                    None,
                    None,
                    userid,
                ),
            )
            await db.commit()
            await db.close()
            raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Removed {userid} from {team_name.lower()}")
    else:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="User is not registered.")
