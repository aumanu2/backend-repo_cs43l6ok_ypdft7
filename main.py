import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents

app = FastAPI(title="LevelUp ATS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"name": "LevelUp ATS API", "status": "ok"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from LevelUp ATS backend!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_name"] = getattr(db, "name", "unknown")
            try:
                collections = db.list_collection_names()
                response["collections"] = collections
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = response["database_name"] or (
        "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    )
    return response


# ---------- Data models (request/response) ----------
class JobIn(BaseModel):
    title: str
    department: str
    location: str = "Remote"
    status: str = "open"
    owner: str
    description: Optional[str] = None


class CandidateIn(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    current_role: Optional[str] = None
    stage: str = "applied"
    resume_url: Optional[str] = None
    skills: List[str] = []
    assessment_scores: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    job_id: Optional[str] = None
    salary_expectation: Optional[str] = None
    avatar_url: Optional[str] = None


class InterviewIn(BaseModel):
    candidate_id: str
    candidate_name: str
    interviewer: str
    time: datetime
    status: str = "scheduled"
    meeting_url: Optional[str] = None


class FeedbackIn(BaseModel):
    interview_id: str
    candidate_id: str
    ratings: Dict[str, int]
    recommendation: str
    comments: Optional[str] = None


class OfferIn(BaseModel):
    candidate_id: str
    candidate_name: str
    role: str
    proposed_salary: str
    status: str = "draft"
    template_name: Optional[str] = None


class OnboardingTaskIn(BaseModel):
    candidate_id: str
    task: str
    assignee: str = "HR"
    status: str = "pending"


class MessageIn(BaseModel):
    sender: str
    receiver: str
    content: str


# ---------- Helper seed endpoints ----------
@app.post("/api/seed", tags=["dev"])
def seed_demo_data():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    # seed jobs
    if db["job"].count_documents({}) == 0:
        sample_jobs = [
            {
                "title": "Senior Frontend Engineer",
                "department": "Engineering",
                "location": "Remote",
                "status": "open",
                "owner": "Alex Johnson",
                "description": "Own the web UI and design systems.",
                "date_posted": datetime.utcnow(),
            },
            {
                "title": "Product Manager",
                "department": "Product",
                "location": "NYC",
                "status": "open",
                "owner": "Priya Sharma",
                "description": "Drive roadmap and outcomes.",
                "date_posted": datetime.utcnow() - timedelta(days=3),
            },
        ]
        for j in sample_jobs:
            create_document("job", j)

    # seed candidates
    if db["candidate"].count_documents({}) == 0:
        sample_candidates = [
            {
                "name": "Jordan Lee",
                "email": "jordan@example.com",
                "current_role": "Frontend Engineer",
                "stage": "interview",
                "skills": ["React", "TypeScript", "Tailwind"],
                "assessment_scores": {"technical": 85, "culture": 78, "communication": 88},
                "avatar_url": "https://i.pravatar.cc/120?img=5",
            },
            {
                "name": "Samira Khan",
                "email": "samira@example.com",
                "current_role": "Product Manager",
                "stage": "applied",
                "skills": ["Roadmapping", "Analytics", "User Research"],
                "assessment_scores": {"technical": 70, "culture": 90, "communication": 92},
                "avatar_url": "https://i.pravatar.cc/120?img=32",
            },
            {
                "name": "Diego Martinez",
                "email": "diego@example.com",
                "current_role": "Backend Engineer",
                "stage": "offer",
                "skills": ["Python", "FastAPI", "MongoDB"],
                "assessment_scores": {"technical": 91, "culture": 84, "communication": 80},
                "avatar_url": "https://i.pravatar.cc/120?img=15",
            },
        ]
        for c in sample_candidates:
            create_document("candidate", c)

    # seed interviews
    if db["interview"].count_documents({}) == 0:
        cand = db["candidate"].find_one({"stage": "interview"})
        if cand:
            create_document(
                "interview",
                {
                    "candidate_id": str(cand.get("_id")),
                    "candidate_name": cand.get("name"),
                    "interviewer": "Alex Johnson",
                    "time": datetime.utcnow() + timedelta(hours=4),
                    "status": "scheduled",
                    "meeting_url": "https://meet.example.com/abc",
                },
            )

    return {"status": "ok"}


# ---------- Metrics & Analytics ----------
@app.get("/api/metrics")
def get_metrics():
    def count(col: str, filt: dict = None):
        if db is None:
            return 0
        return db[col].count_documents(filt or {})

    total_jobs = count("job")
    active_candidates = count("candidate", {"stage": {"$nin": ["rejected", "hired"]}})
    offers_sent = count("offer", {"status": {"$in": ["sent", "accepted", "declined"]}})
    time_to_fill = 24  # demo metric

    return {
        "total_jobs": total_jobs,
        "active_candidates": active_candidates,
        "offers_sent": offers_sent,
        "time_to_fill": time_to_fill,
    }


@app.get("/api/analytics")
def analytics_placeholder():
    return {
        "funnel": {
            "applications": db["candidate"].count_documents({}) if db else 0,
            "interviews": db["interview"].count_documents({}) if db else 0,
            "offers": db["offer"].count_documents({}) if db else 0,
            "hires": db["candidate"].count_documents({"stage": "hired"}) if db else 0,
        },
        "avg_time_per_stage": {
            "applied": 2.5,
            "screening": 3.1,
            "interview": 5.2,
            "offer": 1.3,
        },
        "offer_acceptance_rate": 0.72,
        "top_sources": [
            {"source": "LinkedIn", "count": 48},
            {"source": "Referrals", "count": 31},
            {"source": "Careers Page", "count": 22},
        ],
    }


# ---------- Jobs ----------
@app.get("/api/jobs")
def list_jobs():
    jobs = get_documents("job") if db else []
    return jobs


@app.post("/api/jobs")
def create_job(job: JobIn):
    inserted_id = create_document("job", job.model_dump())
    return {"id": inserted_id}


# ---------- Candidates ----------
@app.get("/api/candidates")
def list_candidates():
    items = get_documents("candidate") if db else []
    return items


@app.post("/api/candidates")
def create_candidate(candidate: CandidateIn):
    inserted_id = create_document("candidate", candidate.model_dump())
    return {"id": inserted_id}


class StageUpdate(BaseModel):
    stage: str


@app.post("/api/candidates/{candidate_id}/stage")
def update_candidate_stage(candidate_id: str, payload: StageUpdate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    from bson import ObjectId

    try:
        db["candidate"].update_one(
            {"_id": ObjectId(candidate_id)}, {"$set": {"stage": payload.stage, "updated_at": datetime.utcnow()}}
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Interviews & Feedback ----------
@app.get("/api/interviews")
def list_interviews():
    items = get_documents("interview") if db else []
    return items


@app.post("/api/interviews")
def create_interview(interview: InterviewIn):
    inserted_id = create_document("interview", interview.model_dump())
    return {"id": inserted_id}


@app.post("/api/interviews/{interview_id}/feedback")
def create_feedback(interview_id: str, feedback: FeedbackIn):
    inserted_id = create_document("feedback", {**feedback.model_dump(), "interview_id": interview_id})
    return {"id": inserted_id}


# ---------- Offers ----------
@app.get("/api/offers")
def list_offers():
    items = get_documents("offer") if db else []
    return items


@app.post("/api/offers")
def create_offer(offer: OfferIn):
    inserted_id = create_document("offer", offer.model_dump())
    return {"id": inserted_id}


class OfferStatus(BaseModel):
    status: str


@app.post("/api/offers/{offer_id}/status")
def update_offer_status(offer_id: str, payload: OfferStatus):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    from bson import ObjectId

    try:
        db["offer"].update_one(
            {"_id": ObjectId(offer_id)}, {"$set": {"status": payload.status, "updated_at": datetime.utcnow()}}
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Onboarding ----------
@app.get("/api/onboarding")
def list_onboarding():
    items = get_documents("onboardingtask") if db else []
    return items


@app.post("/api/onboarding")
def create_onboarding(task: OnboardingTaskIn):
    inserted_id = create_document("onboardingtask", task.model_dump())
    return {"id": inserted_id}


# ---------- Communication Hub ----------
@app.get("/api/messages")
def list_messages():
    messages = get_documents("message") if db else []
    return messages


@app.post("/api/messages")
def create_message(msg: MessageIn):
    inserted_id = create_document("message", msg.model_dump())
    return {"id": inserted_id}


# ---------- Schema endpoint for viewers ----------
@app.get("/schema")
def get_schema_info():
    # Minimal static description; in real-world would introspect models
    return {
        "collections": [
            "job",
            "candidate",
            "interview",
            "feedback",
            "offer",
            "onboardingtask",
            "message",
        ]
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
