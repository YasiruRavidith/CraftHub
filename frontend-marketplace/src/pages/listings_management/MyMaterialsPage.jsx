// src/pages/listings_management/MyMaterialsPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import productService from '../../services/productService'; // Assuming getMaterials can filter by owner
import ProductCard from '../../components/listings/ProductCard';
import Loader from '../../components/common/Loader';
import Button from '../../components/common/Button';
import Pagination from '../../components/common/Pagination';
import { useAuth } from '../../contexts/AuthContext';

const ITEMS_PER_PAGE = 8;

const MyMaterialsPage = () => {
  const { user } = useAuth();
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const fetchMyMaterials = useCallback(async (page) => {
    if (!user) return;
    setLoading(true);
    setError('');
    try {
      // Backend needs to support filtering by 'seller__username=me' or 'owner=me'
      // Or have a dedicated endpoint like /listings/materials/my/
      // For now, assuming productService.getMaterials can take a seller_id or username
      const params = {
        page: page,
        page_size: ITEMS_PER_PAGE,
        seller__username: user.username, // Filter by current user's username
        // OR if your backend /listings/materials/ supports an "owner=me" query param for current user:
        // owner: 'me'
      };
      const data = await productService.getMaterials(params);
      setMaterials(data.results || []);
      setTotalPages(Math.ceil((data.count || 0) / ITEMS_PER_PAGE));
      setCurrentPage(page);
    } catch (err) {
      setError('Failed to fetch your materials. Please try again later.');
      console.error("Fetch my materials error:", err);
    }
    setLoading(false);
  }, [user]); // Depend on user

  useEffect(() => {
    if (user) {
      fetchMyMaterials(1);
    }
  }, [fetchMyMaterials, user]);

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      fetchMyMaterials(page);
    }
  };

  // TODO: Implement deleteMaterial and navigate to edit page
  // const handleDelete = async (materialId) => {
  //   if (window.confirm('Are you sure you want to delete this material?')) {
  //     try {
  //       await productService.deleteMaterial(materialId);
  //       fetchMyMaterials(currentPage); // Refresh list
  //     } catch (err) {
  //       alert('Failed to delete material.');
  //     }
  //   }
  // };

  if (!user) { // Should be caught by PrivateRoute, but good to have a check
    return <p>Please log in to see your materials.</p>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-800">My Materials</h1>
        <Link to="/dashboard/listings/create?type=material"> {/* Or a dedicated create material page */}
          <Button variant="primary">Add New Material</Button>
        </Link>
      </div>

      {loading && <Loader text="Loading your materials..." />}
      {error && <p className="text-center text-red-500 p-4 bg-red-100 rounded">{error}</p>}
      
      {!loading && !error && materials.length === 0 && (
        <div className="text-center p-10 bg-white rounded-lg shadow">
          <p className="text-gray-600 text-lg">You haven't listed any materials yet.</p>
          <Link to="/dashboard/listings/create?type=material" className="mt-4 inline-block">
            <Button variant="primary" size="lg">List Your First Material</Button>
          </Link>
        </div>
      )}

      {!loading && !error && materials.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {materials.map(material => (
              <div key={material.id || material.slug} className="relative">
                <ProductCard item={material} type="material" />
                <div className="absolute top-2 right-2 space-x-1">
                  {/* <Button size="sm" variant="outline" onClick={() => navigate(`/dashboard/listings/edit/material/${material.slug}`)}>Edit</Button> */}
                  {/* <Button size="sm" variant="danger" onClick={() => handleDelete(material.id)}>Delete</Button> */}
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

export default MyMaterialsPage;