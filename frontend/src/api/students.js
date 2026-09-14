import { apiClient } from './client';

export const studentsApi = {
  getMe: () => apiClient.get('/students/me').then((r) => r.data),
  updateMe: (payload) => apiClient.put('/students/me', payload).then((r) => r.data),
  list: (params) => apiClient.get('/students', { params }).then((r) => r.data),
  get: (id) => apiClient.get(`/students/${id}`).then((r) => r.data),
};
