// src/services/authService.js
import apiClient from './apiClient';

const login = async (username, password) => {
  try {
    const response = await apiClient.post('/accounts/login/', { username, password });
    // Backend should return { token: 'xxx', user: { id: 1, username: '...', email: '...', user_type: '...' } }
    return response.data;
  } catch (error) {
    console.error('Login API error:', error.response?.data || error.message);
    throw error; // Re-throw to be caught by the calling component/context
  }
};

const register = async (userData) => {
  // userData: { username, email, password, password2, user_type, first_name, last_name }
  try {
    const response = await apiClient.post('/accounts/register/', userData);
    // Backend should return { token: 'xxx', user: { id: 1, username: '...', ... } }
    return response.data;
  } catch (error) {
    console.error('Registration API error:', error.response?.data || error.message);
    throw error;
  }
};

const logout = async () => {
  // Optional: Call a backend endpoint to invalidate the token server-side if implemented.
  // try {
  //   await apiClient.post('/accounts/logout/');
  // } catch (error) {
  //   console.error('Logout API error:', error.response?.data || error.message);
  // }
  // Primarily, frontend logout clears local token and user state.
  console.log("Logout service called.");
};

const getCurrentUser = async () => {
    try {
        // This endpoint should return the authenticated user's details
        // based on the token sent in the Authorization header.
        const response = await apiClient.get('/accounts/users/me/');
        return response.data;
    } catch (error) {
        console.error('Get current user API error:', error.response?.data || error.message);
        throw error; // Propagate error for AuthContext to handle (e.g., clear invalid token)
    }
};

export default {
  login,
  register,
  logout,
  getCurrentUser,
};