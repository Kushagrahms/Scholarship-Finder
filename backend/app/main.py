from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import or_, select, and_
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.schemas import ScholarshipResponse
from app.expiration_job import expire_scholarships
from fastapi.middleware.cors import CORSMiddleware

# Standardized education-level dropdown values
EDUCATION_LEVELS = {
    "school": ["school", "secondary", "higher secondary"],
    "undergraduate": ["undergraduate", "bachelor", "b.tech", "b.e."],
    "postgraduate": ["postgraduate", "master", "m.tech", "m.e."],
    "diploma": ["diploma"],
    "phd": ["phd", "doctoral", "doctorate"],
}

# Standardized scholarship-category dropdown values
CATEGORIES = {
    "merit": ["merit"],
    "need": ["need-based", "financial assistance", "means-based"],
    "welfare": ["welfare"],
    "minority": ["minority"],
    "disability": ["disability", "specially abled"],
    "other": [],
}

def active_scholarship_filter():
    today = date.today()

    return and_(
        models.Scholarship.status == "ACTIVE",
        or_(
            models.Scholarship.deadline.is_(None),
            models.Scholarship.deadline >=today,
        ),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create missing tables from SQLAlchemy models
    Base.metadata.create_all(bind=engine)
    expire_scholarships()
    yield
    engine.dispose()


app = FastAPI(
    title="Scholarship Finder API",
    description="Government scholarship discovery and search API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.get("/")
def home():
    return {
        "message": "Scholarship Finder API is running",
        "status": "success",
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    from sqlalchemy import text

    db.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": "connected",
    }


@app.get("/scholarships", response_model=list[ScholarshipResponse])
def list_scholarships(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    education_level: str | None = Query(default=None),
    category: str | None = Query(default=None),
    location: str | None = Query(default=None),
    deadline_before: date | None = Query(default=None),
    deadline_after: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    statement = select(models.Scholarship).where(
        active_scholarship_filter()
    )

    # Education-level filter
    if education_level:
        key = education_level.strip().lower()
        terms = EDUCATION_LEVELS.get(key)

        if terms is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Invalid education level. Choose: school, "
                    "undergraduate, postgraduate, diploma, or phd."
                ),
            )

        statement = statement.where(
            or_(
                *[
                    models.Scholarship.education_level.ilike(
                        f"%{term}%"
                    )
                    for term in terms
                ]
            )
        )

    # Category filter
    if category:
        key = category.strip().lower()
        terms = CATEGORIES.get(key)

        if terms is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Invalid category. Choose: merit, need, welfare, "
                    "minority, disability, or other."
                ),
            )

        if key == "other":
            statement = statement.where(
                models.Scholarship.category.is_(None)
            )
        else:
            statement = statement.where(
                or_(
                    *[
                        models.Scholarship.category.ilike(
                            f"%{term}%"
                        )
                        for term in terms
                    ]
                )
            )

    # Location filter
    if location:
        statement = statement.where(
            models.Scholarship.location.ilike(
                f"%{location.strip()}%"
            )
        )

    # Application deadline filters
    if deadline_before:
        statement = statement.where(
            models.Scholarship.deadline.is_not(None),
            models.Scholarship.deadline <= deadline_before,
        )

    if deadline_after:
        statement = statement.where(
            models.Scholarship.deadline.is_not(None),
            models.Scholarship.deadline >= deadline_after,
        )

    # Pagination and ordering
    statement = (
        statement
        .order_by(models.Scholarship.title)
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all()


@app.get(
    "/scholarships/search",
    response_model=list[ScholarshipResponse],
)
def search_scholarships(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    pattern = f"%{q.strip()}%"

    statement = (
        select(models.Scholarship)
        .where(
            active_scholarship_filter(),
            or_(
                models.Scholarship.title.ilike(pattern),
                models.Scholarship.provider.ilike(pattern),
                models.Scholarship.eligibility.ilike(pattern),
                models.Scholarship.category.ilike(pattern),
            ),
        )
        .order_by(models.Scholarship.title)
        .limit(limit)
    )

    return db.scalars(statement).all()


@app.get(
    "/scholarships/{scholarship_id}",
    response_model=ScholarshipResponse,
)
def get_scholarship(
    scholarship_id: int,
    db: Session = Depends(get_db),
):
    statement = select(models.Scholarship).where(
        models.Scholarship.id == scholarship_id,
        active_scholarship_filter()
    )
    scholarship = db.scalars(statement).first()

    if scholarship is None:
        raise HTTPException(status_code=404, detail="Scholarship not found")
    
    return scholarship
