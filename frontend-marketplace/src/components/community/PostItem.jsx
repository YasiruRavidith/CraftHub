// src/components/community/PostItem.jsx
import React from 'react';
import { formatDateTime } from '../../utils/formatters';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../common/Button';

const PostItem = ({ post, onEdit, onDelete }) => {
  const { user } = useAuth();
  if (!post) return null;

  const canEditOrDelete = user && (user.id === post.author?.id || user.is_staff);

  return (
    <div className="flex space-x-3 py-4 border-b border-gray-200 last:border-b-0">
      <img
        className="h-10 w-10 rounded-full flex-shrink-0"
        src={post.author?.profile?.profile_picture || `https://ui-avatars.com/api/?name=${post.author?.username || 'A'}&size=40`}
        alt={post.author?.username || 'Author'}
      />
      <div className="flex-1 space-y-1">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900">{post.author?.username || 'Unknown User'}</h3>
          <p className="text-xs text-gray-500">
            {formatDateTime(post.created_at)}
            {post.is_edited && <span className="italic ml-1">(edited)</span>}
          </p>
        </div>
        {/* Use a library to render Markdown or sanitize HTML if content can be rich text */}
        <div className="text-sm text-gray-700 prose max-w-none" dangerouslySetInnerHTML={{ __html: post.content.replace(/\n/g, '<br />') }}>
          {/* For plain text: <p className="whitespace-pre-wrap">{post.content}</p> */}
        </div>
        {canEditOrDelete && (
          <div className="flex space-x-2 mt-2">
            {/* <Button size="sm" variant="ghost" onClick={() => onEdit(post.id)}>Edit</Button>
            <Button size="sm" variant="ghost" className="text-red-600 hover:text-red-800" onClick={() => onDelete(post.id)}>Delete</Button> */}
          </div>
        )}
      </div>
    </div>
  );
};

export default PostItem;