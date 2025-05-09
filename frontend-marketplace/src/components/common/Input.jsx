import React from 'react';

const Input = React.forwardRef(
  ({ type = 'text', label, id, name, error, className = '', ...props }, ref) => {
    const baseInputClasses =
      'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm';
    const errorInputClasses = 'border-red-500 focus:ring-red-500 focus:border-red-500';

    return (
      <div>
        {label && (
          <label htmlFor={id || name} className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        <input
          type={type}
          id={id || name}
          name={name}
          ref={ref}
          className={`${baseInputClasses} ${error ? errorInputClasses : ''} ${className}`}
          {...props}
        />
        {error && <p className="mt-1 text-xs text-red-600">{error.message || error}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input'; // for better debugging

export default Input;