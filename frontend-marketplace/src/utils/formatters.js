// src/utils/formatters.js
export const formatDate = (dateString, options = {}) => {
  if (!dateString) return 'N/A';
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options,
  };
  try {
    return new Date(dateString).toLocaleDateString(undefined, defaultOptions);
  } catch (e) {
    return dateString; // Return original if parsing fails
  }
};

export const formatCurrency = (amount, currency = 'USD', options = {}) => {
  if (amount === null || amount === undefined) return 'N/A';
  const defaultOptions = {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    ...options,
  };
  try {
    return new Intl.NumberFormat(undefined, defaultOptions).format(amount);
  } catch (e) {
    return `${parseFloat(amount).toFixed(2)} ${currency}`;
  }
};

export const formatDateTime = (dateString, options = {}) => {
    if (!dateString) return 'N/A';
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      ...options,
    };
    try {
      return new Date(dateString).toLocaleString(undefined, defaultOptions);
    } catch (e) {
      return dateString;
    }
  };