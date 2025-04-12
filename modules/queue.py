from Database.connection import connect_db
from fastapi import APIRouter, Depends, status
from fastapi import HTTPException as HTTPStatus
from Auth.auth import verify_token
from aiosqlite import IntegrityError
from fastapi.security import HTTPAuthorizationCredentials
from random import choice

QueueRouter = APIRouter(prefix="/queue", tags=["queue"])


@QueueRouter.post("/join", description="Join the queue")
async def join_queue(team_name:str, region:str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # Sanity table creation in case it got lost or does not exist yet.
    await db.execute("CREATE TABLE IF NOT EXISTS queue (team TEXT UNIQUE, region TEXT)")
    await db.commit()
    try:
        await db.execute("INSERT INTO queue VALUES (?, ?)", (team_name.lower(), region,))
        await db.commit()
    except IntegrityError:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_302_FOUND, detail="Team is already in queue.")
    await db.close()
    raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Added {team_name.lower()} to the queue for {region}")

@QueueRouter.post("/leave", description="Leave the queue")
async def leave_queue(team_name:str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()
    check_is_in_queue = await db.execute("SELECT * FROM queue WHERE team = ?", (team_name.lower(),))
    check_is_in_queue_result = await check_is_in_queue.fetchone()
    if not check_is_in_queue_result:
        await db.close()
        return HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="Team is not in the queue.")
    else:
        await db.execute("DELETE FROM queue WHERE team = ?", (team_name.lower(),))
        await db.commit()
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail = f"{team_name} left the queue.")


@QueueRouter.post("/widen", description="Widen the search range for a team.")
async def widen_range(team_name:str, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # Check if the team is in the quwu
    check_is_in_queue = await db.execute("SELECT region FROM queue WHERE team = ?", (team_name.lower(),))
    check_is_in_queue_result = await check_is_in_queue.fetchone()
    if not check_is_in_queue_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="This team is not in the queue.")
    else:
        await db.execute("UPDATE queue SET region = ? WHERE team = ?", ("ALL", team_name.lower(),))
        await db.commit()
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Widened the search for {team_name}")

@QueueRouter.get("/findmatch", description="Find a match for two teams at a time.")
async def findmatch(team_name:str, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # Check if the team is in the queue to begin with.
    check_is_in_queue = await db.execute("SELECT region FROM queue WHERE team = ?", (team_name.lower(),))
    check_is_in_queue_result = await check_is_in_queue.fetchone()
    if not check_is_in_queue_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="This team is not in the queue.")
    else:
        possible_matches = []
        region = str(check_is_in_queue_result[0])
        if region == "ALL":
            all_teams = await db.execute("SELECT team FROM queue")
            all_teams_result = await all_teams.fetchall()
        else:
            all_teams = await db.execute("SELECT team FROM queue WHERE region = ?", (region,))
            all_teams_result = await all_teams.fetchall()
        
        for team in all_teams_result:
            if str(team[0]).lower() == team_name.lower():
                pass
            else:
                possible_matches.append(team)
        
        if len(possible_matches) < 1:
            await db.close()
            raise HTTPStatus(status_code=status.HTTP_412_PRECONDITION_FAILED, detail="Not enough teams in the queue.")
        team_two = choice(possible_matches)
        await db.execute("DELETE FROM queue WHERE team = ?", (team_name,))
        await db.commit()
        await db.execute("DELETE FROM queue WHERE team = ?", (team_two[0],))
        await db.commit()
        await db.close()
        match_found = {"team_one":team_name, "team_two":team_two}
        return match_found
