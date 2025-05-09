// src/components/community/ForumCategoryCard.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { truncateText } from '../../utils/helpers';

const ForumCategoryCard = ({ category }) => {
  if (!category) return null;

  return (
    <div className="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow">
      <Link to={`/community/forums/${category.slug}`} className="block"> {/* Link to category-specific thread list */}
        <h3 className="text-lg font-semibold text-blue-600 hover:underline mb-1">{category.name}</h3>
      </Link>
      <p className="text-sm text-gray-600 mb-2">{truncateText(category.description, 100) || "No description."}</p>
      <div className="text-xs text-gray-500">
        <span>Threads: {category.threads_count || 0}</span>
        {/* Add last activity later if available from API */}
      </div>
    </div>
  );
};

export default ForumCategoryCard;