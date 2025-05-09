// src/components/community/ThreadListItem.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { formatDate, formatDateTime } from '../../utils/formatters'; // Assuming formatDateTime exists

const ThreadListItem = ({ thread }) => {
  if (!thread) return null;

  // Construct thread URL based on category slug and thread slug
  const threadUrl = `/community/threads/${thread.slug}`;
  // Or if category is part of the URL: `/community/forums/${thread.category?.slug}/${thread.slug}`;
  // Adjust based on your ForumThreadPage routing.

  return (
    <li className="py-4 px-2 hover:bg-gray-50 transition-colors">
      <div className="flex items-center space-x-3">
        <div className="flex-shrink-0">
          {/* Placeholder for user avatar */}
          <img
            className="h-10 w-10 rounded-full"
            src={thread.author?.profile?.profile_picture || `https://ui-avatars.com/api/?name=${thread.author?.username || 'A'}&size=40`}
            alt={thread.author?.username || 'Author'}
          />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-gray-900 truncate">
            <Link to={threadUrl} className="hover:underline hover:text-blue-600">
              {thread.is_pinned && <span className="text-yellow-500 mr-1">📌</span>}
              {thread.is_locked && <span className="text-red-500 mr-1">🔒</span>}
              {thread.title}
            </Link>
          </p>
          <p className="text-xs text-gray-500">
            Started by <span className="font-medium">{thread.author?.username || 'Unknown'}</span>
            {' in '}
            <Link to={`/community/forums/${thread.category_slug}`} className="hover:underline text-blue-500">
                {thread.category?.name || thread.category_slug || 'General'}
            </Link>
            {' on '}{formatDate(thread.created_at)}
          </p>
        </div>
        <div className="hidden sm:flex flex-col items-end text-xs text-gray-500 whitespace-nowrap">
          <p>{thread.posts_count || 0} replies</p>
          <p>{thread.views_count || 0} views</p>
          <p>Last post: {formatDateTime(thread.last_activity_at || thread.updated_at)}</p>
          {thread.last_activity_by && <p>by {thread.last_activity_by.username}</p>}
        </div>
      </div>
    </li>
  );
};

export default ThreadListItem;