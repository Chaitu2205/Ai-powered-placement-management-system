import React, { useEffect, useState } from 'react';
import { applicationsApi } from '../../api/applications';
import { getErrorMessage } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import DataTable from '../../components/DataTable';
import StatusBadge from '../../components/StatusBadge';
import Pagination from '../../components/Pagination';

const STATUS_OPTIONS = [
  'APPLIED',
  'SHORTLISTED',
  'ONLINE_TEST',
  'TECHNICAL_INTERVIEW',
  'HR_INTERVIEW',
  'SELECTED',
  'REJECTED',
];

export default function AdminApplications() {
  const { showToast } = useToast();
  const [data, setData] = useState({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const pageSize = 20;

  const load = () => {
    setLoading(true);
    applicationsApi
      .list({ page, page_size: pageSize })
      .then(setData)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, [page]);

  const handleStatusChange = async (id, status) => {
    try {
      await applicationsApi.updateStatus(id, status);
      showToast('Status updated', 'success');
      load();
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
      <ErrorBanner message={error} />
      <div className="mt-4">
        <DataTable
          columns={[
            { key: 'id', header: 'ID' },
            { key: 'job_id', header: 'Job ID' },
            { key: 'student_id', header: 'Student ID' },
            { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
            {
              key: 'update',
              header: 'Update',
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
          rows={data.items}
        />
        <Pagination page={page} pageSize={pageSize} total={data.total} onPageChange={setPage} />
      </div>
    </div>
  );
}
