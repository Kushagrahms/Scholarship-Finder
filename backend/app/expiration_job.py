
from datetime import date

from sqlalchemy import update

from app.database import SessionLocal
from app.models import Scholarship


def expire_scholarships() -> int:
    today = date.today()

    with SessionLocal() as db:
        result = db.execute(
            update(Scholarship)
            .where(
                Scholarship.status == "ACTIVE",
                Scholarship.deadline.is_not(None),
                Scholarship.deadline < today,
            )
            .values(status="EXPIRED")
        )

        expired_count = result.rowcount or 0
        db.commit()

    print(f"Expired {expired_count} scholarships.")
    return expired_count
