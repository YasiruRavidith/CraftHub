// src/pages/community/ForumsPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import forumService from '../../services/forumService';
import ForumCategoryCard from './ForumCategoryCard';
import ThreadListItem from './ThreadListItem';
import Loader from '../../components/common/Loader';
import Button from '../../components/common/Button';
import Pagination from '../../components/common/Pagination'; // Assuming you might paginate threads

const THREADS_PER_PAGE = 15;

const ForumsPage = () => {
  const [categories, setCategories] = useState([]);
  const [threads, setThreads] = useState([]); // For "Recent Threads" or a specific category
  const [loadingCategories, setLoadingCategories] = useState(true);
  const [loadingThreads, setLoadingThreads] = useState(true);
  const [error, setError] = useState('');
  
  // TODO: Add pagination for threads if showing many
  // const [currentPage, setCurrentPage] = useState(1);
  // const [totalPages, setTotalPages] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      setLoadingCategories(true);
      setLoadingThreads(true);
      setError('');
      try {
        const [categoriesData, threadsData] = await Promise.all([
          forumService.getForumCategories(),
          forumService.getForumThreads({ page_size: THREADS_PER_PAGE }) // Fetch recent threads
        ]);
        setCategories(Array.isArray(categoriesData) ? categoriesData : categoriesData.results || []); // Handle both paginated and non-paginated
        setThreads(threadsData.results || []);
        // setTotalPages(Math.ceil((threadsData.count || 0) / THREADS_PER_PAGE));
      } catch (err) {
        setError('Failed to load forum data. Please try again later.');
        console.error("Forum data fetch error:", err);
      }
      setLoadingCategories(false);
      setLoadingThreads(false);
    };
    fetchData();
  }, []);

  // const handleThreadPageChange = (page) => { ... };

  if (loadingCategories && loadingThreads) return <Loader text="Loading forums..." />;
  if (error) return <p className="text-center text-red-500 p-4 bg-red-100 rounded">{error}</p>;

  return (
    <div className="container-mx">
      <div className="flex justify-between items-center my-6">
        <h1 className="text-3xl font-bold text-gray-800">Forums</h1>
        {/* TODO: Link to "Create New Thread" page/modal */}
        <Link to="/community/threads/create">
            <Button variant="primary">Start New Discussion</Button>
        </Link>
      </div>

      <h2 className="text-2xl font-semibold text-gray-700 mb-4">Categories</h2>
      {loadingCategories ? <Loader text="Loading categories..." /> : (
        categories.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {categories.map(category => (
              <ForumCategoryCard key={category.id || category.slug} category={category} />
            ))}
          </div>
        ) : <p className="text-gray-500">No forum categories available.</p>
      )}

      <h2 className="text-2xl font-semibold text-gray-700 mb-4">Recent Discussions</h2>
      {loadingThreads ? <Loader text="Loading recent discussions..." /> : (
        threads.length > 0 ? (
          <ul className="bg-white shadow rounded-md divide-y divide-gray-200">
            {threads.map(thread => (
              <ThreadListItem key={thread.id || thread.slug} thread={thread} />
            ))}
          </ul>
        ) : <p className="text-gray-500">No recent discussions.</p>
      )}
      {/* TODO: Add Pagination for threads if applicable */}
    </div>
  );
};

export default ForumsPage;