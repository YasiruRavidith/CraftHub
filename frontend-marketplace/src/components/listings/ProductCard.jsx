// src/components/listings/ProductCard.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { truncateText } from '../../utils/helpers'; // We'll create this

const ProductCard = ({ item, type = 'material' }) => { // type can be 'material' or 'design'
  if (!item) return null;

  const detailUrl = type === 'material' ? `/materials/${item.slug}` : `/designs/${item.slug}`;
  const imageUrl = item.main_image_url || item.thumbnail_image_url || `https://via.placeholder.com/300x200?text=${type === 'material' ? item.name : item.title}`;
  const name = type === 'material' ? item.name : item.title;
  const price = item.price_per_unit || item.price;
  const unit = item.unit || (type === 'design' ? '(license)' : '');
  const owner = item.seller?.username || item.designer?.username || 'N/A';

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-lg transition-shadow duration-300 overflow-hidden flex flex-col">
      <Link to={detailUrl} className="block">
        <img
          src={imageUrl}
          alt={name}
          className="w-full h-56 object-cover"
        />
      </Link>
      <div className="p-4 flex flex-col flex-grow">
        <h3 className="text-lg font-semibold text-gray-800 mb-1 hover:text-blue-600">
          <Link to={detailUrl}>{truncateText(name, 50)}</Link>
        </h3>
        <p className="text-xs text-gray-500 mb-2">By: {owner}</p>
        {item.description && (
          <p className="text-sm text-gray-600 mb-3 flex-grow">
            {truncateText(item.description, 80)}
          </p>
        )}
        {price !== undefined && price !== null && (
          <p className="text-md font-bold text-blue-700 mb-3">
            ${parseFloat(price).toFixed(2)} {unit && `/ ${unit}`}
          </p>
        )}
        <Link
          to={detailUrl}
          className="mt-auto inline-block text-center w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors text-sm font-medium"
        >
          View Details
        </Link>
      </div>
    </div>
  );
};

export default ProductCard;