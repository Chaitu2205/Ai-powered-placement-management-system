import React, { useEffect, useState } from 'react';
import { studentsApi } from '../../api/students';
import { getErrorMessage } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import DataTable from '../../components/DataTable';
import StatusBadge from '../../components/StatusBadge';
import Pagination from '../../components/Pagination';

export default function AdminStudents() {
  const [data, setData] = useState({ items: [], total: 0 });
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const pageSize = 20;

  useEffect(() => {
    setLoading(true);
    studentsApi
      .list({ search: search || undefined, page, page_size: pageSize })
      .then(setData)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [search, page]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Students</h1>
      <input
        placeholder="Search by name…"
        value={search}
        onChange={(e) => {
          setPage(1);
          setSearch(e.target.value);
        }}
        className="input mt-4 max-w-sm"
      />
      <ErrorBanner message={error} />
      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="mt-4">
          <DataTable
            columns={[
              { key: 'full_name', header: 'Name' },
              { key: 'department_id', header: 'Dept.', render: (r) => r.department_id ?? '—' },
              { key: 'batch_year', header: 'Batch', render: (r) => r.batch_year ?? '—' },
              { key: 'cgpa', header: 'CGPA', render: (r) => r.cgpa ?? '—' },
              {
                key: 'placement_status',
                header: 'Status',
                render: (r) => <StatusBadge status={r.placement_status} />,
              },
            ]}
            rows={data.items}
          />
          <Pagination page={page} pageSize={pageSize} total={data.total} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
