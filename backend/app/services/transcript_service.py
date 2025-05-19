from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.domain.models.transcript import Transcript
from app.domain.schemas.transcript import TranscriptCreate, TranscriptUpdate
from app.repositories.transcript_repository import TranscriptRepository


class TranscriptService:
    def __init__(self, db: Session):
        self.transcript_repository = TranscriptRepository(db)

    def get(self, id: Any) -> Optional[Transcript]:
        return self.transcript_repository.get(id)

    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Transcript]:
        return self.transcript_repository.get_multi(skip=skip, limit=limit)

    def create(self, obj_in: TranscriptCreate) -> Transcript:
        return self.transcript_repository.create(obj_in=obj_in)

    def update(
        self, id: int, obj_in: Union[TranscriptUpdate, Dict[str, Any]]
    ) -> Transcript:
        transcript = self.get(id)
        return self.transcript_repository.update(db_obj=transcript, obj_in=obj_in)

    def remove(self, id: int) -> Transcript:
        return self.transcript_repository.remove(id)
