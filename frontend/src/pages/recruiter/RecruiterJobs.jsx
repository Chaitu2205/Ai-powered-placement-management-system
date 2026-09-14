import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { jobsApi } from '../../api/jobs';
import { getErrorMessage } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import DataTable from '../../components/DataTable';
import StatusBadge from '../../components/StatusBadge';
import ConfirmDialog from '../../components/ConfirmDialog';

export default function RecruiterJobs() {
  const { showToast } = useToast();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [confirmingId, setConfirmingId] = useState(null);

  const load = () => {
    jobsApi
      .list({ page: 1, page_size: 100 })
      .then((data) => setJobs(data.items))
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleClose = async () => {
    try {
      await jobsApi.close(confirmingId);
      showToast('Job closed', 'success');
      setConfirmingId(null);
      load();
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
        <Link to="/recruiter/jobs/new" className="btn-primary">
          + Post a job
        </Link>
      </div>

      <ErrorBanner message={error} />

      <div className="mt-6">
        <DataTable
          columns={[
            { key: 'title', header: 'Title' },
            { key: 'location', header: 'Location', render: (r) => r.location || '—' },
            { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
            {
              key: 'actions',
              header: '',
              render: (r) => (
                <div className="flex gap-3">
                  <Link to={`/recruiter/jobs/${r.id}/applicants`} className="text-sm text-brand-600 hover:underline">
                    Applicants
                  </Link>
                  <Link to={`/recruiter/jobs/${r.id}/edit`} className="text-sm text-brand-600 hover:underline">
                    Edit
                  </Link>
                  {r.status === 'open' && (
                    <button
                      onClick={() => setConfirmingId(r.id)}
                      className="text-sm text-red-600 hover:underline"
                    >
                      Close
                    </button>
                  )}
                </div>
              ),
            },
          ]}
          rows={jobs}
          emptyMessage="You haven't posted any jobs yet."
        />
      </div>

      <ConfirmDialog
        open={confirmingId !== null}
        title="Close this job?"
        message="Students will no longer be able to apply."
        confirmLabel="Close job"
        onConfirm={handleClose}
        onCancel={() => setConfirmingId(null)}
      />
    </div>
  );
}
