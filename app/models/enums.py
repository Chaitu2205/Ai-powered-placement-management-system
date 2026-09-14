"""
Shared enums used across ORM models and Pydantic schemas.

Kept in one place so the same enum can be reused by both layers without
duplication or drift.
"""
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STUDENT = "student"
    RECRUITER = "recruiter"


class JobType(str, enum.Enum):
    FULL_TIME = "full_time"
    INTERNSHIP = "internship"


class JobStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class DriveStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    COMPLETED = "completed"


class ApplicationStatus(str, enum.Enum):
    APPLIED = "APPLIED"
    SHORTLISTED = "SHORTLISTED"
    ONLINE_TEST = "ONLINE_TEST"
    TECHNICAL_INTERVIEW = "TECHNICAL_INTERVIEW"
    HR_INTERVIEW = "HR_INTERVIEW"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"


class ResumeFileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"


class PlacementStatus(str, enum.Enum):
    NOT_PLACED = "not_placed"
    SHORTLISTED = "shortlisted"
    SELECTED = "selected"


class ProficiencyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class SkillSource(str, enum.Enum):
    MANUAL = "manual"
    RESUME_EXTRACTED = "resume_extracted"


class InterviewType(str, enum.Enum):
    TECHNICAL = "technical"
    HR = "hr"
    BEHAVIORAL = "behavioral"


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ExperienceLevel(str, enum.Enum):
    FRESHER = "fresher"
    EXPERIENCED = "experienced"


class SessionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    STATUS_CHANGE = "status_change"
