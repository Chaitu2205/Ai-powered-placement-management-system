import React, { useEffect, useState } from 'react';
import { jobsApi } from '../../api/jobs';
import { getErrorMessage } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import DataTable from '../../components/DataTable';
import StatusBadge from '../../components/StatusBadge';
import Pagination from '../../components/Pagination';

export default function AdminJobs() {
  const [data, setData] = useState({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const pageSize = 20;

  useEffect(() => {
    setLoading(true);
    jobsApi
      .list({ page, page_size: pageSize })
      .then(setData)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [page]);

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
      <ErrorBanner message={error} />
      <div className="mt-4">
        <DataTable
          columns={[
            { key: 'title', header: 'Title' },
            { key: 'company_id', header: 'Company ID' },
            { key: 'location', header: 'Location', render: (r) => r.location || '—' },
            { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
          ]}
          rows={data.items}
        />
        <Pagination page={page} pageSize={pageSize} total={data.total} onPageChange={setPage} />
      </div>
    </div>
  );
}
