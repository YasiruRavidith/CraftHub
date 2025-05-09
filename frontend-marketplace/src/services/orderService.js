// src/services/orderService.js
import apiClient from './apiClient';

const getMyOrders = async (params = {}) => {
  try {
    // Backend /api/v1/orders/ should filter by authenticated user (buyer or seller of items)
    const response = await apiClient.get('/orders/', { params });
    return response.data; // Expects DRF paginated response
  } catch (error) {
    console.error('Error fetching my orders:', error.response?.data || error.message);
    throw error;
  }
};

const getOrderDetail = async (orderId) => {
  try {
    const response = await apiClient.get(`/orders/${orderId}/`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching order ${orderId}:`, error.response?.data || error.message);
    throw error;
  }
};

// TODO: createOrder (if done from frontend directly, not just from quote), updateOrderStatus

export default {
  getMyOrders,
  getOrderDetail,
};