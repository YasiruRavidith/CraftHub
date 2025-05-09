// src/components/auth/LoginForm.jsx
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useAuth } from '../../contexts/AuthContext';
import Input from '../common/Input';
import Button from '../common/Button';

const LoginForm = () => {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [apiError, setApiError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const onSubmit = async (data) => {
    setApiError('');
    setLoading(true);
    try {
      await login(data.username, data.password);
      navigate('/dashboard'); // Or intended redirect
    } catch (err) {
      setApiError(err.response?.data?.detail || err.response?.data?.non_field_errors?.[0] || err.message || 'Login failed. Please check credentials.');
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {apiError && <p className="text-sm text-red-600 bg-red-100 p-3 rounded-md">{apiError}</p>}
      <Input
        label="Username or Email"
        id="username"
        {...register("username", { required: "Username or email is required" })}
        error={errors.username}
        placeholder="your_username or email@example.com"
      />
      <Input
        label="Password"
        type="password"
        id="password"
        {...register("password", { required: "Password is required" })}
        error={errors.password}
        placeholder="••••••••"
      />
      <Button type="submit" className="w-full" isLoading={loading} disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </Button>
      <div className="text-sm text-center">
        <Link to="/auth/forgot-password" className="font-medium text-blue-600 hover:text-blue-500">
          Forgot your password?
        </Link>
      </div>
    </form>
  );
};

export default LoginForm;