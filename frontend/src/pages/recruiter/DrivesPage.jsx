import React, { useEffect, useState } from 'react';
import { drivesApi } from '../../api/drives';
import { getErrorMessage } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import DataTable from '../../components/DataTable';
import StatusBadge from '../../components/StatusBadge';

export default function DrivesPage() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const canManage = user?.role === 'admin';

  const [drives, setDrives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', start_date: '', end_date: '', min_cgpa: '' });
  const [saving, setSaving] = useState(false);

  const load = () => {
    drivesApi
      .list()
      .then(setDrives)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await drivesApi.create({
        ...form,
        min_cgpa: form.min_cgpa ? Number(form.min_cgpa) : null,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
      });
      showToast('Placement drive created', 'success');
      setShowForm(false);
      setForm({ name: '', start_date: '', end_date: '', min_cgpa: '' });
      load();
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Placement Drives</h1>
        {canManage && (
          <button onClick={() => setShowForm((s) => !s)} className="btn-primary">
            {showForm ? 'Cancel' : '+ New drive'}
          </button>
        )}
      </div>

      <ErrorBanner message={error} />

      {showForm && (
        <form onSubmit={handleCreate} className="card mt-4 grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="text-sm font-medium text-gray-700">Drive name</label>
            <input required className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Start date</label>
            <input type="date" className="input" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">End date</label>
            <input type="date" className="input" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Minimum CGPA</label>
            <input type="number" step="0.1" className="input" value={form.min_cgpa} onChange={(e) => setForm({ ...form, min_cgpa: e.target.value })} />
          </div>
          <button type="submit" disabled={saving} className="btn-primary col-span-2 self-end">
            {saving ? 'Creating…' : 'Create drive'}
          </button>
        </form>
      )}

      <div className="mt-6">
        <DataTable
          columns={[
            { key: 'name', header: 'Name' },
            { key: 'start_date', header: 'Start', render: (r) => r.start_date || '—' },
            { key: 'end_date', header: 'End', render: (r) => r.end_date || '—' },
            { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
          ]}
          rows={drives}
          emptyMessage="No placement drives yet."
        />
      </div>
    </div>
  );
}
