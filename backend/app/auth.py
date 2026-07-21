from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Header, HTTPException
from pydantic import BaseModel, ConfigDict


class AuthModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GoogleLoginRequest(AuthModel):
    accessToken: str


class AuthUser(AuthModel):
    id: str
    email: str
    name: str | None = None
    picture: str | None = None
    role: str = "user"


class AuthSession(AuthModel):
    token: str
    user: AuthUser


def _google_client_id() -> str:
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()


def _jwt_secret() -> str:
    return os.getenv("AUTH_JWT_SECRET", "").strip()


def auth_config(database_configured: bool) -> dict[str, Any]:
    client_id = _google_client_id()
    enabled = bool(client_id and _jwt_secret() and database_configured)
    return {
        "googleClientId": client_id,
        "googleEnabled": enabled,
        "persistentExperimentsEnabled": enabled,
        "anonymousExperimentsEnabled": True,
    }


def _role_for(email: str) -> str:
    admins = {
        value.strip().lower()
        for value in os.getenv("EXPERIMENT_ADMIN_EMAILS", "").split(",")
        if value.strip()
    }
    return "admin" if email.lower() in admins else "user"


def verify_google_access_token(access_token: str) -> AuthUser:
    client_id = _google_client_id()
    if not client_id:
        raise HTTPException(status_code=503, detail="Google login is not configured")
    try:
        with httpx.Client(timeout=10.0) as client:
            token_info = client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"access_token": access_token},
            )
            token_info.raise_for_status()
            claims = token_info.json()
            user_info = client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_info.raise_for_status()
            profile = user_info.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(status_code=401, detail="Google token could not be verified") from error

    if claims.get("aud") != client_id:
        raise HTTPException(status_code=401, detail="Google token audience is not authorized")
    email = str(profile.get("email") or claims.get("email") or "").lower()
    subject = str(profile.get("sub") or claims.get("sub") or "")
    if not email or not subject or str(profile.get("email_verified", "true")).lower() == "false":
        raise HTTPException(status_code=401, detail="A verified Google email is required")
    return AuthUser(
        id=subject,
        email=email,
        name=profile.get("name"),
        picture=profile.get("picture"),
        role=_role_for(email),
    )


def issue_session(user: AuthUser) -> AuthSession:
    secret = _jwt_secret()
    if not secret:
        raise HTTPException(status_code=503, detail="Persistent sessions are not configured")
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "role": user.role,
            "iat": now,
            "exp": now + timedelta(days=7),
            "iss": "colonymind-experiment-studio",
        },
        secret,
        algorithm="HS256",
    )
    return AuthSession(token=token, user=user)


def optional_user(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> AuthUser | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    secret = _jwt_secret()
    if not secret:
        raise HTTPException(status_code=503, detail="Persistent sessions are not configured")
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer="colonymind-experiment-studio",
        )
    except jwt.PyJWTError as error:
        raise HTTPException(status_code=401, detail="Session expired or invalid") from error
    return AuthUser(
        id=str(claims["sub"]),
        email=str(claims["email"]),
        name=claims.get("name"),
        picture=claims.get("picture"),
        role=str(claims.get("role", "user")),
    )
