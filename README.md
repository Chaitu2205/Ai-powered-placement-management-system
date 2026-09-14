# Ai-powered-placement-management-system
🤖 AI-Powered Placement Management System

A full-stack placement management platform designed to connect students, recruiters, and administrators in one system, with resume intelligence, job matching, interview assistance, and analytics.

📌 Overview

The AI-Powered Placement Management System is a web-based application developed to simplify and modernize the college placement process.

Instead of managing students, recruiters, jobs, applications, resumes, interviews, and placement statistics separately, the system brings these activities together through a single platform.

The project follows a role-based architecture with three main users:

🎓 Student — manage profile, resume, skills, jobs, applications, and interviews

🏢 Recruiter — manage company information, jobs, applicants, and placement drives

🛡️ Admin — manage users and monitor overall placement activities

AI capabilities are integrated through the backend to support resume analysis and interview-related features.

✨ Key Features

🎓 Student Module

Student registration and login

Profile management

Resume upload and processing

Skill management

Job browsing

Job recommendations

Job matching

Application tracking

Interview preparation

Interview answer evaluation

Notifications

Placement analytics

🏢 Recruiter Module

Recruiter authentication

Company management

Job creation and management

Placement drive management

Applicant management

Candidate/application tracking

Recruiter analytics

🛡️ Admin Module

Role-based access

User management

System-level monitoring

Placement analytics

Administrative dashboard

🤖 AI & Intelligent Features

Resume text extraction

Resume analysis

Detected skill information

Job matching and recommendations

Interview question generation

Interview answer evaluation

📊 Analytics

Role-specific dashboards provide useful placement insights for:

Students

Recruiters

Administrators

🏗️ System Architecture

                    ┌──────────────────────┐
                    │        Users         │
                    │ Student / Recruiter  │
                    │       / Admin        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    React Frontend    │
                    │ JavaScript / Vite     │
                    │    Tailwind CSS       │
                    └──────────┬───────────┘
                               │ REST API
                               ▼
                    ┌──────────────────────┐
                    │    FastAPI Backend   │
                    │   Business Logic     │
                    │ Authentication / RBAC│
                    └───────┬───────┬──────┘
                            │       │
                 ┌──────────┘       └──────────┐
                 ▼                             ▼
       ┌──────────────────┐          ┌──────────────────┐
       │   MySQL Database │          │    AI Services   │
       │                  │          │  Resume /        │
       │ Placement Data   │          │  Interview AI    │
       └──────────────────┘          └──────────────────┘

🛠️ Technology Stack

Backend

Python 3.12

FastAPI

SQLAlchemy 2.x

Alembic

Pydantic v2

MySQL

PyMySQL

Authentication & Security

JWT authentication

Password hashing with bcrypt

Role-Based Access Control (RBAC)

CORS configuration

Environment-based configuration

Frontend

React

JavaScript

Vite

Tailwind CSS

Axios

React Router

Recharts / Chart.js

AI & Resume Processing

LLM API integration through the backend

PyMuPDF for PDF resume processing

python-docx for DOCX resume processing

🗄️ Database Design

The Phase 1 architecture defines 18 database tables covering the major areas of the placement workflow.

Core entities include:

Users

Students

Recruiters

Companies

Jobs

Placement Drives

Applications

Resumes

Resume Analyses

Interviews

Interview Questions

Interview Answers

Notifications

Skills

Student Skills

Job Skills

Placements

Supporting / audit data

The database is designed to keep major entities separate and connect them through relationships.

📁 Project Structure

backend_phase4/
│
├── app/
│   ├── api/              # API routes
│   ├── models/           # SQLAlchemy database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── ai/               # AI integration
│   ├── config/           # Application settings
│   └── main.py           # FastAPI entry point
│
├── alembic/              # Database migrations
├── tests/                # Backend tests
├── uploads/              # Resume uploads
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── .env.example
├── requirements.txt
└── README.md

🔐 Authentication Flow

The application uses JWT-based authentication.

User
  │
  ▼
Register / Login
  │
  ▼
Password Hashing
  │
  ▼
JWT Access Token
  │
  ▼
Authenticated API Requests
  │
  ▼
Role-Based Authorization
  │
  ├── Student
  ├── Recruiter
  └── Admin

🔌 Main API Areas

The backend REST API is organized around the application's major workflows.

Area

Purpose

Authentication

Registration, login and current-user information

Students

Profiles, resumes, skills and applications

Recruiters

Companies, jobs, applicants and drives

Admin

User management and system oversight

Resumes & AI

Upload, parsing, analysis and matching

Interviews

Question generation and answer evaluation

Analytics

Student, recruiter and admin dashboards

Notifications

User notifications and read status

🚀 Running the Project Locally

1. Clone the repository

git clone https://github.com/YOUR-USERNAME/ai-powered-placement-management-system.git
cd ai-powered-placement-management-system

2. Create a Python virtual environment

python -m venv venv

Activate it on Windows:

.\venv\Scripts\Activate.ps1

3. Install backend dependencies

pip install -r requirements.txt

4. Configure environment variables

Create a .env file based on .env.example.

Example:

APP_ENV=development
DEBUG=True

DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/placement_management

JWT_SECRET_KEY=YOUR_SECRET_KEY
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

AI_API_KEY=YOUR_AI_API_KEY
AI_MODEL_NAME=YOUR_AI_MODEL

RESUME_UPLOAD_DIR=uploads/resumes
MAX_RESUME_SIZE_MB=5

⚠️ Never commit your real .env file, passwords, JWT secrets, or API keys to GitHub.

5. Run database migrations

alembic upgrade head

6. Start the backend

python -m uvicorn app.main:app --reload

Backend:

http://127.0.0.1:8000

7. Start the frontend

Open another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:5173

🧪 Testing

The backend has been tested with the project's automated test suite.

Current verification:

120 tests passed

Run the test suite with:

pytest

For frontend production verification:

npm run build

📈 Development Roadmap

Phase

Feature

01

Architecture & system design

02

Backend foundation

03

Authentication & RBAC

04

Core placement APIs

05

React frontend

06

Resume upload & parsing

07

AI resume analysis

08

Job matching

09–10

Interview intelligence

11–12

Analytics & security

🔒 Security

The project includes several security measures:

JWT authentication

Password hashing with bcrypt

Role-based authorization

Environment variables for secrets

CORS configuration

Production API documentation controls

Validation error handling designed to avoid exposing sensitive input

Login rate limiting is a known future enhancement.

🎯 Project Goals

The main goals of this project are to:

Centralize the college placement workflow.

Reduce manual placement management.

Give students better visibility into suitable opportunities.

Help recruiters manage candidates efficiently.

Provide administrators with placement insights.

Use AI to improve resume and interview preparation.

📌 Current Project Status

Status: Core system implemented and locally verified.

Implemented areas include:

Backend architecture

MySQL database integration

Authentication and RBAC

Core placement APIs

React frontend

Resume upload and parsing

Resume analysis

Job matching

Interview functionality

Analytics dashboards

Security improvements

The application is currently intended to be run locally. Cloud deployment can be added as a future step.

👨‍💻 Author

Chaitanya

AI-Powered Placement Management System
B.Tech Project

⭐ Future Enhancements

Possible future improvements include:

Cloud deployment

Production AI provider configuration

Email notifications

Advanced recruiter search and filtering

More detailed placement reports

Automated login rate limiting

Additional AI-powered career guidance
