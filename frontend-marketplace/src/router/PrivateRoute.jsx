// src/router/PrivateRoute.jsx
import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const PrivateRoute = ({ children, allowedUserTypes }) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="flex justify-center items-center min-h-screen">Checking authentication...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  // Optional: Role-based access control
  if (allowedUserTypes && allowedUserTypes.length > 0 && !allowedUserTypes.includes(user?.user_type)) {
    // Redirect to a "not authorized" page or home page
    console.warn(`User type ${user?.user_type} not allowed for this route. Allowed: ${allowedUserTypes.join(', ')}`);
    return <Navigate to="/unauthorized" replace />; // Or to home: <Navigate to="/" replace />
  }

  return children ? children : <Outlet />;
};

export default PrivateRoute;