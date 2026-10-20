"""Initial schema, explicit and versioned; not dependent on future ORM metadata."""
from alembic import op
import sqlalchemy as sa
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('ramas', sa.Column('id', sa.Integer, primary_key=True), sa.Column('nombre', sa.String(100), nullable=False, unique=True), sa.Column('descripcion', sa.Text, nullable=False))
    op.create_table('dirigentes', sa.Column('id', sa.Integer, primary_key=True), sa.Column('nombre', sa.String(100), nullable=False), sa.Column('usuario', sa.String(120), nullable=False, unique=True), sa.Column('password_hash', sa.String(255), nullable=False), sa.Column('activo', sa.Boolean, nullable=False))
    op.create_table('scouts', sa.Column('id', sa.Integer, primary_key=True), sa.Column('nombres', sa.String(100), nullable=False), sa.Column('apellidos', sa.String(100), nullable=False), sa.Column('rama_id', sa.Integer, sa.ForeignKey('ramas.id', ondelete='RESTRICT'), nullable=False), sa.Column('activo', sa.Boolean, nullable=False))
    op.create_table('actividades', sa.Column('id', sa.Integer, primary_key=True), sa.Column('titulo', sa.String(160), nullable=False), sa.Column('descripcion', sa.Text, nullable=False), sa.Column('lugar', sa.String(160), nullable=False), sa.Column('inicio', sa.DateTime(timezone=True), nullable=False), sa.Column('fin', sa.DateTime(timezone=True), nullable=False), sa.Column('cupo_maximo', sa.Integer, nullable=False), sa.Column('rama_id', sa.Integer, sa.ForeignKey('ramas.id', ondelete='RESTRICT')), sa.Column('estado', sa.String(20), nullable=False), sa.CheckConstraint('inicio < fin', name='fechas_validas'), sa.CheckConstraint('cupo_maximo > 0', name='cupo_positivo'), sa.CheckConstraint("estado IN ('abierta','cerrada','cancelada')", name='estado_actividad'))
    op.create_table('inscripciones', sa.Column('id', sa.Integer, primary_key=True), sa.Column('scout_id', sa.Integer, sa.ForeignKey('scouts.id', ondelete='RESTRICT'), nullable=False), sa.Column('actividad_id', sa.Integer, sa.ForeignKey('actividades.id', ondelete='RESTRICT'), nullable=False), sa.Column('fecha_registro', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column('estado', sa.String(20), nullable=False), sa.UniqueConstraint('scout_id', 'actividad_id', name='scout_actividad_unicos'), sa.CheckConstraint("estado IN ('inscrito','cancelado')", name='estado_inscripcion'))
    for table, fields in [('scouts', ['rama_id']), ('actividades', ['rama_id']), ('inscripciones', ['scout_id', 'actividad_id'])]:
        for field in fields: op.create_index(f'ix_{table}_{field}', table, [field])

def downgrade():
    for table in ['inscripciones', 'actividades', 'scouts', 'dirigentes', 'ramas']: op.drop_table(table)
