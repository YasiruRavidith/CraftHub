// src/pages/DesignSearchPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import productService from '../services/productService';
import ProductCard from '../components/listings/ProductCard';
import Loader from '../components/common/Loader';
import Pagination from '../components/common/Pagination';

const ITEMS_PER_PAGE = 12;

const DesignSearchPage = () => {
  const [designs, setDesigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const fetchDesigns = useCallback(async (page) => {
    setLoading(true);
    setError('');
    try {
      const params = { page: page, page_size: ITEMS_PER_PAGE };
      const data = await productService.getDesigns(params);
      setDesigns(data.results || []);
      setTotalPages(Math.ceil((data.count || 0) / ITEMS_PER_PAGE));
      setCurrentPage(page);
    } catch (err) {
      setError('Failed to fetch designs. Please try again later.');
      console.error("Fetch designs error:", err);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchDesigns(1);
  }, [fetchDesigns]);

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      fetchDesigns(page);
    }
  };

  return (
    <div className="container-mx text-gray-950">
      <h1 className="text-3xl font-bold my-6 text-gray-800">Discover Designs</h1>
       <div className="mb-6 p-4 bg-gray-50 rounded-lg shadow">
        <input type="text" placeholder="Search designs..." className="p-2 border rounded w-full md:w-1/2" />
      </div>

      {loading && <Loader text="Fetching designs..." />}
      {error && <p className="text-center text-red-500 p-10 text-lg">{error}</p>}
      
      {!loading && !error && designs.length === 0 && (
        <p className="text-center text-gray-600 p-10 text-lg">No designs found.</p>
      )}

      {!loading && !error && designs.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {designs.map(design => (
              <ProductCard key={design.id || design.slug} item={design} type="design" />
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

export default DesignSearchPage;