"""Administrative commands, deliberately outside public HTTP registration."""
import argparse
from getpass import getpass
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from .db import SessionLocal
from .models import Dirigente, Rama, Scout, Actividad
from .security import password_hash

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    user = sub.add_parser('create-dirigente')
    user.add_argument('--usuario', required=True)
    user.add_argument('--nombre', required=True)
    sub.add_parser('seed')
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.command == 'create-dirigente':
            if db.scalar(select(Dirigente).where(Dirigente.usuario == args.usuario)):
                parser.error('El usuario ya existe')
            password = getpass('Contraseña (mínimo 12 caracteres): ')
            if len(password) < 12 or password != getpass('Repetir contraseña: '):
                parser.error('Contraseña corta o confirmación distinta')
            db.add(Dirigente(nombre=args.nombre, usuario=args.usuario, password_hash=password_hash.hash(password)))
            db.commit(); print('Dirigente creado')
        else:
            for nombre in ['Exploradores', 'Caminantes', 'Comunidad']:
                rama = db.scalar(select(Rama).where(Rama.nombre == nombre))
                if not rama:
                    rama = Rama(nombre=nombre, descripcion='Rama ficticia de demostración')
                    db.add(rama); db.flush()
                for n in range(1, 3):
                    apellido = f'Ejemplo {nombre}'
                    if not db.scalar(select(Scout.id).where(Scout.nombres == f'Scout {n}', Scout.apellidos == apellido)):
                        db.add(Scout(nombres=f'Scout {n}', apellidos=apellido, rama_id=rama.id))
                titulo = f'Encuentro de {nombre}'
                if not db.scalar(select(Actividad.id).where(Actividad.titulo == titulo)):
                    inicio = datetime.now(timezone.utc) + timedelta(days=7)
                    db.add(Actividad(titulo=titulo, descripcion='Ejemplo sin datos reales', lugar='Parque de demostración', inicio=inicio, fin=inicio + timedelta(hours=3), cupo_maximo=10, rama_id=rama.id))
            db.commit(); print('Datos ficticios disponibles; existentes conservados')
if __name__ == '__main__': main()
