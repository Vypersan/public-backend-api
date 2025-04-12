from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import HTTPException
from fastapi import Depends
from fastapi import status
from jwt.exceptions import PyJWTError
import jwt
from typing import Optional
from datetime import datetime, timedelta
import json

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 365


security = HTTPBearer()


# Function to create a new JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    with open("./Auth/conf.json") as f:
        loaded_json = json.load(f)
        loaded_encryption_key = loaded_json["ENCRYPTION_KEY"]
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, loaded_encryption_key, algorithm=ALGORITHM)
    return encoded_jwt


# Function to verify the JWT token
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        with open("./Auth/conf.json") as f:
            loaded_json = json.load(f)
            loaded_encryption_key = loaded_json["ENCRYPTION_KEY"]
        payload = jwt.decode(token, loaded_encryption_key, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_pass_key():
    with open("./Auth/conf.json") as f:
        loaded_json = json.load(f)
        loaded_passkey = loaded_json["passkey"]
        return loaded_passkey
