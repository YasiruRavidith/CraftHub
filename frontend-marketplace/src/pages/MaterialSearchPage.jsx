// src/pages/MaterialSearchPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import productService from '../services/productService';
import ProductCard from '../components/listings/ProductCard';
import Loader from '../components/common/Loader';
import Pagination from '../components/common/Pagination';
// import SearchFiltersComponent from '../components/listings/SearchFiltersComponent'; // Create this for complex filters

const ITEMS_PER_PAGE = 12; // Or get from backend if it supports page_size

const MaterialSearchPage = () => {
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  // const [filters, setFilters] = useState({}); // For search query, category, etc.

  const fetchMaterials = useCallback(async (page) => { // Removed filters for simplicity for now
    setLoading(true);
    setError('');
    try {
      // const params = { ...filters, page: page, page_size: ITEMS_PER_PAGE };
      const params = { page: page, page_size: ITEMS_PER_PAGE };
      const data = await productService.getMaterials(params);
      setMaterials(data.results || []);
      setTotalPages(Math.ceil((data.count || 0) / ITEMS_PER_PAGE));
      setCurrentPage(page);
    } catch (err) {
      setError('Failed to fetch materials. Please try again later.');
      console.error("Fetch materials error:", err);
    }
    setLoading(false);
  }, []); // [filters] add filters to dependency array if used

  useEffect(() => {
    fetchMaterials(1); // Fetch first page on initial load or when filters change
  }, [fetchMaterials]);

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      fetchMaterials(page);
    }
  };

  // const handleFilterChange = (newFilters) => {
  //   setFilters(newFilters);
  //   fetchMaterials(1, newFilters); // Reset to page 1 when filters change
  // };

  return (
    <div className="container-mx">
      <h1 className="text-3xl font-bold my-6 text-gray-800">Browse Materials</h1>
      {/* <SearchFiltersComponent onFilterChange={handleFilterChange} type="material" /> */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg shadow">
        {/* Placeholder for search input and basic filters */}
        <input type="text" placeholder="Search materials..." className="p-2 border rounded w-full md:w-1/2" />
      </div>

      {loading && <Loader text="Fetching materials..." />}
      {error && <p className="text-center text-red-500 p-10 text-lg">{error}</p>}
      
      {!loading && !error && materials.length === 0 && (
        <p className="text-center text-gray-600 p-10 text-lg">No materials found.</p>
      )}

      {!loading && !error && materials.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {materials.map(material => (
              <ProductCard key={material.id || material.slug} item={material} type="material" />
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

export default MaterialSearchPage;