import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pwdlib import PasswordHash

from config import settings


basic_auth = HTTPBasic()
password_hasher = PasswordHash.recommended()


def require_admin(
    credentials: Annotated[HTTPBasicCredentials, Depends(basic_auth)],
) -> str:
    username_matches = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        settings.admin_username.encode("utf-8"),
    )

    password_matches = password_hasher.verify(
        credentials.password,
        settings.admin_password_hash.get_secret_value(),
    )

    if not (username_matches and password_matches):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return settings.admin_username