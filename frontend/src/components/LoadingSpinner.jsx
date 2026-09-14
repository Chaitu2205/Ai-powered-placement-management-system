import React from 'react';

export default function LoadingSpinner({ fullScreen = false }) {
  const spinner = (
    <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
  );

  if (!fullScreen) return <div className="flex justify-center py-8">{spinner}</div>;

  return (
    <div className="flex h-screen w-full items-center justify-center">{spinner}</div>
  );
}
