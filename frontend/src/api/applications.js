import { apiClient } from './client';

export const applicationsApi = {
  apply: (jobId, resumeId) =>
    apiClient.post('/applications', { job_id: jobId, resume_id: resumeId ?? null }).then((r) => r.data),
  my: () => apiClient.get('/applications/my').then((r) => r.data),
  list: (params) => apiClient.get('/applications', { params }).then((r) => r.data),
  updateStatus: (id, status) =>
    apiClient.put(`/applications/${id}/status`, { status }).then((r) => r.data),
};
