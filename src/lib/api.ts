// src/lib/api.ts
// Centralized API utility for connecting Next.js frontend to FastAPI backend
// Uses axios for all HTTP requests

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Add token to requests if it exists
const getAuthToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token');
  }
  return null;
};

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // for cookies/session if needed
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  validateStatus: (status) => status < 500 // Don't reject if status is < 500
});

// Add request interceptor for auth token and logging
api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for logging
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle network errors
    if (!error.response) {
      console.error('Network Error:', {
        message: error.message,
        config: error.config
      });
      return Promise.reject({
        response: {
          status: 0,
          data: {
            detail: 'Network error - Unable to connect to the server. Please check if the server is running.'
          }
        }
      });
    }

    // Handle timeout
    if (error.code === 'ECONNABORTED') {
      console.error('Timeout Error:', {
        url: error.config?.url,
        timeout: error.config?.timeout
      });
      return Promise.reject({
        response: {
          status: 408,
          data: {
            detail: 'Request timeout - The server took too long to respond.'
          }
        }
      });
    }

    // Handle other errors
    console.error('API Error:', {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    });
    return Promise.reject(error);
  }
);

// --- Auth ---
export const login = (data: { 
  auth_type: 'sql' | 'windows';
  server?: string; 
  database?: string; 
  username: string; 
  password?: string;
}) => {
  return api.post('/auth/login', data);
};
export const logout = () => api.post('/auth/logout');
export const getCurrentUser = () => api.get('/auth/me');

// --- Reports ---
export const generateReport = (data: any) => api.post('/report/generate', data, { responseType: 'blob' });
export const getReportList = () => api.get('/report/list');
export const getReportPreview = (data: any) => api.post('/report/preview', data);
export const downloadReport = (reportId: string) => api.get(`/report/download/${reportId}`, { responseType: 'blob' });

// --- Templates ---
export const getTemplates = () => api.get('/template/');
export const getTemplate = (id: string) => api.get(`/template/${id}`);
export const createTemplate = (data: any) => api.post('/template/', data);
export const updateTemplate = (id: string, data: any) => api.put(`/template/${id}`, data);
export const deleteTemplate = (id: string) => api.delete(`/template/${id}`);

// --- Email ---
export const sendEmail = (data: any) => api.post('/email/send', data);
export const getSmtpSettings = () => api.get('/email/settings');
export const updateSmtpSettings = (data: any) => api.put('/email/settings', data);

// --- Scheduler ---
export const getSchedules = () => api.get('/scheduler/');
export const createSchedule = (data: any) => api.post('/scheduler/', data);
export const updateSchedule = (id: string, data: any) => api.put(`/scheduler/${id}`, data);
export const deleteSchedule = (id: string) => api.delete(`/scheduler/${id}`);

// --- Logger ---
export const getLogs = () => api.get('/logger/');
export const getLogById = (id: string) => api.get(`/logger/${id}`);

// --- Charts ---
export const getChartData = (params: any) => api.get('/charts/', { params });

// --- MSSQL/WinCC ---
export const getMachineList = () => api.get('/report/machines');
export const getDashboardStats = () => api.get('/dashboard/stats');
export const getScadaTags = () => api.get('/dashboard/scada/tags');

// --- System Configuration ---
export const getSystemSettings = () => api.get('/system-settings/');
export const updateSystemSettings = (data: any) => api.put('/system-settings/', data);

// --- Tag Mapping (OPC UA tag -> machine/parameter rules) ---
export const getTagMappingRules = () => api.get('/tag-mapping/');
export const createTagMappingRule = (data: any) => api.post('/tag-mapping/', data);
export const updateTagMappingRule = (id: number, data: any) => api.put(`/tag-mapping/${id}`, data);
export const deleteTagMappingRule = (id: number) => api.delete(`/tag-mapping/${id}`);
export const reloadTagMapping = () => api.post('/tag-mapping/reload');

export default api;

