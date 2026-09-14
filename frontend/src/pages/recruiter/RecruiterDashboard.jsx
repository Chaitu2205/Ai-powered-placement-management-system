import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { analyticsApi } from '../../api/analytics';
import { getErrorMessage } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import EmptyState from '../../components/EmptyState';

export default function RecruiterDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    analyticsApi
      .recruiter()
      .then(setAnalytics)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorBanner message={error} />;

  const applicantChartData = analytics.applicants_per_job.map((j) => ({
    job: j.job_title.length > 18 ? `${j.job_title.slice(0, 18)}…` : j.job_title,
    applicants: j.applicant_count,
  }));

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Recruiter Dashboard</h1>
      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Jobs Posted" value={analytics.total_jobs_posted} />
        <StatCard label="Active Jobs" value={analytics.active_jobs} />
        <StatCard label="Closed Jobs" value={analytics.closed_jobs} />
        <StatCard label="Applications Received" value={analytics.total_applications_received} />
      </div>

      <div className="mt-6 card">
        <h2 className="mb-4 font-semibold text-gray-900">Applicants per job</h2>
        {applicantChartData.length === 0 ? (
          <EmptyState title="No jobs posted yet" />
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={applicantChartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="job" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="applicants" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {analytics.applications_by_status.length > 0 && (
        <div className="mt-6 card">
          <h2 className="mb-3 font-semibold text-gray-900">Applications by status</h2>
          <div className="flex flex-wrap gap-3">
            {analytics.applications_by_status.map((s) => (
              <div key={s.status} className="rounded-lg bg-gray-50 px-3 py-2 text-sm">
                <span className="font-medium text-gray-900">{s.count}</span>{' '}
                <span className="text-gray-500">{s.status.replace(/_/g, ' ')}</span>
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
