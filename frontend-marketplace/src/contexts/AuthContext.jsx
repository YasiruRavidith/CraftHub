import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import apiClient from '../services/apiClient';
import authService from '../services/authService'; // We'll refine this too

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true); // For initial auth check

  const initializeAuth = useCallback(async () => {
    const token = localStorage.getItem('authToken');
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Token ${token}`;
      try {
        const currentUser = await authService.getCurrentUser(); // Verify token and get user
        setUser(currentUser);
        setIsAuthenticated(true);
      } catch (error) {
        console.error("Failed to verify token or fetch user:", error);
        localStorage.removeItem('authToken'); // Invalid token
        delete apiClient.defaults.headers.common['Authorization'];
      }
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  const login = async (username, password) => {
    try {
      const data = await authService.login(username, password);
      localStorage.setItem('authToken', data.token);
      localStorage.setItem('authUser', JSON.stringify(data.user)); // Storing user for quick access
      setUser(data.user);
      setIsAuthenticated(true);
      apiClient.defaults.headers.common['Authorization'] = `Token ${data.token}`;
      return data.user;
    } catch (error) {
      // Error is already logged in authService, re-throw for component to handle
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const data = await authService.register(userData);
      localStorage.setItem('authToken', data.token);
      localStorage.setItem('authUser', JSON.stringify(data.user));
      setUser(data.user);
      setIsAuthenticated(true);
      apiClient.defaults.headers.common['Authorization'] = `Token ${data.token}`;
      return data.user;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    authService.logout(); // Backend logout if implemented
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    setUser(null);
    setIsAuthenticated(false);
    delete apiClient.defaults.headers.common['Authorization'];
    // Could also navigate to home or login page here if using useNavigate outside a component
  };

  const updateUserContext = (updatedUserData) => {
    setUser(updatedUserData);
    localStorage.setItem('authUser', JSON.stringify(updatedUserData));
  };


  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    register,
    logout,
    updateUserContext
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen text-xl font-semibold">
        Authenticating...
      </div>
    );
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined || context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};