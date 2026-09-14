import { apiClient } from './client';

export const interviewsApi = {
  createSession: (payload) => apiClient.post('/interviews', payload).then((r) => r.data),
  mySessions: () => apiClient.get('/interviews/my').then((r) => r.data),
  getSession: (id) => apiClient.get(`/interviews/${id}`).then((r) => r.data),
  generateQuestions: (sessionId, questionCount = 5) =>
    apiClient
      .post(`/interviews/${sessionId}/generate-questions`, null, { params: { question_count: questionCount } })
      .then((r) => r.data),
  getQuestions: (sessionId) => apiClient.get(`/interviews/${sessionId}/questions`).then((r) => r.data),
  submitAnswer: (questionId, answerText) =>
    apiClient.post(`/interviews/questions/${questionId}/answer`, { answer_text: answerText }).then((r) => r.data),
  evaluateAnswer: (questionId) =>
    apiClient.post(`/interviews/questions/${questionId}/evaluate`).then((r) => r.data),
  getAnswer: (questionId) =>
    apiClient.get(`/interviews/questions/${questionId}/answer`).then((r) => r.data),
};
