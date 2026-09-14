"""initial schema - all Phase 1 tables

Revision ID: 0001
Revises:
Create Date: 2026-09-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------- #
    # Tables with no FK dependencies
    # ---------------------------------------------------------------- #
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_departments_name"),
        sa.UniqueConstraint("code", name="uq_departments_code"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.UniqueConstraint("name", name="uq_skills_name"),
    )
    op.create_index("ix_skills_name", "skills", ["name"])

    op.create_table(
        "placement_drives",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("eligible_departments", sa.String(255), nullable=True),
        sa.Column("min_cgpa", sa.Numeric(3, 2), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="upcoming"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ---------------------------------------------------------------- #
    # students / recruiters (depend on users, departments)
    # ---------------------------------------------------------------- #
    op.create_table(
        "students",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "department_id",
            sa.Integer,
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # current_resume_id -> resumes.id is added later via ALTER TABLE
        # (see bottom of this migration) because resumes.student_id -> students.id
        # creates a circular dependency between the two tables.
        sa.Column("current_resume_id", sa.Integer, nullable=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("batch_year", sa.Integer, nullable=True),
        sa.Column("cgpa", sa.Numeric(3, 2), nullable=True),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("placement_status", sa.String(20), nullable=False, server_default="not_placed"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_students_user_id"),
    )

    op.create_table(
        "recruiters",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("designation", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_recruiters_user_id"),
    )

    # ---------------------------------------------------------------- #
    # companies (depends on recruiters) / jobs (depends on companies, drives, users)
    # ---------------------------------------------------------------- #
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "recruiter_id",
            sa.Integer,
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("logo_url", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_companies_name", "companies", ["name"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "placement_drive_id",
            sa.Integer,
            sa.ForeignKey("placement_drives.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("job_type", sa.String(20), nullable=False, server_default="full_time"),
        sa.Column("location", sa.String(150), nullable=True),
        sa.Column("package_lpa", sa.Numeric(6, 2), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])
    op.create_index("ix_jobs_title", "jobs", ["title"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    # ---------------------------------------------------------------- #
    # resumes (depends on students) / resume_analysis (depends on resumes)
    # ---------------------------------------------------------------- #
    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("uploaded_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resumes_student_id", "resumes", ["student_id"])

    op.create_table(
        "resume_analysis",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("resume_id", sa.Integer, sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("extracted_name", sa.String(150), nullable=True),
        sa.Column("extracted_email", sa.String(255), nullable=True),
        sa.Column("extracted_phone", sa.String(20), nullable=True),
        sa.Column("education_json", sa.JSON, nullable=True),
        sa.Column("projects_json", sa.JSON, nullable=True),
        sa.Column("internships_json", sa.JSON, nullable=True),
        sa.Column("certifications_json", sa.JSON, nullable=True),
        sa.Column("experience_json", sa.JSON, nullable=True),
        sa.Column("overall_score", sa.Integer, nullable=True),
        sa.Column("strengths_json", sa.JSON, nullable=True),
        sa.Column("weaknesses_json", sa.JSON, nullable=True),
        sa.Column("missing_skills_json", sa.JSON, nullable=True),
        sa.Column("suggestions_json", sa.JSON, nullable=True),
        sa.Column("ats_keywords_json", sa.JSON, nullable=True),
        sa.Column("summary_text", sa.Text, nullable=True),
        sa.Column("analyzed_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resume_analysis_resume_id", "resume_analysis", ["resume_id"])

    # ---------------------------------------------------------------- #
    # applications (depends on students, jobs, resumes)
    # ---------------------------------------------------------------- #
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.Integer, sa.ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="APPLIED"),
        sa.Column("match_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_id", "job_id", name="uq_student_job_application"),
    )
    op.create_index("ix_applications_student_id", "applications", ["student_id"])
    op.create_index("ix_applications_job_id", "applications", ["job_id"])
    op.create_index("ix_applications_status", "applications", ["status"])

    # ---------------------------------------------------------------- #
    # student_skills / job_skills (many-to-many association tables)
    # ---------------------------------------------------------------- #
    op.create_table(
        "student_skills",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", sa.Integer, sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("proficiency", sa.String(20), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),
    )
    op.create_index("ix_student_skills_student_id", "student_skills", ["student_id"])
    op.create_index("ix_student_skills_skill_id", "student_skills", ["skill_id"])

    op.create_table(
        "job_skills",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", sa.Integer, sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("job_id", "skill_id", name="uq_job_skill"),
    )
    op.create_index("ix_job_skills_job_id", "job_skills", ["job_id"])
    op.create_index("ix_job_skills_skill_id", "job_skills", ["skill_id"])

    # ---------------------------------------------------------------- #
    # interview_sessions / interview_questions / interview_answers
    # ---------------------------------------------------------------- #
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("interview_type", sa.String(20), nullable=False),
        sa.Column("difficulty", sa.String(10), nullable=False),
        sa.Column("experience_level", sa.String(15), nullable=False),
        sa.Column("status", sa.String(15), nullable=False, server_default="in_progress"),
        sa.Column("overall_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_interview_sessions_student_id", "interview_sessions", ["student_id"])

    op.create_table(
        "interview_questions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.Integer,
            sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_interview_questions_session_id", "interview_questions", ["session_id"])

    op.create_table(
        "interview_answers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "question_id",
            sa.Integer,
            sa.ForeignKey("interview_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("answer_text", sa.Text, nullable=False),
        sa.Column("score", sa.Numeric(4, 2), nullable=True),
        sa.Column("relevance_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("correctness_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("completeness_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("communication_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("good_points_json", sa.JSON, nullable=True),
        sa.Column("improvements_json", sa.JSON, nullable=True),
        sa.Column("suggested_answer", sa.Text, nullable=True),
        sa.Column("submitted_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("question_id", name="uq_interview_answers_question_id"),
    )

    # ---------------------------------------------------------------- #
    # notifications / audit_logs
    # ---------------------------------------------------------------- #
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("details_json", sa.JSON, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])

    # ---------------------------------------------------------------- #
    # Circular FK: students.current_resume_id -> resumes.id
    # Added last, now that both tables exist.
    # ---------------------------------------------------------------- #
    op.create_foreign_key(
        "fk_students_current_resume",
        "students",
        "resumes",
        ["current_resume_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_students_current_resume", "students", type_="foreignkey")
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("interview_answers")
    op.drop_table("interview_questions")
    op.drop_table("interview_sessions")
    op.drop_table("job_skills")
    op.drop_table("student_skills")
    op.drop_table("applications")
    op.drop_table("resume_analysis")
    op.drop_table("resumes")
    op.drop_table("jobs")
    op.drop_table("companies")
    op.drop_table("recruiters")
    op.drop_table("students")
    op.drop_table("placement_drives")
    op.drop_table("skills")
    op.drop_table("users")
    op.drop_table("departments")
