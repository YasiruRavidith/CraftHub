// src/components/auth/RegisterForm.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useAuth } from '../../contexts/AuthContext';
import Input from '../common/Input';
import Button from '../common/Button';

const RegisterForm = () => {
  const { register: formRegister, handleSubmit, watch, formState: { errors } } = useForm();
  const [apiError, setApiError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register: authRegister } = useAuth();
  const navigate = useNavigate();

  const password = watch("password");

  const onSubmit = async (data) => {
    setApiError('');
    setLoading(true);
    //const { password2, ...registrationData } = data; // Exclude password2 from data sent to API
    console.log("Data being sent to backend:", data); // <--- ADD THIS
    try {
      await authRegister(data);
      navigate('/dashboard'); // Or to a "please verify email" page
    } catch (err) {
        let errorMessage = "Registration failed. Please try again.";
        if (err.response && err.response.data) {
            const responseData = err.response.data;
            console.error("Backend validation errors:", responseData); // <--- LOG THIS
            // Concatenate all error messages from DRF
            errorMessage = Object.keys(responseData)
                .map(key => `${key}: ${Array.isArray(responseData[key]) ? responseData[key].join(', ') : responseData[key]}`)
                .join('; ');
        } else if (err.message) {
            errorMessage = err.message;
        }
      setApiError(errorMessage);
    }
    setLoading(false);
  };

  const userTypeOptions = [
    { value: 'buyer', label: 'Buyer' },
    { value: 'seller', label: 'Seller' },
    { value: 'designer', label: 'Designer' },
    { value: 'manufacturer', label: 'Manufacturer' },
  ];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 text-gray-950">
      {apiError && <p className="text-sm text-red-600 bg-red-100 p-3 rounded-md">{apiError}</p>}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
            label="First Name"
            id="first_name"
            {...formRegister("first_name")}
            error={errors.first_name}
        />
        <Input
            label="Last Name"
            id="last_name"
            {...formRegister("last_name")}
            error={errors.last_name}
        />
      </div>

      <Input
        label="Username"
        id="username"
        {...formRegister("username", { required: "Username is required" })}
        error={errors.username}
      />
      <Input
        label="Email"
        type="email"
        id="email"
        {...formRegister("email", { 
            required: "Email is required",
            pattern: { value: /^\S+@\S+$/i, message: "Invalid email address" }
        })}
        error={errors.email}
      />
      <div>
        <label htmlFor="user_type" className="block text-sm font-medium text-gray-700 mb-1">Account Type</label>
        <select
          id="user_type"
          {...formRegister("user_type", { required: "Account type is required" })}
          className={`mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md ${errors.user_type ? 'border-red-500' : ''}`}
          defaultValue=""
        >
          <option value="" disabled>Select account type</option>
          {userTypeOptions.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {errors.user_type && <p className="mt-1 text-xs text-red-600">{errors.user_type.message}</p>}
      </div>
      <Input
        label="Password"
        type="password"
        id="password"
        {...formRegister("password", { 
            required: "Password is required",
            minLength: { value: 8, message: "Password must be at least 8 characters" }
        })}
        error={errors.password}
      />
      <Input
        label="Confirm Password"
        type="password"
        id="password2"
        {...formRegister("password2", { 
            required: "Please confirm your password",
            validate: value => value === password || "Passwords do not match"
        })}
        error={errors.password2}
      />
      <Button type="submit" className="w-full" isLoading={loading} disabled={loading}>
        {loading ? 'Registering...' : 'Create Account'}
      </Button>
    </form>
  );
};

export default RegisterForm;