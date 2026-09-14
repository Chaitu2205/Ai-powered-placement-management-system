import { apiClient } from './client';

export const recruitersApi = {
  getMe: () => apiClient.get('/recruiters/me').then((r) => r.data),
  updateMe: (payload) => apiClient.put('/recruiters/me', payload).then((r) => r.data),
  list: () => apiClient.get('/recruiters').then((r) => r.data),
};
