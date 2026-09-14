import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { analyticsApi } from '../../api/analytics';
import { studentsApi } from '../../api/students';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import EmptyState from '../../components/EmptyState';
import { getErrorMessage } from '../../api/client';

export default function StudentDashboard() {
  const [profile, setProfile] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([studentsApi.getMe(), analyticsApi.student()])
      .then(([me, data]) => {
        setProfile(me);
        setAnalytics(data);
      })
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorBanner message={error} />;

  const chartData = analytics.applications_by_status.map((s) => ({
    status: s.status.replace(/_/g, ' '),
    count: s.count,
  }));

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Welcome, {profile?.full_name}</h1>
      <p className="mt-1 text-sm text-gray-500">Here's a snapshot of your placement activity.</p>

      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total Applications" value={analytics.total_applications} />
        <StatCard label="Open Jobs" value={analytics.open_jobs_count} />
        <StatCard
          label="Resume Score"
          value={analytics.resume_score != null ? `${analytics.resume_score}/100` : '—'}
        />
        <StatCard
          label="Avg. Interview Score"
          value={analytics.average_interview_score != null ? `${analytics.average_interview_score.toFixed(1)}/10` : '—'}
        />
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 font-semibold text-gray-900">Applications by status</h2>
          {chartData.length === 0 ? (
            <EmptyState title="No applications yet" />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="status" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card">
          <h2 className="mb-4 font-semibold text-gray-900">Interview practice</h2>
          <p className="text-sm text-gray-600">Sessions started: {analytics.total_interview_sessions}</p>
          <p className="mt-1 text-sm text-gray-600">Questions answered: {analytics.questions_answered}</p>
          {analytics.latest_interview_score != null && (
            <p className="mt-1 text-sm text-gray-600">
              Latest session score: <span className="font-medium">{analytics.latest_interview_score}/10</span>{' '}
              ({analytics.latest_interview_status})
            </p>
          )}
        </div>
      </div>

      {analytics.recommended_jobs.length > 0 && (
        <div className="mt-6 card">
          <h2 className="mb-4 font-semibold text-gray-900">Recommended for you</h2>
          <div className="flex flex-col gap-2">
            {analytics.recommended_jobs.map((job) => (
              <div key={job.job_id} className="flex items-center justify-between border-b border-gray-100 py-2 last:border-0">
                <div>
                  <p className="text-sm font-medium text-gray-900">{job.job_title}</p>
                  <p className="text-xs text-gray-500">{job.company_name}</p>
                </div>
                <span className="text-sm font-semibold text-brand-700">{job.match_score}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="card">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
