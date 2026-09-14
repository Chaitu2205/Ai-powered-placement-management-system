import React from 'react';

const COLORS = {
  APPLIED: 'bg-blue-100 text-blue-700',
  SHORTLISTED: 'bg-indigo-100 text-indigo-700',
  ONLINE_TEST: 'bg-purple-100 text-purple-700',
  TECHNICAL_INTERVIEW: 'bg-amber-100 text-amber-700',
  HR_INTERVIEW: 'bg-orange-100 text-orange-700',
  SELECTED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-700',
  open: 'bg-green-100 text-green-700',
  closed: 'bg-gray-200 text-gray-600',
};

export default function StatusBadge({ status }) {
  const classes = COLORS[status] || 'bg-gray-100 text-gray-700';
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${classes}`}>
      {String(status).replace(/_/g, ' ')}
    </span>
  );
}
