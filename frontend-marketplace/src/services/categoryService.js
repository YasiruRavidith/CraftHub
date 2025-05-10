// src/services/categoryService.js
import apiClient from './apiClient';

const getCategories = async (params = {}) => {
  try {
    const response = await apiClient.get('/listings/categories/', { params });
    // Assuming backend returns a list or paginated response with 'results'
    return Array.isArray(response.data) ? response.data : response.data.results || [];
  } catch (error)
 {
    console.error('Error fetching categories:', error.response?.data || error.message);
    throw error;
  }
};

export default {
  getCategories,
};