// src/pages/LoginPage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import LoginForm from '../components/auth/LoginForm.jsx';

const LoginPage = () => {
  return (
    <> {/* Changed from div to fragment to let AuthLayout handle container */}
      <div className="text-center mb-8">
        {/* Optional: Logo or branding */}
        <h2 className="text-3xl font-bold text-gray-800">Welcome Back!</h2>
        <p className="text-gray-500">Login to access your account.</p>
      </div>
      <LoginForm />
      <p className="mt-6 text-center text-sm text-gray-600">
        Don't have an account?{' '}
        <Link to="/auth/register" className="font-medium text-blue-600 hover:text-blue-500">
          Sign up
        </Link>
      </p>
    </>
  );
};

export default LoginPage;