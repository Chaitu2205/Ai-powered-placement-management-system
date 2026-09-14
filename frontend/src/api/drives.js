import { apiClient } from './client';

export const drivesApi = {
  list: () => apiClient.get('/drives').then((r) => r.data),
  get: (id) => apiClient.get(`/drives/${id}`).then((r) => r.data),
  create: (payload) => apiClient.post('/drives', payload).then((r) => r.data),
  update: (id, payload) => apiClient.put(`/drives/${id}`, payload).then((r) => r.data),
};
