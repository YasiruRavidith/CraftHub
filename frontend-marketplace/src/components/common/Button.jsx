import React from 'react';

const Button = ({
  children,
  onClick,
  type = 'button',
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  isLoading = false,
  ...props
}) => {
  const baseStyles =
    'font-semibold rounded-lg focus:outline-none focus:ring-2 focus:ring-opacity-75 transition duration-150 ease-in-out inline-flex items-center justify-center';

  const sizeStyles = {
    sm: 'py-1.5 px-3 text-xs',
    md: 'py-2 px-4 text-sm',
    lg: 'py-2.5 px-6 text-base',
  };

  const variantStyles = {
    primary: `bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500 ${disabled || isLoading ? 'bg-blue-400 cursor-not-allowed' : ''}`,
    secondary: `bg-gray-600 hover:bg-gray-700 text-white focus:ring-gray-500 ${disabled || isLoading ? 'bg-gray-400 cursor-not-allowed' : ''}`,
    danger: `bg-red-600 hover:bg-red-700 text-white focus:ring-red-500 ${disabled || isLoading ? 'bg-red-400 cursor-not-allowed' : ''}`,
    outline: `bg-transparent hover:bg-blue-50 text-blue-700 border border-blue-600 focus:ring-blue-500 ${disabled || isLoading ? 'text-blue-400 border-blue-400 cursor-not-allowed' : ''}`,
    ghost: `bg-transparent hover:bg-gray-100 text-gray-700 focus:ring-gray-500 ${disabled || isLoading ? 'text-gray-400 cursor-not-allowed' : ''}`,
    link: `bg-transparent text-blue-600 hover:text-blue-800 hover:underline focus:ring-blue-500 p-0 ${disabled || isLoading ? 'text-blue-400 cursor-not-allowed' : ''}`,
  };

  return (
    <button
      type={type}
      onClick={onClick}
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : null}
      {children}
    </button>
  );
};

export default Button;