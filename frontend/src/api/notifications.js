import { apiClient } from './client';

export const notificationsApi = {
  list: () => apiClient.get('/notifications').then((r) => r.data),
  markRead: (id) => apiClient.put(`/notifications/${id}/read`).then((r) => r.data),
};

export const auditLogsApi = {
  list: (params) => apiClient.get('/audit-logs', { params }).then((r) => r.data),
};

export const departmentsApi = {
  list: () => apiClient.get('/departments').then((r) => r.data),
};

export const skillsApi = {
  list: (params) => apiClient.get('/skills', { params }).then((r) => r.data),
};
