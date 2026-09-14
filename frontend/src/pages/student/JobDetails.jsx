import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { jobsApi } from '../../api/jobs';
import { applicationsApi } from '../../api/applications';
import { getErrorMessage } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import StatusBadge from '../../components/StatusBadge';

export default function JobDetails() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    jobsApi
      .get(jobId)
      .then(setJob)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [jobId]);

  const handleApply = async () => {
    setApplying(true);
    setError('');
    try {
      await applicationsApi.apply(Number(jobId));
      showToast('Application submitted!', 'success');
      navigate('/student/applications');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setApplying(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (!job) return <ErrorBanner message={error || 'Job not found'} />;

  return (
    <div className="max-w-2xl">
      <div className="flex items-start justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
        <StatusBadge status={job.status} />
      </div>
      <p className="mt-1 text-sm text-gray-500">{job.location || 'Location not specified'}</p>
      {job.package_lpa && (
        <p className="mt-1 text-sm font-medium text-brand-700">₹{job.package_lpa} LPA</p>
      )}

      <div className="card mt-6">
        <h2 className="font-semibold text-gray-900">Description</h2>
        <p className="mt-2 whitespace-pre-line text-sm text-gray-700">{job.description}</p>

        {job.job_skills?.length > 0 && (
          <>
            <h2 className="mt-4 font-semibold text-gray-900">Required skills</h2>
            <div className="mt-2 flex flex-wrap gap-2">
              {job.job_skills.map((js) => (
                <span
                  key={js.skill.id}
                  className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700"
                >
                  {js.skill.name}
                  {js.is_mandatory ? '' : ' (preferred)'}
                </span>
              ))}
            </div>
          </>
        )}
      </div>

      <ErrorBanner message={error} />

      <button
        onClick={handleApply}
        disabled={applying || job.status !== 'open'}
        className="btn-primary mt-6"
      >
        {job.status !== 'open' ? 'This job is closed' : applying ? 'Applying…' : 'Apply now'}
      </button>
    </div>
  );
}
