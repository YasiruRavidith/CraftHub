// src/pages/DesignSearchPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import productService from '../services/productService';
import ProductCard from '../components/listings/ProductCard';
import Loader from '../components/common/Loader';
import Pagination from '../components/common/Pagination';
// import SearchFiltersComponent from '../components/listings/SearchFiltersComponent'; // For advanced filters

const ITEMS_PER_PAGE = 12;

const DesignSearchPage = () => {
  const [designs, setDesigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  // const [filters, setFilters] = useState({});

  const fetchDesigns = useCallback(async (page) => {
    setLoading(true);
    setError('');
    try {
      // const params = { ...filters, page: page, page_size: ITEMS_PER_PAGE };
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
  }, []); // Add filters to dependency array if used

  useEffect(() => {
    fetchDesigns(1);
  }, [fetchDesigns]);

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      fetchDesigns(page);
    }
  };

  // const handleFilterChange = (newFilters) => {
  //   setFilters(newFilters);
  //   fetchDesigns(1, newFilters);
  // };

  return (
    <div className="container-mx">
      <h1 className="text-3xl font-bold my-6 text-slate-950">Discover Designs</h1>
      {/* <SearchFiltersComponent onFilterChange={handleFilterChange} type="design" /> */}
      <div className="mb-6 p-4 bg-orange-50 rounded-lg shadow">
        <input 
          type="text" 
          placeholder="Search designs by title, designer, tags..." 
          className="p-2 border border-gray-300 rounded w-full md:w-1/2 focus:ring-teal-500 focus:border-teal-500" 
          // TODO: Implement actual search functionality by updating filters state
        />
      </div>

      {loading && <Loader text="Fetching designs..." />}
      {error && <p className="text-center text-red-500 p-10 text-lg bg-red-50 rounded-md">{error}</p>}
      
      {!loading && !error && designs.length === 0 && (
        <p className="text-center text-slate-600 p-10 text-lg">No designs found.</p>
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