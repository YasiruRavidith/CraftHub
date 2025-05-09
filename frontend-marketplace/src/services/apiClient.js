// src/services/apiClient.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`; // Assuming Token authentication from DRF
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Potentially clear local auth state and redirect
      console.error("Unauthorized request or token expired. Logging out.");
      localStorage.removeItem('authToken');
      localStorage.removeItem('authUser');
      // This is a side-effect, better handled by calling logout from AuthContext
      // or by having components react to 401s.
      // For now, just log. A robust solution would involve event emitters or context updates.
      // window.location.href = '/auth/login'; // Avoid direct manipulation if possible
    }
    return Promise.reject(error);
  }
);

export default apiClient;