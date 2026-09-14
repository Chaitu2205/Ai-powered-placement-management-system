import { apiClient } from './client';

export const authApi = {
  register: (payload) => apiClient.post('/auth/register', payload).then((r) => r.data),
  login: (email, password) => apiClient.post('/auth/login', { email, password }).then((r) => r.data),
  me: () => apiClient.get('/auth/me').then((r) => r.data),
};
