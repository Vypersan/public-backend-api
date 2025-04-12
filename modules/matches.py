from Database.connection import connect_db
from fastapi import APIRouter, Depends, status
from fastapi import HTTPException as HTTPStatus
from Auth.auth import verify_token
from aiosqlite import IntegrityError
from fastapi.security import HTTPAuthorizationCredentials
from random import choice

MatchRouter = APIRouter(prefix="/matches", tags=["matches"])


@MatchRouter.post("/setupmatch", description="Setup a match.")
async def setup_match(match_id:str, team_one:str, team_two:str, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    # sanity table creation:
    await db.execute("CREATE TABLE IF NOT EXISTS matches (match_id TEXT PRIMARY KEY, team_one TEXT, team_two TEXT, score_team_one INTEGER, score_team_two INTEGER)")
    await db.commit()
    await db.execute("CREATE TABLE IF NOT EXISTS scores (team TEXT UNIQUE, wins INTEGER, losses INTEGER, total INTEGER)")
    await db.commit()
    
    # Check if the match already exists
    match_exists = await db.execute("SELECT team_one, team_two FROM matches WHERE match_id = ?", (match_id,))
    match_exists_result = await match_exists.fetchone()
    if match_exists_result:
        existing_team_one = match_exists_result[0]
        existing_team_two = match_exists_result[1]
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_302_FOUND, detail=f"{match_id} already exists, {existing_team_one} VS {existing_team_two}")
    else:
        await db.execute("INSERT INTO matches VALUES (?, ?, ?, ?, ?)", (match_id, team_one.lower(), team_two.lower(), None, None,))
        await db.commit()
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_200_OK, detail=f"Created setup for {match_id}")
    
@MatchRouter.post("/submit", description="Submit a score")
async def submit_match(match_id:str, score_team_one: int, score_team_two:int, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()
    
    # Check if the match is valid:
    check_is_valid = await db.execute("SELECT score_team_one, score_team_two, team_one, team_two FROM matches WHERE match_id = ?", (match_id,))
    check_is_valid_result = await check_is_valid.fetchone()
    if not check_is_valid_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="Match does not exist.")
    else:
        if check_is_valid_result[0] is not None or check_is_valid_result[1] is not None:
            await db.close()
            raise HTTPStatus(status_code=status.HTTP_302_FOUND, detail="A score is already submitted.")
        else:
            await db.execute("UPDATE matches SET score_team_one = ?, score_team_two = ? WHERE match_id = ?", (score_team_one, score_team_two, match_id,))
            await db.commit()
            if score_team_one == 13:
                winner_team = check_is_valid_result[2]
                loser_team = check_is_valid_result[3]
            elif score_team_two == 13:
                winner_team = check_is_valid_result[3]
                loser_team = check_is_valid_result[2]

            get_current_stats_winner = await db.execute("SELECT wins, losses, total FROM scores WHERE team = ?", (winner_team,))
            get_current_stats_loser = await db.execute("SELECT wins, losses, total FROM scores WHERE team = ?", (loser_team,))
            get_current_stats_winner_result = await get_current_stats_winner.fetchone()
            get_current_stats_loser_result = await get_current_stats_loser.fetchone()
            if get_current_stats_winner_result is None:
                await db.execute("INSERT INTO scores VALUES (?, ?, ?, ?)", (winner_team, 1, 0, 1))
                await db.commit()
            else:
                winner_team_wins = get_current_stats_winner_result[0]
                winner_team_total = get_current_stats_loser_result[2]
                new_winner_wins = int(winner_team_wins) + 1
                new_winner_total = int(winner_team_total) + 1
                await db.execute("UPDATE scores SET wins = ?, total = ? WHERE team = ?", (new_winner_wins, new_winner_total, winner_team,))
                await db.commit()
            
            if get_current_stats_loser_result is None:
                await db.execute("INSERT INTO scores VALUES (?, ?, ?, ?)", (loser_team, 0, 1, 1))
                await db.commit()
            else:
                loser_team_losses = get_current_stats_loser_result[1]
                loser_team_total = get_current_stats_loser_result[2]
                new_loser_losses = int(loser_team_losses) + 1
                new_loser_total = int(loser_team_total) + 1
                await db.execute("UPDATE scores SET losses = ?, total = ? WHERE team = ?", (new_loser_losses, new_loser_total, loser_team,))
                await db.commit()

            await db.close()
            raise HTTPStatus(status_code=status.HTTP_200_OK, detail="Submitted match.")


@MatchRouter.get("/view", description="View a match.")
async def view_match(match_id:str, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()

    check_exists  = await db.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,))
    check_exists_result = await check_exists.fetchone()
    if not check_exists_result:
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="Match does not exist.")
    else:
        teams = await db.execute("SELECT team_one, team_two, score_team_one, score_team_two FROM matches WHERE match_id = ?", (match_id,))
        teams_result = await teams.fetchone()
        team_one = teams_result[0]
        team_two = teams_result[1]
        score_team_one  = teams_result[2]
        score_team_two = teams_result[3]

        await db.close()
        return {"team_one":team_one, "team_two":team_two, "score_team_one":score_team_one, "score_team_two":score_team_two}
    

@MatchRouter.get("/viewstats", description="View the match stats for the team.")
async def view_team_match_stats(team_name:str, credentials : HTTPAuthorizationCredentials = Depends(verify_token)):
    db = await connect_db()
    check_exists = await db.execute("SELECT wins, losses, total FROM scores WHERE team = ?", (team_name.lower(),))
    check_exists_result = await check_exists.fetchone()
    if not check_exists_result:
        print(check_exists_result)
        await db.close()
        raise HTTPStatus(status_code=status.HTTP_404_NOT_FOUND, detail="Team has no matches yet.")
    else:
        wins = check_exists_result[0]
        losses = check_exists_result[1]
        total = check_exists_result[2]
        await db.close()
        return {"wins":wins, "losses":losses, "total":total}




