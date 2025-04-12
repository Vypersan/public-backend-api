import aiosqlite
import sqlite3


async def connect_db():
    """Connect to the database"""
    return await aiosqlite.connect("./database.db")


def log_converter(type):
    global newtype
    if type == 1:
        newtype = "warn"
        return newtype
    elif type == 2:
        newtype = "mute"
        return newtype
    elif type == 3:
        newtype = "unmute"
        return newtype
    elif type == 4:
        newtype = "kick"
        return newtype
    elif type == 5:
        newtype = "softban"
        return newtype
    elif type == 6:
        newtype = "ban"
        return newtype
    elif type == 7:
        newtype = "unban"
        return newtype


async def log_counter():
    db = await connect_db()
    counter = await db.execute("SELECT COUNT (*) FROM moderationLogs")
    global new_case
    result = await counter.fetchone()
    new_case = result[0] + 1
    try:
        await db.close()
    except ValueError:
        pass
    return new_case
