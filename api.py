# Importing libraries.

from fastapi import FastAPI, Depends, status
from fastapi import HTTPException as HTTPStatus
from Database.connection import connect_db
from fastapi.security import HTTPAuthorizationCredentials
from aiosqlite import IntegrityError
from Auth.auth import (
    verify_token,
    ACCESS_TOKEN_EXPIRE_DAYS,
    create_access_token,
    get_pass_key,
)
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
import json
from modules import players, teams, invites, queue, matches, bans, publicdata

api = FastAPI(title="Golden OX API", version="0.1", description="The backend api for tournament bots", redoc_url="/docv2", docs_url="/docs", swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"}, contact={"name": "Vyper", "email": "kitsune@yokaigroup.gg"})

# Including extra paths (Routers)
api.include_router(players.PlayerRouter)
api.include_router(teams.teamrouter)
api.include_router(invites.InviteRouter)
api.include_router(queue.QueueRouter)
api.include_router(matches.MatchRouter)
api.include_router(bans.BanRouter)
api.include_router(publicdata.PublicDataRouter)

# Making sure any origin is allowed to interact. Endpoints will remain secured via JWT excluding the publicdata path.
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)


# Used to generate bearer tokens. 

@api.post("/auth", tags=["AUTHORIZATION"], include_in_schema=False)
def login(username: str, passkey: str):

    with open("./Auth/conf.json") as f:
        loaded_json = json.load(f)
        loaded_encryption_key = loaded_json["ENCRYPTION_KEY"]

        if str(passkey) != loaded_encryption_key:
            raise HTTPStatus(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid passkey")

    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


# Add a new developer.
@api.post(
    "/config/dev/add",
    tags=["DEV"],
    description="Add a new developer.",
    include_in_schema=False,
)
async def config_dev_add(
    discordid: int,
    discordname: str,
    passkey: str,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
):
    if passkey != get_pass_key():
        return {"Error": "Invalid Passkey!"}

    else:
        db = await connect_db()
        try:
            await db.execute(
                "INSERT INTO botdevs VALUES (?, ?)",
                (
                    discordid,
                    discordname,
                ),
            )
        except IntegrityError:
            try:
                await db.close()
            except ValueError:
                pass

            raise HTTPStatus(
                status_code=status.HTTP_302_FOUND,
                detail=f"{discordid} is already a dev.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        await db.commit()

        try:
            await db.close()
        except ValueError:
            pass
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Added {discordid} as a dev.")


# Delete a existing developer.


@api.post(
    "/config/dev/delete",
    tags=["DEV"],
    description="Delete a developer.",
    include_in_schema=False,
)
async def config_dev_delete(
    discordid: int,
    passkey: str,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
):
    if passkey != get_pass_key():
        return {"Error": "Invalid Passkey!"}
    else:
        db = await connect_db()
        check_exists = await db.execute(f"SELECT * FROM botdevs WHERE userid = {discordid}")
        check_exists_results = await check_exists.fetchall()
        if not check_exists_results:
            try:
                await db.close()
            except ValueError:
                pass
            raise HTTPStatus(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{discordid} is not a dev.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            await db.execute(
                "DELETE FROM botdevs WHERE userid = ?",
                (discordid,),
            )
        await db.commit()
        try:
            await db.close()
        except ValueError:
            pass
        raise HTTPStatus(
            status_code=status.HTTP_200_OK,
            detail=f"Removed {discordid} as a developer.",
        )


@api.get("/config/dev/view", tags=["DEV"], include_in_schema=False)
async def view_dev(userid: int, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()
    check_exists = await db.execute("SELECT * FROM botdevs WHERE userid = ?", (userid,))
    check_exists_result = await check_exists.fetchone()
    if not check_exists_result:
        try:
            await db.close()
        except ValueError:
            pass
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="This user is not a developer.")
    else:
        try:
            await db.close()
        except ValueError:
            pass
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail="This user is a developer.")
