// src/pages/MaterialSearchPage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { debounce } from 'lodash'; // npm install lodash
import productService from '../services/productService';
import ProductCard from '../components/listings/ProductCard';
import Loader from '../components/common/Loader';
import Pagination from '../components/common/Pagination';
import { Search, XCircle, Filter, AlertTriangle } from 'lucide-react'; // Icons

const ITEMS_PER_PAGE = 12;
const DEBOUNCE_DELAY = 500; // Increased debounce for better UX

const MaterialSearchPage = () => {
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  // const [filtersOpen, setFiltersOpen] = useState(false); // For a filter sidebar/modal

  const fetchMaterials = useCallback(async (page, query = '') => {
    setLoading(true);
    setError('');
    try {
      const params = { 
        page, 
        page_size: ITEMS_PER_PAGE,
        search: query.trim() // Ensure your backend 'search' filter is configured for MaterialViewSet
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
    () => debounce((query) => {
      setCurrentPage(1); // Reset to page 1 on new search
      fetchMaterials(1, query);
    }, DEBOUNCE_DELAY),
    [fetchMaterials] // fetchMaterials is stable due to its own useCallback
  );

  useEffect(() => {
    // Initial fetch and when search query changes (debounced)
    debouncedFetch(searchQuery);
    // Cleanup function to cancel any pending debounced calls when the component unmounts or searchQuery changes before debounce triggers
    return () => debouncedFetch.cancel();
  }, [searchQuery, debouncedFetch]);

  const handlePageChange = useCallback((page) => {
    if (page >= 1 && page <= totalPages && page !== currentPage) { // Avoid refetching same page
      fetchMaterials(page, searchQuery);
    }
  }, [fetchMaterials, totalPages, searchQuery, currentPage]);

  const handleSearchChange = useCallback((e) => {
    setSearchQuery(e.target.value);
  }, []);
  
  const clearSearch = useCallback(() => {
    setSearchQuery('');
    // debouncedFetch will be called automatically by the useEffect for searchQuery
  }, []);


  const renderContent = () => { // Removed useMemo, can cause stale closures with handlers if not careful with deps
    if (loading && materials.length === 0) { // Show loader only on initial load or when no data yet
        return <div className="py-20"><Loader text="Fetching materials..." /></div>;
    }
    if (error) {
        return (
            <div className="text-center py-20 px-6 bg-red-50 border border-red-200 rounded-lg">
                <AlertTriangle size={48} className="mx-auto text-red-500 mb-4" />
                <p className="text-xl text-red-700 font-semibold">{error}</p>
                <p className="text-sm text-red-600 mt-1">Please check your connection or try refreshing.</p>
            </div>
        );
    }
    if (!loading && materials.length === 0) {
        return (
            <div className="text-center py-20 px-6 bg-slate-50 rounded-lg">
                <Search size={48} className="mx-auto text-slate-400 mb-4" />
                <p className="text-xl text-slate-700 font-semibold">No Materials Found</p>
                <p className="text-sm text-slate-500 mt-1">
                    {searchQuery ? "Try adjusting your search query." : "There are currently no materials listed."}
                </p>
            </div>
        );
    }

    return (
      <>
        {loading && <div className="absolute top-0 left-0 w-full h-2  bg-purple-200 animate-pulse rounded-t-lg"></div>}
        <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-5 transition-opacity duration-300 ${loading ? 'opacity-50' : 'opacity-100'}`}>
          {materials.map(material => (
            <ProductCard key={material.id || material.slug} item={material} type="material" />
          ))}
        </div>
        {totalPages > 1 && (
            <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={handlePageChange}
            />
        )}
      </>
    );
  };

  return (
    <div className="container-mx py-8 text-slate-950"> {/* Main text color */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-stone-200 mb-4 md:mb-0">
          Browse Materials
        </h1>
        <div className="flex items-center space-x-3 w-full md:w-auto">
          <div className="relative flex-grow md:flex-grow-0 md:w-72">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400 pointer-events-none">
              <Search size={20} className="text-slate-400" />
            </div>
            <input 
              type="text" 
              value={searchQuery}
              onChange={handleSearchChange}
              placeholder="Search..." 
              className="w-full pl-10 pr-10 py-2.5 border border-slate-300 rounded-lg text-slate-400 shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
            />
            {searchQuery && (
              <div 
                onClick={clearSearch} 
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-purple-600"
                aria-label="Clear search"
              >
                <XCircle size={18} />
              </div>
            )}
          </div>
          {/* <button 
            onClick={() => setFiltersOpen(true)} 
            className="p-2.5 border border-slate-300 rounded-lg shadow-sm text-slate-700 hover:bg-purple-50 focus:outline-none focus:ring-2 focus:ring-purple-500 flex items-center"
          >
            <Filter size={20} className="mr-2" /> Filters
          </button> */}
        </div>
      </div>
      
      {/* Placeholder for Advanced Filters Sidebar/Modal if setFiltersOpen is true */}
      {/* {filtersOpen && <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setFiltersOpen(false)}>...Filter Component...</div>} */}
      
      {renderContent()}
    </div>
  );
};

export default React.memo(MaterialSearchPage); 
// React.memo might not be very effective here if fetchMaterials or other props passed to children change reference often.
// Consider if it's truly needed or if child components should be memoized instead.