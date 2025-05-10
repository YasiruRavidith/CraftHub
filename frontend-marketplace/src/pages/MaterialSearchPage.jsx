// src/pages/MaterialSearchPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { debounce } from 'lodash';
import productService from '../services/productService';
import ProductCard from '../components/listings/ProductCard';
import Loader from '../components/common/Loader';
import Pagination from '../components/common/Pagination';

const ITEMS_PER_PAGE = 12;
const DEBOUNCE_DELAY = 300;

const MaterialSearchPage = () => {
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchMaterials = useCallback(async (page, query = '') => {
    setLoading(true);
    setError('');
    try {
      const params = { 
        page, 
        page_size: ITEMS_PER_PAGE,
        search: query.trim()
      };
      const data = await productService.getMaterials(params);
      setMaterials(data.results || []);
      setTotalPages(Math.ceil((data.count || 0) / ITEMS_PER_PAGE));
      setCurrentPage(page);
    } catch (err) {
      setError('Failed to fetch materials. Please try again later.');
      console.error("Fetch materials error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const debouncedFetch = useMemo(
    () => debounce((query) => fetchMaterials(1, query), DEBOUNCE_DELAY),
    [fetchMaterials]
  );

  useEffect(() => {
    debouncedFetch(searchQuery);
    return () => debouncedFetch.cancel();
  }, [searchQuery, debouncedFetch]);

  const handlePageChange = useCallback((page) => {
    if (page >= 1 && page <= totalPages) {
      fetchMaterials(page, searchQuery);
    }
  }, [fetchMaterials, totalPages, searchQuery]);

  const handleSearchChange = useCallback((e) => {
    setSearchQuery(e.target.value);
  }, []);

  const renderContent = useMemo(() => {
    if (loading) return <Loader text="Fetching materials..." />;
    if (error) return <p className="text-center text-red-500 p-10 text-lg">{error}</p>;
    if (materials.length === 0) return <p className="text-center text-gray-600 p-10 text-lg">No materials found.</p>;

    return (
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
    );
  }, [materials, loading, error, currentPage, totalPages, handlePageChange]);

  return (
    <div className="container-mx text-gray-950">
      <h1 className="text-3xl font-bold my-6 text-gray-800">Browse Materials</h1>
      <div className="mb-6 p-4 bg-gray-50 rounded-lg shadow">
        <input 
          type="text" 
          value={searchQuery}
          onChange={handleSearchChange}
          placeholder="Search materials..." 
          className="p-2 border rounded w-full md:w-1/2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      {renderContent}
    </div>
  );
};

export default React.memo(MaterialSearchPage);