"""
Database Schemas for LevelUp ATS

Each Pydantic model represents a collection in MongoDB. The collection name is the
lowercased class name (e.g., Job -> "job").
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# Core domain models

class Job(BaseModel):
    title: str = Field(..., description="Job title")
    department: str = Field(..., description="Department or team")
    location: str = Field("Remote", description="Location")
    status: Literal["draft", "open", "paused", "closed"] = Field("open")
    owner: str = Field(..., description="Hiring manager/Owner")
    description: Optional[str] = Field(None, description="JD markdown or HTML")
    applicants_count: int = Field(0, ge=0)
    date_posted: Optional[datetime] = None

class Candidate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    current_role: Optional[str] = None
    stage: Literal["applied", "screening", "interview", "offer", "hired", "rejected"] = "applied"
    resume_url: Optional[str] = None
    skills: List[str] = []
    assessment_scores: Optional[dict] = Field(default_factory=dict)
    notes: Optional[str] = None
    job_id: Optional[str] = None
    salary_expectation: Optional[str] = None
    avatar_url: Optional[str] = None

class Interview(BaseModel):
    candidate_id: str
    candidate_name: str
    interviewer: str
    time: datetime
    status: Literal["scheduled", "completed", "cancelled"] = "scheduled"
    meeting_url: Optional[str] = None

class Feedback(BaseModel):
    interview_id: str
    candidate_id: str
    ratings: dict = Field(default_factory=lambda: {
        "technical": 0,
        "culture": 0,
        "communication": 0
    })
    recommendation: Literal["proceed", "reject", "hold"] = "hold"
    comments: Optional[str] = None

class Offer(BaseModel):
    candidate_id: str
    candidate_name: str
    role: str
    proposed_salary: str
    status: Literal["draft", "routing", "approved", "sent", "accepted", "declined"] = "draft"
    template_name: Optional[str] = None

class OnboardingTask(BaseModel):
    candidate_id: str
    task: str
    assignee: Literal["HR", "IT", "Admin"] = "HR"
    status: Literal["pending", "in_progress", "done"] = "pending"

class Message(BaseModel):
    sender: str
    receiver: str
    content: str
    timestamp: Optional[datetime] = None

# These schemas will be used by the database viewer and validators.
