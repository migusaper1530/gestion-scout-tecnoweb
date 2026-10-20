"""Generate local secrets without overwriting an existing environment."""
from pathlib import Path
import secrets
import os
root = Path(__file__).resolve().parents[1]
p = root / '.env'
content = (root / '.env.example').read_text().replace('POSTGRES_PASSWORD=\n', f'POSTGRES_PASSWORD={secrets.token_hex(24)}\n').replace('JWT_SECRET=\n', f'JWT_SECRET={secrets.token_hex(32)}\n')
fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as f: f.write(content)
print('.env creado con permisos 600. No compartir ni subir a Git.')
