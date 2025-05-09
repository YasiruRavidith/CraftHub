// src/pages/HomePage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/common/Button';

const HomePage = () => {
  return (
    <div className="text-center py-10 md:py-20">
      <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-gray-800 mb-6">
        B2B Garment Marketplace
      </h1>
      <p className="text-lg md:text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
        Discover, connect, and collaborate with manufacturers, designers, and material suppliers in the global garment industry.
      </p>
      <div className="space-y-4 sm:space-y-0 sm:space-x-4">
        <Link to="/materials">
          <Button variant="primary" size="lg">Browse Materials</Button>
        </Link>
        <Link to="/auth/register">
          <Button variant="outline" size="lg">Join as a Member</Button>
        </Link>
      </div>
      {/* Placeholder for featured items or categories */}
      <div className="mt-16">
        <h2 className="text-2xl font-semibold mb-6">Featured</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Placeholder cards */}
          <div className="p-6 bg-white rounded-lg shadow-md">Featured Category 1</div>
          <div className="p-6 bg-white rounded-lg shadow-md">Featured Product 1</div>
          <div className="p-6 bg-white rounded-lg shadow-md">Featured Designer 1</div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;