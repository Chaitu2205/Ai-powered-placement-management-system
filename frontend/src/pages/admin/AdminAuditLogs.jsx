import React, { useEffect, useState } from 'react';
import { auditLogsApi } from '../../api/notifications';
import { getErrorMessage } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import DataTable from '../../components/DataTable';
import Pagination from '../../components/Pagination';

export default function AdminAuditLogs() {
  const [data, setData] = useState({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const pageSize = 25;

  useEffect(() => {
    setLoading(true);
    auditLogsApi
      .list({ page, page_size: pageSize })
      .then(setData)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [page]);

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
      <ErrorBanner message={error} />
      <div className="mt-4">
        <DataTable
          columns={[
            { key: 'created_at', header: 'When', render: (r) => new Date(r.created_at).toLocaleString() },
            { key: 'action', header: 'Action' },
            { key: 'entity_type', header: 'Entity' },
            { key: 'entity_id', header: 'Entity ID', render: (r) => r.entity_id ?? '—' },
            { key: 'user_id', header: 'Actor User ID', render: (r) => r.user_id ?? 'system' },
          ]}
          rows={data.items}
        />
        <Pagination page={page} pageSize={pageSize} total={data.total} onPageChange={setPage} />
      </div>
    </div>
  );
}
