// src/pages/listings_management/MyDesignsPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import productService from '../../services/productService';
import ProductCard from '../../components/listings/ProductCard';
import Loader from '../../components/common/Loader';
import Button from '../../components/common/Button';
import Pagination from '../../components/common/Pagination';
import { useAuth } from '../../contexts/AuthContext';

const ITEMS_PER_PAGE = 8;

const MyDesignsPage = () => {
  const { user } = useAuth();
  const [designs, setDesigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const fetchMyDesigns = useCallback(async (page) => {
    if (!user) return;
    setLoading(true);
    setError('');
    try {
      const params = {
        page: page,
        page_size: ITEMS_PER_PAGE,
        designer__username: user.username, // Filter by current user's username
      };
      const data = await productService.getDesigns(params); // Use getDesigns
      setDesigns(data.results || []);
      setTotalPages(Math.ceil((data.count || 0) / ITEMS_PER_PAGE));
      setCurrentPage(page);
    } catch (err) {
      setError('Failed to fetch your designs. Please try again later.');
      console.error("Fetch my designs error:", err);
    }
    setLoading(false);
  }, [user]);

  useEffect(() => {
    if (user) {
      fetchMyDesigns(1);
    }
  }, [fetchMyDesigns, user]);

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      fetchMyDesigns(page);
    }
  };

  // TODO: Implement deleteDesign and navigate to edit page

  if (!user) {
    return <p>Please log in to see your designs.</p>;
  }
   // Authorization check specific for designers
   if (!['designer', 'admin'].includes(user.user_type)) {
    return <p className="text-red-500 p-4">You are not authorized to view this page.</p>;
  }


  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-800">My Designs</h1>
        <Link to="/dashboard/listings/create?type=design">
          <Button variant="primary">Add New Design</Button>
        </Link>
      </div>

      {loading && <Loader text="Loading your designs..." />}
      {error && <p className="text-center text-red-500 p-4 bg-red-100 rounded">{error}</p>}
      
      {!loading && !error && designs.length === 0 && (
        <div className="text-center p-10 bg-white rounded-lg shadow">
          <p className="text-gray-600 text-lg">You haven't created any designs yet.</p>
          <Link to="/dashboard/listings/create?type=design" className="mt-4 inline-block">
            <Button variant="primary" size="lg">Create Your First Design</Button>
          </Link>
        </div>
      )}

      {!loading && !error && designs.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {designs.map(design => (
              <div key={design.id || design.slug} className="relative">
                <ProductCard item={design} type="design" />
                <div className="absolute top-2 right-2 space-x-1">
                  {/* Placeholders for edit/delete buttons */}
                  <Button size="sm" variant="outline" className="text-xs">Edit</Button>
                  <Button size="sm" variant="danger" className="text-xs">Del</Button>
                </div>
              </div>
            ))}
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

export default MyDesignsPage;