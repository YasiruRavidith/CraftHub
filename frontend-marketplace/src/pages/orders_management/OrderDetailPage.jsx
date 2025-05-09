// src/pages/orders_management/OrderDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import orderService from '../../services/orderService';
import Loader from '../../components/common/Loader';
import Button from '../../components/common/Button';
import { useAuth } from '../../contexts/AuthContext';
import { formatDate, formatCurrency, formatDateTime } from '../../utils/formatters';

const OrderDetailPage = () => {
  const { orderId } = useParams();
  const { user } = useAuth();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchOrderDetails = async () => {
      if (!orderId) return;
      setLoading(true);
      setError('');
      try {
        const data = await orderService.getOrderDetail(orderId);
        setOrder(data);
      } catch (err) {
        setError('Failed to fetch order details. You may not have permission to view this order.');
        console.error("Fetch order detail error:", err);
      }
      setLoading(false);
    };
    fetchOrderDetails();
  }, [orderId]);

  // TODO: Function to handle order status updates (e.g., buyer cancels, seller updates)
  // const handleUpdateStatus = async (newStatus) => { ... };

  if (loading) return <Loader text="Loading order details..." />;
  if (error) return <p className="text-center text-red-500 p-4 bg-red-100 rounded">{error}</p>;
  if (!order) return <p className="text-center text-gray-600 p-10">Order not found.</p>;

  const isBuyer = user?.id === order.buyer?.id;
  // const isSellerInOrder = order.items?.some(item => item.seller?.id === user?.id);

  return (
    <div className="bg-white p-6 md:p-8 rounded-lg shadow-xl max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 pb-4 border-b">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800">Order Details</h1>
          <p className="text-sm text-gray-500">Order ID: <span className="font-mono">{order.id}</span></p>
        </div>
        <div className={`mt-2 sm:mt-0 px-3 py-1 text-sm font-semibold rounded-full inline-block ${
            order.status === 'completed' || order.status === 'delivered' ? 'bg-green-100 text-green-800' :
            order.status === 'pending_payment' || order.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
            order.status === 'cancelled_by_buyer' || order.status === 'cancelled_by_seller' || order.status === 'payment_failed' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
        }`}>
            Status: {order.status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Buyer Information</h3>
          <p className="text-sm text-gray-600">Name: {order.buyer?.first_name || ''} {order.buyer?.last_name || order.buyer?.username}</p>
          <p className="text-sm text-gray-600">Email: {order.buyer?.email}</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Order Summary</h3>
          <p className="text-sm text-gray-600">Date Placed: {formatDateTime(order.created_at)}</p>
          <p className="text-sm text-gray-600 font-semibold mt-1">Order Total: {formatCurrency(order.order_total)}</p>
        </div>
      </div>
      
      {order.related_quote_details && (
        <div className="mb-6 p-4 bg-blue-50 rounded-md">
          <h3 className="text-md font-semibold text-blue-700 mb-1">This order was created from a quote:</h3>
          <p className="text-sm text-blue-600">Quote ID: {order.related_quote_details.id}</p>
          {order.related_quote_details.rfq_title && <p className="text-sm text-blue-600">Original RFQ: {order.related_quote_details.rfq_title}</p>}
        </div>
      )}


      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-3">Items in this Order</h3>
        <div className="border rounded-md overflow-hidden">
          <ul className="divide-y divide-gray-200">
            {order.items?.map(item => (
              <li key={item.id} className="p-4 flex flex-col sm:flex-row justify-between items-start">
                <div className="flex-grow mb-2 sm:mb-0">
                  <p className="font-medium text-gray-800">{item.item_name || item.custom_item_description}</p>
                  <p className="text-xs text-gray-500">
                    Product ID: {item.material_id || item.design_id || 'Custom'}
                  </p>
                  <p className="text-xs text-gray-500">Sold by: {item.seller_username || 'N/A'}</p>
                </div>
                <div className="text-sm text-gray-600 text-left sm:text-right">
                  <p>{item.quantity} x {formatCurrency(item.unit_price)}</p>
                  <p className="font-semibold">{formatCurrency(item.subtotal)}</p>
                </div>
              </li>
            ))}
            {(!order.items || order.items.length === 0) && <li className="p-4 text-sm text-gray-500">No items in this order.</li>}
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Shipping Address</h3>
          <pre className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md whitespace-pre-wrap">
            {order.shipping_address || "Not specified"}
          </pre>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Billing Address</h3>
           <pre className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md whitespace-pre-wrap">
            {order.billing_address || "Same as shipping or not specified"}
          </pre>
        </div>
      </div>
      
      {order.payment_intent_id && (
        <p className="text-xs text-gray-400 mt-4">Payment Intent ID: {order.payment_intent_id}</p>
      )}

      {/* TODO: Action buttons based on user role and order status */}
      <div className="mt-8 border-t pt-6 flex justify-end space-x-3">
        <Link to="/dashboard/my-orders">
          <Button variant="ghost">Back to My Orders</Button>
        </Link>
        {/* Example: Buyer can cancel if order is 'pending_payment' or 'processing' */}
        {isBuyer && (order.status === 'pending_payment' || order.status === 'processing') && (
          <Button variant="danger" /* onClick={() => handleUpdateStatus('cancelled_by_buyer')} */ >
            Cancel Order
          </Button>
        )}
      </div>
    </div>
  );
};

export default OrderDetailPage;