import React, { useEffect, useState } from 'react';
import { applicationsApi } from '../../api/applications';
import { getErrorMessage } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import EmptyState from '../../components/EmptyState';
import StatusBadge from '../../components/StatusBadge';

const TIMELINE = ['APPLIED', 'SHORTLISTED', 'TECHNICAL_INTERVIEW', 'HR_INTERVIEW', 'SELECTED'];

export default function MyApplications() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    applicationsApi
      .my()
      .then(setApplications)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorBanner message={error} />;
  if (applications.length === 0) {
    return <EmptyState title="No applications yet" message="Browse jobs and apply to get started." />;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">My Applications</h1>
      <div className="mt-6 flex flex-col gap-4">
        {applications.map((app) => (
          <div key={app.id} className="card">
            <div className="flex items-center justify-between">
              <span className="font-medium text-gray-900">Job #{app.job_id}</span>
              <StatusBadge status={app.status} />
            </div>
            {app.status !== 'REJECTED' && (
              <div className="mt-4 flex items-center gap-2">
                {TIMELINE.map((step, idx) => {
                  const reached = TIMELINE.indexOf(app.status) >= idx;
                  return (
                    <React.Fragment key={step}>
                      <div
                        className={`h-2 w-2 rounded-full ${reached ? 'bg-brand-600' : 'bg-gray-200'}`}
                        title={step}
                      />
                      {idx < TIMELINE.length - 1 && (
                        <div className={`h-0.5 flex-1 ${reached ? 'bg-brand-600' : 'bg-gray-200'}`} />
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            )}
            {app.match_score != null && (
              <p className="mt-2 text-xs text-gray-500">Match score: {app.match_score}%</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
