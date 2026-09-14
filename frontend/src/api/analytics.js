import { apiClient } from './client';

export const analyticsApi = {
  student: () => apiClient.get('/analytics/student').then((r) => r.data),
  recruiter: () => apiClient.get('/analytics/recruiter').then((r) => r.data),
  admin: () => apiClient.get('/analytics/admin').then((r) => r.data),
};
