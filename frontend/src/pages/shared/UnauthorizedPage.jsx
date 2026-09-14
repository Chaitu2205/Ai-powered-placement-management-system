import React from 'react';
import { Link } from 'react-router-dom';

export default function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-gray-50 text-center">
      <h1 className="text-3xl font-bold text-gray-900">403 — Not authorized</h1>
      <p className="text-gray-500">You don't have permission to view this page.</p>
      <Link to="/" className="text-brand-600 hover:underline">
        Go back home
      </Link>
    </div>
  );
}
