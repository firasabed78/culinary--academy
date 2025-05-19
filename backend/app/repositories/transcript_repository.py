from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.domain.models.transcript import Transcript
from app.domain.schemas.transcript import TranscriptCreate, TranscriptUpdate


class TranscriptRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: Any) -> Optional[Transcript]:
        return self.db.query(Transcript).filter(Transcript.id == id).first()

    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Transcript]:
        return self.db.query(Transcript).offset(skip).limit(limit).all()

    def create(self, obj_in: TranscriptCreate) -> Transcript:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = Transcript(**obj_in_data)  # type: ignore
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db_obj: Transcript,
        obj_in: Union[TranscriptUpdate, Dict[str, Any]],
    ) -> Transcript:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove(self, id: int) -> Transcript:
        obj = self.db.query(Transcript).get(id)
        self.db.delete(obj)
        self.db.commit()
        return obj
