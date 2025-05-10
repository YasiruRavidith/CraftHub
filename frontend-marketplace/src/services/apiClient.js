// src/services/apiClient.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  // We can remove the default Content-Type here, or let the interceptor manage it.
  // For clarity, let's remove it and have the interceptor set it for JSON if not FormData.
  // headers: {
  //   'Content-Type': 'application/json', // Default for JSON, but FormData needs multipart
  // },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }

    // If data is an instance of FormData, Axios will automatically set the
    // Content-Type to 'multipart/form-data' and handle the boundary.
    // We just need to make sure we don't inadvertently override it with 'application/json'.
    if (!(config.data instanceof FormData)) {
      // If it's not FormData, and no Content-Type is already set by the specific request,
      // then default to application/json.
      if (!config.headers['Content-Type']) {
        config.headers['Content-Type'] = 'application/json';
      }
    }
    // If config.data IS FormData, we do NOT set Content-Type here.
    // Axios will handle it. If we manually set 'multipart/form-data'
    // without the boundary, it will break.

    // For debugging, you can log the final headers before the request is sent
    // console.log('Axios request config:', config);

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
      console.error("Unauthorized request or token expired.");
      // Consider calling a logout function from AuthContext or dispatching an event
      // instead of direct localStorage manipulation here for better state management.
      // For example:
      // import { logoutUser } from '../contexts/AuthContext'; // Hypothetical
      // logoutUser(); // This function would clear local storage and update auth state.
      localStorage.removeItem('authToken');
      localStorage.removeItem('authUser');
      // Redirecting here can be problematic if this apiClient is used in non-component logic.
      // It's better for components to handle navigation based on context/state changes.
      // if (window.location.pathname !== '/auth/login') {
      //    window.location.href = '/auth/login';
      // }
    }
    return Promise.reject(error);
  }
);

export default apiClient;