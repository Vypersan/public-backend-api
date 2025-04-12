from Database.connection import connect_db
from fastapi import APIRouter, Depends, status
from fastapi import HTTPException as HTTPStatus
from Auth.auth import verify_token
from aiosqlite import IntegrityError
from fastapi.security import HTTPAuthorizationCredentials


InviteRouter = APIRouter(prefix="/invites", tags=["invites"])


@InviteRouter.post("/create", description="Manage player invites.")
async def invite_user(userid:str, team_name:str, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()
    # Sanity table creation
    await db.execute("CREATE TABLE IF NOT EXISTS invites (userid TEXT, team TEXT)")
    await db.commit()

    # Check if the invite already exists.
    check_is_invited = await db.execute("SELECT team FROM invites WHERE team = ? AND userid = ?", (team_name.lower(), userid,))
    check_is_invited_result = await check_is_invited.fetchone()
    if check_is_invited_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_302_FOUND, detail="User is already invited to this team.")
    else:
        print("Generating new invite")
        await db.execute("INSERT INTO invites VALUES (?, ?)", (userid, team_name.lower(),))
        await db.commit()
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK)
    

@InviteRouter.post("/accept", description="Acept invite")
async def accept_invite(userid:str, team_name:str, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()
    print("got request")

    # Check if the invite is valid:
    check_invite = await db.execute("SELECT * FROM invites WHERE userid = ? AND team = ?", (userid, team_name.lower(), ))
    check_invite_result = await check_invite.fetchone()
    if not check_invite_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="Invite does not exist.")
    print("Updating")
    await db.execute("DELETE FROM invites WHERE userid = ? and team = ?", (userid, team_name.lower(),))
    await db.commit()
    await db.execute("UPDATE players SET team = ?, role = ? WHERE userid = ?", (team_name.lower(), "PLAYER", userid,))
    await db.commit()
    await db.close()
    print("test")
    raise HTTPStatus(status_code=status.HTTP_200_OK)
    


@InviteRouter.get("/view", description="View invites")
async def view_invites(userid:str, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()
    check_invites = await db.execute("SELECT team FROM invites WHERE userid = ?", (userid,))
    check_invites_result = await check_invites.fetchall()
    if len(check_invites_result) < 0:
        print(check_invites)
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="No invites")
    else:
        all_invites = []
        for invite in check_invites_result:
            all_invites.append(invite)
        await db.close()
        return all_invites