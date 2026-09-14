import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

import ProtectedRoute from './routes/ProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';
import LoadingSpinner from './components/LoadingSpinner';

import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import UnauthorizedPage from './pages/shared/UnauthorizedPage';
import NotificationsPage from './pages/shared/NotificationsPage';

import StudentDashboard from './pages/student/StudentDashboard';
import StudentProfile from './pages/student/StudentProfile';
import JobsList from './pages/student/JobsList';
import JobDetails from './pages/student/JobDetails';
import MyApplications from './pages/student/MyApplications';
import InterviewPractice from './pages/student/InterviewPractice';

import RecruiterDashboard from './pages/recruiter/RecruiterDashboard';
import RecruiterProfile from './pages/recruiter/RecruiterProfile';
import CompanyPage from './pages/recruiter/CompanyPage';
import RecruiterJobs from './pages/recruiter/RecruiterJobs';
import JobForm from './pages/recruiter/JobForm';
import JobApplicants from './pages/recruiter/JobApplicants';
import DrivesPage from './pages/recruiter/DrivesPage';

import AdminDashboard from './pages/admin/AdminDashboard';
import AdminStudents from './pages/admin/AdminStudents';
import AdminRecruiters from './pages/admin/AdminRecruiters';
import AdminCompanies from './pages/admin/AdminCompanies';
import AdminJobs from './pages/admin/AdminJobs';
import AdminApplications from './pages/admin/AdminApplications';
import AdminAuditLogs from './pages/admin/AdminAuditLogs';

const HOME_BY_ROLE = { student: '/student', recruiter: '/recruiter', admin: '/admin' };

function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner fullScreen />;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={HOME_BY_ROLE[user.role] || '/login'} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />

      {/* Student */}
      <Route element={<ProtectedRoute roles={['student']} />}>
        <Route element={<DashboardLayout />}>
          <Route path="/student" element={<StudentDashboard />} />
          <Route path="/student/profile" element={<StudentProfile />} />
          <Route path="/student/jobs" element={<JobsList />} />
          <Route path="/student/jobs/:jobId" element={<JobDetails />} />
          <Route path="/student/applications" element={<MyApplications />} />
          <Route path="/student/interview-practice" element={<InterviewPractice />} />
          <Route path="/student/notifications" element={<NotificationsPage />} />
        </Route>
      </Route>

      {/* Recruiter */}
      <Route element={<ProtectedRoute roles={['recruiter']} />}>
        <Route element={<DashboardLayout />}>
          <Route path="/recruiter" element={<RecruiterDashboard />} />
          <Route path="/recruiter/profile" element={<RecruiterProfile />} />
          <Route path="/recruiter/company" element={<CompanyPage />} />
          <Route path="/recruiter/jobs" element={<RecruiterJobs />} />
          <Route path="/recruiter/jobs/new" element={<JobForm />} />
          <Route path="/recruiter/jobs/:jobId/edit" element={<JobForm />} />
          <Route path="/recruiter/jobs/:jobId/applicants" element={<JobApplicants />} />
          <Route path="/recruiter/drives" element={<DrivesPage />} />
        </Route>
      </Route>

      {/* Admin */}
      <Route element={<ProtectedRoute roles={['admin']} />}>
        <Route element={<DashboardLayout />}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/students" element={<AdminStudents />} />
          <Route path="/admin/recruiters" element={<AdminRecruiters />} />
          <Route path="/admin/companies" element={<AdminCompanies />} />
          <Route path="/admin/jobs" element={<AdminJobs />} />
          <Route path="/admin/drives" element={<DrivesPage />} />
          <Route path="/admin/applications" element={<AdminApplications />} />
          <Route path="/admin/audit-logs" element={<AdminAuditLogs />} />
          <Route path="/admin/notifications" element={<NotificationsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
