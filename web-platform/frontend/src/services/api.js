import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor para tratar erros
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Strategies API
export const strategiesAPI = {
  list: (params) => api.get('/strategies/', { params }),
  get: (name) => api.get(`/strategies/${name}`),
  create: (data) => api.post('/strategies/', data),
  update: (name, data) => api.put(`/strategies/${name}`, data),
  delete: (name) => api.delete(`/strategies/${name}`),
  activate: (name) => api.post(`/strategies/${name}/activate`),
  deactivate: (name) => api.post(`/strategies/${name}/deactivate`),
  discover: () => api.get('/strategies/discover/available')
};

// Orders API
export const ordersAPI = {
  list: (params) => api.get('/orders/', { params }),
  get: (id) => api.get(`/orders/${id}`),
  stats: (params) => api.get('/orders/stats/summary', { params }),
  todaySummary: () => api.get('/orders/today/summary'),
  closeAll: () => api.post('/orders/close-all')
};

// Health check
export const healthCheck = () => api.get('/health');

export default api;

