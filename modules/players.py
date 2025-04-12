from Database.connection import connect_db
from fastapi import APIRouter, Depends, status
from fastapi import HTTPException as HTTPStatus
from Auth.auth import verify_token
from aiosqlite import IntegrityError
from fastapi.security import HTTPAuthorizationCredentials


PlayerRouter = APIRouter(prefix="/players", tags=["players"])

@PlayerRouter.post('/register', description="Register an user.")
async def register_player(userid:str, uid:int, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    await db.execute("CREATE TABLE IF NOT EXISTS players (userid TEXT PRIMARY KEY, gameid UNIQUE, team TEXT, role TEXT, is_banned TEXT, reason TEXT, duration TEXT)")
    await db.commit()
    try:
        await db.execute("INSERT INTO players VALUES (?, ?, ?, ?,?, ?, ?)", (userid, uid, None, None, None, None, None))
        await db.commit()
    except IntegrityError:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_302_FOUND, detail="A user is already registered with that userid or uid.")
    await db.commit()
    await db.close()
    raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Registered {userid} + {uid}")


@PlayerRouter.get("/view", description="view information about an user.")
async def view_player(userid:str, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()
    user_info_request = await db.execute("SELECT userid, gameid, team, role, is_banned, reason, duration FROM players WHERE userid = ?", (userid,))
    user_info_result = await user_info_request.fetchone()
    if not user_info_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="User is not registered.")
    else:
        uid = user_info_result[1]
        team = user_info_result[2]
        role = user_info_result[3]
        is_banned = user_info_result[4]
        ban_reason = user_info_result[5]
        ban_duration = user_info_result[6]
        await db.close()
        return {"userid":userid, "uid":uid, "team":team, "role":role, "ban_status":is_banned, "ban_reason":ban_reason, "ban_duration":ban_duration}
    

@PlayerRouter.delete("/delete", description="Delete a registered user.")
async def delete_user(userid:str, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()
    user_info_request = await db.execute("SELECT userid, uid, team, role FROM players WHERE userid = ?", (userid,))
    user_info_result = await user_info_request.fetchone()
    if not user_info_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="User is not registered.")
    else:
        await db.execute("DELETE FROM players WHERE userid = ?", (userid,))
        await db.commit()
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Deleted  {userid}")
    