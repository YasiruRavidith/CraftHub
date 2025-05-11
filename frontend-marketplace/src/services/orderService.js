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

const createOrderFromCart = async (cartData) => {
  // cartData should be an array of items, structured as the backend expects
  // e.g., items: [{ material_id: 'uuid', quantity: 2, unit_price: '10.00' }, ...]
  // The backend OrderSerializer's 'items' field expects this.
  // You might also need to pass shipping_address, billing_address if collected.
  try {
    const payload = {
      items: cartData.map(item => ({
        // Adjust keys to match what your OrderItemSerializer expects for creation within OrderSerializer
        // (e.g., material_id, design_id, custom_item_description, quantity, unit_price)
        [item.type === 'material' ? 'material_id' : 'design_id']: item.id, // Assuming item.id is the product's actual ID/UUID
        quantity: item.quantity,
        unit_price: item.price, // Ensure this is the correct price to record
        // custom_item_description: item.custom_description, // If applicable
        // seller_id: item.seller_id // Usually seller is derived by backend from product or quote
      })),
      // shipping_address: "Collected shipping address", // Add these if you have them
      // billing_address: "Collected billing address",
    };
    console.log("Sending order creation payload:", payload);
    const response = await apiClient.post('/orders/', payload); // POST to /api/v1/orders/
    return response.data; // The created order object
  } catch (error) {
    console.error('Error creating order from cart:', error.response?.data || error.message);
    throw error;
  }
};

// TODO: createOrder (if done from frontend directly, not just from quote), updateOrderStatus

export default {
  getMyOrders,
  getOrderDetail,
  createOrderFromCart,
};