import { apiClient } from './client';

export const companiesApi = {
  list: (params) => apiClient.get('/companies', { params }).then((r) => r.data),
  get: (id) => apiClient.get(`/companies/${id}`).then((r) => r.data),
  create: (payload) => apiClient.post('/companies', payload).then((r) => r.data),
  update: (id, payload) => apiClient.put(`/companies/${id}`, payload).then((r) => r.data),
};
