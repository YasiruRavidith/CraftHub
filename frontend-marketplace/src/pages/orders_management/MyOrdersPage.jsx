// src/pages/orders_management/MyOrdersPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import orderService from '../../services/orderService';
import Loader from '../../components/common/Loader';
import Pagination from '../../components/common/Pagination';
import { useAuth } from '../../contexts/AuthContext';
import { formatDate, formatCurrency } from '../../utils/formatters';

const ITEMS_PER_PAGE = 10;

const MyOrdersPage = () => {
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const fetchMyOrders = useCallback(async (page) => {
    if (!user) return;
    setLoading(true);
    setError('');
    try {
      const params = { page: page, page_size: ITEMS_PER_PAGE };
      // Backend's OrderViewSet.get_queryset filters for the current user
      const data = await orderService.getMyOrders(params);
      setOrders(data.results || []);
      setTotalPages(Math.ceil((data.count || 0) / ITEMS_PER_PAGE));
      setCurrentPage(page);
    } catch (err) {
      setError('Failed to fetch your orders. Please try again later.');
      console.error("Fetch my orders error:", err);
    }
    setLoading(false);
  }, [user]);

  useEffect(() => {
    if (user) {
      fetchMyOrders(1);
    }
  }, [fetchMyOrders, user]);

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      fetchMyOrders(page);
    }
  };

  if (!user) return <p>Please log in to see your orders.</p>;


  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-800 mb-6">My Orders</h1>

      {loading && <Loader text="Loading your orders..." />}
      {error && <p className="text-center text-red-500 p-4 bg-red-100 rounded">{error}</p>}

      {!loading && !error && orders.length === 0 && (
        <div className="text-center p-10 bg-white rounded-lg shadow">
          <p className="text-gray-600 text-lg">You have no orders yet.</p>
          {user.user_type === 'buyer' && (
            <Link to="/materials" className="mt-4 inline-block">
                <Button variant="primary" size="lg">Browse Products</Button>
            </Link>
          )}
        </div>
      )}

      {!loading && !error && orders.length > 0 && (
        <>
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul role="list" className="divide-y divide-gray-200">
              {orders.map((order) => (
                <li key={order.id}>
                  <Link to={`/dashboard/orders/${order.id}`} className="block hover:bg-gray-50">
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-blue-600 truncate">
                          Order ID: {order.id.substring(0,8)}...
                        </p>
                        <div className="ml-2 flex-shrink-0 flex">
                          <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            order.status === 'completed' || order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                            order.status === 'pending_payment' || order.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                            order.status === 'cancelled_by_buyer' || order.status === 'cancelled_by_seller' || order.status === 'payment_failed' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {order.status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </p>
                        </div>
                      </div>
                      <div className="mt-2 sm:flex sm:justify-between">
                        <div className="sm:flex">
                          <p className="flex items-center text-sm text-gray-500">
                            {/* Placeholder for items summary */}
                            {order.items?.length || 0} item(s)
                          </p>
                          <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                            Total: {formatCurrency(order.order_total, order.items?.[0]?.currency || 'USD')}
                          </p>
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                          <p>Ordered: {formatDate(order.created_at)}</p>
                        </div>
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </div>
  );
};

export default MyOrdersPage;