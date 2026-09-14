import React, { useEffect, useState } from 'react';
import { companiesApi } from '../../api/companies';
import { getErrorMessage } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import DataTable from '../../components/DataTable';
import Pagination from '../../components/Pagination';

export default function AdminCompanies() {
  const [data, setData] = useState({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const pageSize = 20;

  useEffect(() => {
    setLoading(true);
    companiesApi
      .list({ page, page_size: pageSize })
      .then(setData)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [page]);

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Companies</h1>
      <ErrorBanner message={error} />
      <div className="mt-4">
        <DataTable
          columns={[
            { key: 'name', header: 'Name' },
            { key: 'industry', header: 'Industry', render: (r) => r.industry || '—' },
            { key: 'website', header: 'Website', render: (r) => r.website || '—' },
          ]}
          rows={data.items}
        />
        <Pagination page={page} pageSize={pageSize} total={data.total} onPageChange={setPage} />
      </div>
    </div>
  );
}
