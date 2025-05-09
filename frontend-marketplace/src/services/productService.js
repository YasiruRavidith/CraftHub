// src/services/productService.js (or listingService.js)
import apiClient from './apiClient';

// --- Materials ---
const getMaterials = async (params = {}) => {
  try {
    const response = await apiClient.get('/listings/materials/', { params });
    return response.data; // Expects DRF paginated response: { count, next, previous, results }
  } catch (error) {
    console.error('Error fetching materials:', error.response?.data || error.message);
    throw error;
  }
};

const getMaterialBySlug = async (slug) => {
  try {
    const response = await apiClient.get(`/listings/materials/${slug}/`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching material ${slug}:`, error.response?.data || error.message);
    throw error;
  }
};

// Add createMaterial, updateMaterial, deleteMaterial if users can manage them
const createMaterial = async (materialData) => {
  // materialData will be FormData if images are included
  try {
    let headers = {};
    if (!(materialData instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    } // Axios sets Content-Type for FormData automatically

    const response = await apiClient.post('/listings/materials/', materialData, { headers });
    return response.data;
  } catch (error) {
    console.error('Error creating material:', error.response?.data || error.message);
    throw error;
  }
};

// --- Designs ---
const getDesigns = async (params = {}) => {
  try {
    const response = await apiClient.get('/listings/designs/', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching designs:', error.response?.data || error.message);
    throw error;
  }
};

const getDesignBySlug = async (slug) => {
  try {
    const response = await apiClient.get(`/listings/designs/${slug}/`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching design ${slug}:`, error.response?.data || error.message);
    throw error;
  }
};

// Add createDesign, updateDesign, deleteDesign

export default {
  getMaterials,
  getMaterialBySlug,
  createMaterial,
  getDesigns,
  getDesignBySlug,
};