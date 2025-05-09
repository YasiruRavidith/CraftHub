// src/components/listings/MaterialCard.jsx
import React from 'react';
import { Link } from 'react-router-dom';

const MaterialCard = ({ material }) => {
  if (!material) return null;

  return (
    <div className="border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
      <img
        src={material.main_image_url || 'https://via.placeholder.com/300x200?text=Material'}
        alt={material.name}
        className="w-full h-48 object-cover rounded-md mb-4"
      />
      <h3 className="text-lg font-semibold mb-1">{material.name}</h3>
      <p className="text-sm text-gray-600 mb-2">Seller: {material.seller?.username || 'N/A'}</p>
      <p className="text-md font-bold text-blue-600 mb-3">
        ${parseFloat(material.price_per_unit).toFixed(2)} / {material.unit}
      </p>
      <Link
        to={`/materials/${material.slug}`} // Assuming slug-based routing for details
        className="text-sm text-blue-500 hover:underline"
      >
        View Details
      </Link>
    </div>
  );
};

export default MaterialCard;