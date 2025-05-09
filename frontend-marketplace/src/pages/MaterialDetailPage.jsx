// src/pages/MaterialDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import productService from '../services/productService';
import Loader from '../components/common/Loader';
import Button from '../components/common/Button';
import { formatDate, formatCurrency } from '../utils/formatters'; // Example

const MaterialDetailPage = () => {
  const { slug } = useParams(); // Or :id depending on your router setup
  const [material, setMaterial] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchMaterial = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await productService.getMaterialBySlug(slug);
        setMaterial(data);
      } catch (err) {
        setError('Failed to fetch material details.');
        console.error(err);
      }
      setLoading(false);
    };
    if (slug) {
      fetchMaterial();
    }
  }, [slug]);

  if (loading) return <Loader text="Loading material details..." />;
  if (error) return <p className="text-center text-red-500 p-10">{error}</p>;
  if (!material) return <p className="text-center p-10">Material not found.</p>;

  return (
    <div className="container-mx py-8">
      <div className="grid md:grid-cols-2 gap-8 bg-white p-6 rounded-lg shadow-lg">
        <div>
          <img
            src={material.main_image_url || `https://via.placeholder.com/600x400?text=${material.name}`}
            alt={material.name}
            className="w-full h-auto object-cover rounded-lg shadow-md"
          />
          {/* TODO: Image gallery for additional_images */}
        </div>
        <div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800 mb-3">{material.name}</h1>
          <p className="text-sm text-gray-500 mb-4">By: {material.seller?.username || 'N/A'}</p>
          
          <div className="mb-4 p-4 bg-blue-50 rounded-md">
            <p className="text-3xl font-bold text-blue-600">
                {formatCurrency(material.price_per_unit, material.currency || 'USD')} / {material.unit}
            </p>
            {material.minimum_order_quantity > 1 && (
                 <p className="text-sm text-gray-600">Min. Order: {material.minimum_order_quantity} {material.unit}s</p>
            )}
          </div>

          <p className="text-gray-700 mb-6 leading-relaxed">{material.description || "No description available."}</p>
          
          <h3 className="text-lg font-semibold mb-2 text-gray-700">Details:</h3>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mb-6">
            {material.composition && <li><strong>Composition:</strong> {material.composition}</li>}
            {material.weight_gsm && <li><strong>Weight:</strong> {material.weight_gsm} GSM</li>}
            {material.width_cm && <li><strong>Width:</strong> {material.width_cm} cm</li>}
            {material.country_of_origin && <li><strong>Origin:</strong> {material.country_of_origin}</li>}
            {material.lead_time_days && <li><strong>Lead Time:</strong> {material.lead_time_days} days</li>}
            {material.stock_quantity !== null && <li><strong>Stock:</strong> {material.stock_quantity > 0 ? `${material.stock_quantity} available` : 'Out of Stock'}</li>}
          </ul>

          {/* TODO: Certifications display */}
          {/* TODO: Tags display */}

          <div className="mt-6 flex space-x-4">
            <Button variant="primary" size="lg">Add to Cart / Request Quote</Button>
            <Button variant="outline" size="lg">Contact Seller</Button>
          </div>
        </div>
      </div>
      {/* TODO: Seller Information Section */}
      {/* TODO: Reviews and Ratings Section */}
    </div>
  );
};

export default MaterialDetailPage;