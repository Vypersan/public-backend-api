from Database.connection import connect_db
from fastapi import APIRouter, Depends, status
from fastapi import HTTPException as HTTPStatus
from Auth.auth import verify_token
from aiosqlite import IntegrityError
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime


BanRouter = APIRouter(prefix="/bans", tags=["bans"])


@BanRouter.get("/players/view", description="Check if an user is banned or not.")
async def check_user_ban(userid: str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    check_is_banned = await db.execute("SELECT reason, duration FROM players WHERE userid = ?", (userid,))
    check_is_banned_result = await check_is_banned.fetchone()
    if check_is_banned_result is  None:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail="User is not banned.")
    else:
        if check_is_banned_result[1] == datetime.now().strftime("%d-%m-%Y"):
            await db.execute("DELETE FROM playerbans WHERE userid = ?", (userid,))
            await db.commit()
            await db.close()
            raise HTTPStatus(status_code=status.HTTP_200_OK, detail="User was banned but it expired.")
        else:
            ban_reason = check_is_banned_result[0]
            ban_end_time = check_is_banned_result[1]
            await db.close()
            raise HTTPStatus(status_code=status.HTTP_302_FOUND, detail={"Reason":ban_reason, "EndTime":ban_end_time})


@BanRouter.post("/players/ban", description="Ban a player.")
async def ban_player(userid: str, reason: str, end_date:str=None, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # Sanity table creation in case it got lost or corrupted.
    if end_date == None:
        end_date = "PERMANENT"
    else:
        end_date = end_date.lower()
    try:
        await db.execute(
            "UPDATE players SET is_banned = ?, reason = ?, duration = ? WHERE userid = ?",
            (
                True,
                reason,
                end_date,
                userid,
            ),
        )
        await db.commit()
    except IntegrityError:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_302_FOUND, detail="User is already banned.")
    await db.commit()
    await db.close()
    raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Banned {userid} for {reason}")


@BanRouter.delete("/players/unban", description="Unban an user.")
async def unban_user(userid: str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # Check if exists
    check_is_banned = await db.execute("SELECT is_banned FROM players WHERE userid = ?", (userid,))
    check_is_banned_result = await check_is_banned.fetchone()
    if check_is_banned_result[0] is False:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="User is not banned.")
    else:
        await db.execute("UPDATE players SET is_banned = ?, duration = ? ,reason = ? WHERE userid = ?", (None, None, None, userid,))
        await db.commit()
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail="User is unbanned.")


@BanRouter.get("/teams/view", description="Check if a team is banned.")
async def check_team_ban(team_name: str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    check_is_banned = await db.execute("SELECT reason, duration FROM teams WHERE name = ?", (team_name.lower(),))
    check_is_banned_result = await check_is_banned.fetchone()
    print(check_is_banned_result[0])
    if check_is_banned_result[0] is None:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail="Team is not banned.")
    else:
        if check_is_banned_result[1] == datetime.now().strftime("%d-%m-%Y"):
            await db.execute("UPDATE teams SET is_banned = ?, reason = ?, duration = ? WHERE name = ?", (None, None, None, team_name.lower(),))
            await db.commit()
            await db.close()
            raise HTTPStatus(status_code=status.HTTP_200_OK, detail="Team was banned but it expired.")
        else:
            await db.close()
            raise HTTPStatus(status_code=status.HTTP_403_FORBIDDEN, detail="Team is banned.")


@BanRouter.post("/teams/ban", description="Ban a team.")
async def ban_team(team_name: str, reason: str, end_date:str=None, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # Sanity table creation in case it got lost or corrupted.
    if end_date == None:
        end_date = "PERMANENT"
    else:
        end_date = end_date.lower()


    try:
        await db.execute(
            "UPDATE teams SET is_banned = ?, reason = ?, duration = ? WHERE name = ?",
            (
                True,
                reason,
                end_date,
                team_name.lower()
            ),
        )
        await db.commit()
    except IntegrityError:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_302_FOUND, detail="Team is already banned.")
    await db.commit()
    await db.close()
    raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Banned {team_name} for {reason}")


@BanRouter.delete("/teams/unban", description="Unban an team.")
async def unban_team(team_name: str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # Check if the team is banned:
    check_team_ban_status = await db.execute("SELECT is_banned FROM teams WHERE name = ?", (team_name.lower(),))
    check_team_ban_status_result = await check_team_ban_status.fetchone()
    if check_team_ban_status_result is None:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="Team is not banned.")
    else:
        await db.execute("UPDATE teams SET is_banned = ?, duration = ? , reason = ? WHERE name = ?", (None, None, None,     team_name.lower(),))
        await db.commit()
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Unbanned {team_name.lower()}")



