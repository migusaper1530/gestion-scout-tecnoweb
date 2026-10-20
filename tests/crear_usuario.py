"""Read test credentials via stdin; never print password or token."""
import json, sys
from app.db import SessionLocal
from app.models import Dirigente
from app.security import password_hash
payload=json.load(sys.stdin)
with SessionLocal() as db:
    db.add(Dirigente(nombre='Dirigente de prueba ficticio',usuario=payload['usuario'],password_hash=password_hash.hash(payload['password'])))
    db.commit()
print('Cuenta aislada de prueba creada')
