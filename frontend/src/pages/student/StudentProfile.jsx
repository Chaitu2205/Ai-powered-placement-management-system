import React, { useEffect, useState } from 'react';
import { studentsApi } from '../../api/students';
import { getErrorMessage } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';

export default function StudentProfile() {
  const { showToast } = useToast();
  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    studentsApi
      .getMe()
      .then((data) =>
        setForm({
          full_name: data.full_name || '',
          phone: data.phone || '',
          batch_year: data.batch_year || '',
          cgpa: data.cgpa || '',
        })
      )
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await studentsApi.updateMe({
        ...form,
        batch_year: form.batch_year ? Number(form.batch_year) : null,
        cgpa: form.cgpa ? Number(form.cgpa) : null,
      });
      showToast('Profile updated', 'success');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (!form) return <ErrorBanner message={error} />;

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
      <form onSubmit={handleSubmit} className="card mt-6 flex flex-col gap-4">
        <ErrorBanner message={error} />
        <div>
          <label className="text-sm font-medium text-gray-700">Full name</label>
          <input
            className="input"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700">Phone</label>
          <input
            className="input"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
          />
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700">Batch year</label>
          <input
            type="number"
            className="input"
            value={form.batch_year}
            onChange={(e) => setForm({ ...form, batch_year: e.target.value })}
          />
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700">CGPA</label>
          <input
            type="number"
            step="0.01"
            className="input"
            value={form.cgpa}
            onChange={(e) => setForm({ ...form, cgpa: e.target.value })}
          />
        </div>
        <button type="submit" disabled={saving} className="btn-primary self-start">
          {saving ? 'Saving…' : 'Save changes'}
        </button>
      </form>
    </div>
  );
}
