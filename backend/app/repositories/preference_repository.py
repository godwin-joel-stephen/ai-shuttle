from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.preference import Preference


class PreferenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Preference | None:
        statement = select(Preference).where(
            Preference.user_id == user_id
        )

        return self.db.scalar(statement)