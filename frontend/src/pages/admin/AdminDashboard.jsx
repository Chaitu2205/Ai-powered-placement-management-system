import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { analyticsApi } from '../../api/analytics';
import { getErrorMessage } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import EmptyState from '../../components/EmptyState';

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsApi
      .admin()
      .then(setAnalytics)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorBanner message={error} />;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-5">
        <StatCard label="Students" value={analytics.total_students} />
        <StatCard label="Recruiters" value={analytics.total_recruiters} />
        <StatCard label="Companies" value={analytics.total_companies} />
        <StatCard label="Jobs" value={analytics.total_jobs} />
        <StatCard label="Applications" value={analytics.total_applications} />
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <div className="card">
          <h2 className="mb-1 font-semibold text-gray-900">Placement rate</h2>
          <p className="text-3xl font-bold text-brand-700">{analytics.placement_percentage}%</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {analytics.students_by_placement_status.map((s) => (
              <div key={s.status} className="rounded-lg bg-gray-50 px-3 py-2 text-sm">
                <span className="font-medium text-gray-900">{s.count}</span>{' '}
                <span className="capitalize text-gray-500">{s.status.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h2 className="mb-1 font-semibold text-gray-900">Jobs by status</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {analytics.jobs_by_status.map((s) => (
              <div key={s.status} className="rounded-lg bg-gray-50 px-3 py-2 text-sm">
                <span className="font-medium text-gray-900">{s.count}</span>{' '}
                <span className="capitalize text-gray-500">{s.status}</span>
              </div>
            ))}
          </div>
          <h3 className="mb-1 mt-4 text-sm font-semibold text-gray-900">Applications by status</h3>
          <div className="flex flex-wrap gap-2">
            {analytics.applications_by_status.map((s) => (
              <div key={s.status} className="rounded-lg bg-gray-50 px-3 py-2 text-sm">
                <span className="font-medium text-gray-900">{s.count}</span>{' '}
                <span className="text-gray-500">{s.status.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 card">
        <h2 className="mb-4 font-semibold text-gray-900">Applications over the last 6 months</h2>
        {analytics.monthly_application_trend.length === 0 ? (
          <EmptyState title="No application data yet" />
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={analytics.monthly_application_trend}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
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
