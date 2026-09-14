import { apiClient } from './client';

export const jobsApi = {
  list: (params) => apiClient.get('/jobs', { params }).then((r) => r.data),
  get: (id) => apiClient.get(`/jobs/${id}`).then((r) => r.data),
  create: (payload) => apiClient.post('/jobs', payload).then((r) => r.data),
  update: (id, payload) => apiClient.put(`/jobs/${id}`, payload).then((r) => r.data),
  close: (id) => apiClient.post(`/jobs/${id}/close`).then((r) => r.data),
};
