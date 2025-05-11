// src/components/listings/ProductCard.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { truncateText } from '../../utils/helpers';
import { Tag, UserCircle, DollarSign, ArrowRight } from 'lucide-react'; // Import icons

const ProductCard = ({ item, type = 'material' }) => {
  if (!item) return null;

  const detailUrl = type === 'material' ? `/materials/${item.slug}` : `/designs/${item.slug}`;
  
  // Use a more theme-consistent placeholder
  const placeholderText = type === 'material' ? (item.name || 'Material') : (item.title || 'Design');
  const imageUrl = item.main_image_url || item.thumbnail_image_url || `https://via.placeholder.com/400x300/A78BFA/FFFFFF?text=${encodeURIComponent(placeholderText.substring(0,15))}`; // Purple placeholder with white text

  const name = type === 'material' ? item.name : item.title;
  const price = item.price_per_unit || item.price;
  // Construct unit display carefully
  let unitDisplay = '';
  if (type === 'material' && item.unit) {
    unitDisplay = `/ ${item.unit}`;
  } else if (type === 'design' && price !== undefined && price !== null) {
    unitDisplay = item.licensing_terms ? '(License)' : '(Design)'; // Be more specific if possible
  }

  const owner = item.seller?.username || item.designer?.username || 'N/A';

  // Average rating display (optional)
  const rating = item.average_rating && parseFloat(item.average_rating) > 0 
                 ? parseFloat(item.average_rating).toFixed(1) 
                 : null;
  const reviewCount = item.review_count || 0;

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden flex flex-col h-full group transition-all duration-300 hover:shadow-2xl">
      <Link to={detailUrl} className="block relative overflow-hidden">
        <img
          src={imageUrl}
          alt={name}
          className="w-full h-56 object-cover transform transition-transform duration-500 group-hover:scale-110"
        />
        {/* Optional: Badge for new or featured items */}
        {/* <span className="absolute top-3 right-3 bg-purple-600 text-white text-xs font-semibold px-2 py-1 rounded">NEW</span> */}
      </Link>

      <div className="p-5 flex flex-col flex-grow">
        {/* Category/Tag Placeholder */}
        {item.category && (
          <Link 
            to={`/${type === 'material' ? 'materials' : 'designs'}?category=${item.category.slug}`} 
            className="text-xs text-purple-600 hover:text-purple-800 font-medium uppercase tracking-wider mb-1 inline-block"
          >
            {item.category.name}
          </Link>
        )}
        
        <h3 className="text-lg font-bold text-slate-800 mb-2 group-hover:text-purple-700 transition-colors">
          <Link to={detailUrl}>{truncateText(name, 45)}</Link>
        </h3>

        <div className="flex items-center text-xs text-slate-500 mb-3">
          <UserCircle size={14} className="mr-1.5 text-slate-400" />
          <span>By: </span>
          <Link to={`/profiles/${owner}`} className="ml-1 font-medium text-slate-600 hover:text-purple-600 hover:underline">
            {owner}
          </Link>
        </div>
        
        {/* Optional: Display rating */}
        {rating && (
            <div className="flex items-center text-xs text-slate-500 mb-3">
                <span className="text-yellow-500 mr-1">★</span>
                <span className="font-semibold text-slate-700">{rating}</span>
                <span className="ml-1">({reviewCount} reviews)</span>
            </div>
        )}


        {item.description && (
          <p className="text-sm text-slate-600 mb-4 flex-grow min-h-[3.5rem]"> 
            {/* min-h to keep card height somewhat consistent */}
            {truncateText(item.description, 70)}
          </p>
        )}

        {price !== undefined && price !== null && (
          <div className="flex items-center text-xl font-semibold text-purple-700 mb-4">
            <DollarSign size={20} className="mr-1.5 opacity-75" />
            {parseFloat(price).toFixed(2)}
            {unitDisplay && <span className="text-xs font-normal text-slate-500 ml-1">{unitDisplay}</span>}
          </div>
        )}

        <Link
          to={detailUrl}
          className="mt-auto w-full bg-purple-600 text-white py-2.5 px-4 rounded-lg hover:bg-purple-700 transition-colors text-sm font-semibold flex items-center justify-center group-hover:bg-purple-700"
        >
          View Details
          <ArrowRight size={16} className="ml-2 transform transition-transform duration-300 group-hover:translate-x-1" />
        </Link>
      </div>
    </div>
  );
};

export default ProductCard;