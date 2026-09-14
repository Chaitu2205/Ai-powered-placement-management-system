import React, { useEffect, useState } from 'react';
import { notificationsApi } from '../../api/notifications';
import { getErrorMessage } from '../../api/client';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import EmptyState from '../../components/EmptyState';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    notificationsApi
      .list()
      .then(setNotifications)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleMarkRead = async (id) => {
    await notificationsApi.markRead(id);
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorBanner message={error} />;
  if (notifications.length === 0) return <EmptyState title="No notifications" />;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
      <div className="mt-6 flex flex-col gap-3">
        {notifications.map((n) => (
          <div
            key={n.id}
            className={`card flex items-start justify-between ${n.is_read ? 'opacity-60' : ''}`}
          >
            <div>
              <p className="font-medium text-gray-900">{n.title}</p>
              <p className="mt-1 text-sm text-gray-600">{n.message}</p>
              <p className="mt-1 text-xs text-gray-400">{new Date(n.created_at).toLocaleString()}</p>
            </div>
            {!n.is_read && (
              <button
                onClick={() => handleMarkRead(n.id)}
                className="shrink-0 text-xs font-medium text-brand-600 hover:underline"
              >
                Mark as read
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
