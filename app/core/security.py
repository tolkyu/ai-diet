from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.exceptions import raise_unauthorized

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise_unauthorized("Invalid token payload")
        return sub  # type: ignore[return-value]
    except JWTError:
        raise_unauthorized("Could not validate token")
        raise  # unreachable, satisfies type checker


def verify_api_key(api_key: str) -> bool:
    return api_key == settings.admin_api_key


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
