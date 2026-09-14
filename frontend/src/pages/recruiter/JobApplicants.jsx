import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { applicationsApi } from '../../api/applications';
import { getErrorMessage } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import DataTable from '../../components/DataTable';
import StatusBadge from '../../components/StatusBadge';

const STATUS_OPTIONS = [
  'APPLIED',
  'SHORTLISTED',
  'ONLINE_TEST',
  'TECHNICAL_INTERVIEW',
  'HR_INTERVIEW',
  'SELECTED',
  'REJECTED',
];

export default function JobApplicants() {
  const { jobId } = useParams();
  const { showToast } = useToast();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    applicationsApi
      .list({ job_id: jobId, page: 1, page_size: 100 })
      .then((data) => setApplications(data.items))
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, [jobId]);

  const handleStatusChange = async (id, status) => {
    try {
      await applicationsApi.updateStatus(id, status);
      showToast('Application status updated', 'success');
      load();
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Applicants</h1>
      <ErrorBanner message={error} />
      <div className="mt-6">
        <DataTable
          columns={[
            { key: 'job_id', header: 'Job' },
            { key: 'student_id', header: 'Student ID' },
            { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
            {
              key: 'update',
              header: 'Update status',
              render: (r) => (
                <select
                  className="input mt-0"
                  value={r.status}
                  onChange={(e) => handleStatusChange(r.id, e.target.value)}
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              ),
            },
          ]}
          rows={applications}
          emptyMessage="No applications for your jobs yet."
        />
      </div>
    </div>
  );
}
