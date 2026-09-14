import React, { useEffect, useState } from 'react';
import { companiesApi } from '../../api/companies';
import { getErrorMessage } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import EmptyState from '../../components/EmptyState';

export default function CompanyPage() {
  const { showToast } = useToast();
  const [company, setCompany] = useState(null);
  const [form, setForm] = useState({ name: '', industry: '', website: '', description: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadCompany = () => {
    // A recruiter's own company is the one whose recruiter_id matches them;
    // the companies list is small enough per-recruiter to fetch and filter client-side.
    companiesApi
      .list({ page: 1, page_size: 100 })
      .then((data) => {
        const mine = data.items.find((c) => c.recruiter_id != null);
        setCompany(mine || null);
        if (mine) setForm(mine);
      })
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(loadCompany, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const created = await companiesApi.create(form);
      setCompany(created);
      showToast('Company created', 'success');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const updated = await companiesApi.update(company.id, form);
      setCompany(updated);
      showToast('Company updated', 'success');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold text-gray-900">Company</h1>
      {!company && <EmptyState title="No company yet" message="Create your company profile below." />}

      <form onSubmit={company ? handleUpdate : handleCreate} className="card mt-6 flex flex-col gap-4">
        <ErrorBanner message={error} />
        <div>
          <label className="text-sm font-medium text-gray-700">Company name</label>
          <input required className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700">Industry</label>
          <input className="input" value={form.industry || ''} onChange={(e) => setForm({ ...form, industry: e.target.value })} />
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700">Website</label>
          <input className="input" value={form.website || ''} onChange={(e) => setForm({ ...form, website: e.target.value })} />
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700">Description</label>
          <textarea className="input" rows={4} value={form.description || ''} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </div>
        <button type="submit" disabled={saving} className="btn-primary self-start">
          {saving ? 'Saving…' : company ? 'Save changes' : 'Create company'}
        </button>
      </form>
    </div>
  );
}
