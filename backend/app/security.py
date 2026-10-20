from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .db import get_db
from .config import settings
from .models import Dirigente

password_hash = PasswordHash.recommended()
# Used to equalize unknown-user and wrong-password verification work.
dummy_hash = password_hash.hash('dummy-value-not-an-account')
oauth2 = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')

def token_for(user_id, minutes=None):
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub': str(user_id), 'iat': now, 'exp': now + timedelta(minutes=minutes if minutes is not None else settings.token_minutes)}, settings.jwt_secret, algorithm='HS256')

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=['HS256'], options={'require': ['sub', 'exp', 'iat']})
        user = db.get(Dirigente, int(data['sub']))
        if not user or not user.activo: raise ValueError()
        return user
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(401, 'Sesión inválida o vencida', headers={'WWW-Authenticate': 'Bearer'})
