import React, { useEffect, useState } from 'react';
import { recruitersApi } from '../../api/recruiters';
import { getErrorMessage } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import DataTable from '../../components/DataTable';

export default function AdminRecruiters() {
  const [recruiters, setRecruiters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    recruitersApi
      .list()
      .then(setRecruiters)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Recruiters</h1>
      <ErrorBanner message={error} />
      <div className="mt-4">
        <DataTable
          columns={[
            { key: 'full_name', header: 'Name' },
            { key: 'designation', header: 'Designation', render: (r) => r.designation || '—' },
            { key: 'phone', header: 'Phone', render: (r) => r.phone || '—' },
          ]}
          rows={recruiters}
        />
      </div>
    </div>
  );
}
