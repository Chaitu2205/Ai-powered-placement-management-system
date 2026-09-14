import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { jobsApi } from '../../api/jobs';
import { companiesApi } from '../../api/companies';
import { getErrorMessage } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';

export default function JobForm() {
  const { jobId } = useParams();
  const isEdit = Boolean(jobId);
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [companyId, setCompanyId] = useState(null);
  const [form, setForm] = useState({
    title: '',
    description: '',
    location: '',
    package_lpa: '',
    job_type: 'full_time',
  });
  const [skillsText, setSkillsText] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const init = async () => {
      try {
        const companies = await companiesApi.list({ page: 1, page_size: 100 });
        const mine = companies.items.find((c) => c.recruiter_id != null);
        setCompanyId(mine?.id ?? null);

        if (isEdit) {
          const job = await jobsApi.get(jobId);
          setForm({
            title: job.title,
            description: job.description,
            location: job.location || '',
            package_lpa: job.package_lpa || '',
            job_type: job.job_type,
          });
          setSkillsText((job.job_skills || []).map((js) => js.skill.name).join(', '));
        }
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [jobId, isEdit]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      if (isEdit) {
        await jobsApi.update(jobId, {
          ...form,
          package_lpa: form.package_lpa ? Number(form.package_lpa) : null,
        });
        showToast('Job updated', 'success');
      } else {
        const requiredSkills = skillsText
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean)
          .map((skill_name) => ({ skill_name, is_mandatory: true }));

        await jobsApi.create({
          ...form,
          company_id: companyId,
          package_lpa: form.package_lpa ? Number(form.package_lpa) : null,
          required_skills: requiredSkills,
        });
        showToast('Job posted', 'success');
      }
      navigate('/recruiter/jobs');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (!isEdit && !companyId) {
    return (
      <ErrorBanner message="You need to create your company profile before posting a job. Go to Company first." />
    );
  }

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-bold text-gray-900">{isEdit ? 'Edit Job' : 'Post a Job'}</h1>
      <form onSubmit={handleSubmit} className="card mt-6 flex flex-col gap-4">
        <ErrorBanner message={error} />
        <div>
          <label className="text-sm font-medium text-gray-700">Job title</label>
          <input required className="input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700">Description</label>
          <textarea
            required
            minLength={10}
            rows={5}
            className="input"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700">Location</label>
            <input className="input" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Package (LPA)</label>
            <input
              type="number"
              step="0.1"
              className="input"
              value={form.package_lpa}
              onChange={(e) => setForm({ ...form, package_lpa: e.target.value })}
            />
          </div>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700">Job type</label>
          <select
            className="input"
            value={form.job_type}
            onChange={(e) => setForm({ ...form, job_type: e.target.value })}
          >
            <option value="full_time">Full time</option>
            <option value="internship">Internship</option>
          </select>
        </div>
        {!isEdit && (
          <div>
            <label className="text-sm font-medium text-gray-700">Required skills (comma-separated)</label>
            <input
              className="input"
              placeholder="Python, FastAPI, SQL"
              value={skillsText}
              onChange={(e) => setSkillsText(e.target.value)}
            />
          </div>
        )}
        <button type="submit" disabled={saving} className="btn-primary self-start">
          {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Post job'}
        </button>
      </form>
    </div>
  );
}
