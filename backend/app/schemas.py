from datetime import datetime
from typing import Literal, Annotated
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator, StringConstraints

Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
class DTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')
class RamaIn(DTO):
    nombre: Nombre
    descripcion: str = Field(default='', max_length=2000)
class RamaOut(RamaIn):
    id: int
class ScoutIn(DTO):
    nombres: Nombre
    apellidos: Nombre
    rama_id: int = Field(gt=0)
    activo: bool = True
class ScoutOut(ScoutIn):
    id: int
class ActividadIn(DTO):
    titulo: Texto
    descripcion: str = Field(default='', max_length=4000)
    lugar: Texto
    inicio: AwareDatetime
    fin: AwareDatetime
    cupo_maximo: int = Field(gt=0, le=10000)
    rama_id: int | None = Field(default=None, gt=0)
    estado: Literal['abierta', 'cerrada', 'cancelada'] = 'abierta'
    @model_validator(mode='after')
    def fechas(self):
        if self.inicio >= self.fin:
            raise ValueError('El inicio debe ser anterior al fin')
        return self
class ActividadOut(ActividadIn):
    id: int
    inscritos: int
    cupos_disponibles: int
class InscripcionIn(DTO):
    scout_id: int = Field(gt=0)
    actividad_id: int = Field(gt=0)
    estado: Literal['inscrito', 'cancelado'] = 'inscrito'
class InscripcionUpdate(DTO):
    estado: Literal['inscrito', 'cancelado']
class InscripcionOut(InscripcionIn):
    id: int
    fecha_registro: datetime
class DirigenteOut(DTO):
    id: int
    nombre: str
    usuario: str
