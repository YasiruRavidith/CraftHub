// src/pages/dashboards/SellerDashboardPage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../../components/common/Button';

const SellerDashboardPage = () => {
  // Fetch seller-specific data: new orders, listing stats, messages etc.
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-800">Seller Dashboard</h1>
        <Link to="/dashboard/listings/create?type=material">
            <Button variant="primary">Add New Material</Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Example Stats Cards */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-700">Active Listings</h3>
          <p className="text-3xl font-bold text-blue-600">15</p> {/* Placeholder */}
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-700">New Orders (Month)</h3>
          <p className="text-3xl font-bold text-green-600">5</p> {/* Placeholder */}
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-700">Pending RFQs</h3>
          <p className="text-3xl font-bold text-yellow-600">2</p> {/* Placeholder */}
        </div>
      </div>

      {/* Recent Activity / Orders List (Placeholder) */}
      <div className="mt-8 bg-white p-6 rounded-lg shadow">
        <h3 className="text-xl font-semibold text-gray-700 mb-4">Recent Activity</h3>
        <ul className="space-y-3">
          <li className="text-sm text-gray-600">Order #1234 received - Processing</li>
          <li className="text-sm text-gray-600">New RFQ for "Custom Silk Print"</li>
          <li className="text-sm text-gray-600">Material "Organic Cotton" stock updated</li>
        </ul>
      </div>
    </div>
  );
};

export default SellerDashboardPage;