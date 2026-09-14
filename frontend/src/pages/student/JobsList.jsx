import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { jobsApi } from '../../api/jobs';
import { getErrorMessage } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import EmptyState from '../../components/EmptyState';
import StatusBadge from '../../components/StatusBadge';
import Pagination from '../../components/Pagination';

export default function JobsList() {
  const [data, setData] = useState({ items: [], total: 0 });
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const pageSize = 10;

  useEffect(() => {
    setLoading(true);
    jobsApi
      .list({ status: 'open', search: search || undefined, page, page_size: pageSize })
      .then(setData)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [search, page]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Browse Jobs</h1>

      <input
        placeholder="Search by job title…"
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
      ) : data.items.length === 0 ? (
        <EmptyState title="No open jobs" message="Check back later for new openings." />
      ) : (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {data.items.map((job) => (
            <Link key={job.id} to={`/student/jobs/${job.id}`} className="card block hover:shadow-md">
              <div className="flex items-start justify-between">
                <h2 className="font-semibold text-gray-900">{job.title}</h2>
                <StatusBadge status={job.status} />
              </div>
              <p className="mt-1 text-sm text-gray-500">{job.location || 'Location not specified'}</p>
              <p className="mt-2 text-sm text-gray-600 line-clamp-2">{job.description}</p>
              {job.package_lpa && (
                <p className="mt-2 text-sm font-medium text-brand-700">₹{job.package_lpa} LPA</p>
              )}
            </Link>
          ))}
        </div>
      )}

      <Pagination page={page} pageSize={pageSize} total={data.total} onPageChange={setPage} />
    </div>
  );
}
