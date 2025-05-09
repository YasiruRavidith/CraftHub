// src/pages/community/ForumThreadPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import forumService from '../../services/forumService';
import Loader from '../../components/common/Loader';
import PostItem from './PostItem';
import Button from '../../components/common/Button';
import { useAuth } from '../../contexts/AuthContext';
import { useForm } from 'react-hook-form'; // For reply form

const ForumThreadPage = () => {
  const { categorySlug, threadSlug } = useParams(); // Adjust if your URL structure is different
  const effectiveSlug = threadSlug || categorySlug; // If only one slug param is used for thread
  const { isAuthenticated, user } = useAuth();

  const [thread, setThread] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [replyError, setReplyError] = useState('');
  const [isReplying, setIsReplying] = useState(false);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm();

  const fetchThreadAndPosts = useCallback(async () => {
    if (!effectiveSlug) return;
    setLoading(true);
    setError('');
    try {
      // ForumThreadDetailSerializer should return thread with posts
      const threadData = await forumService.getForumThreadBySlug(effectiveSlug);
      setThread(threadData);
      setPosts(threadData.posts || []); // Assuming posts are nested
    } catch (err) {
      setError('Failed to load thread. It might not exist or you may not have permission.');
      console.error("Fetch thread error:", err);
    }
    setLoading(false);
  }, [effectiveSlug]);

  useEffect(() => {
    fetchThreadAndPosts();
  }, [fetchThreadAndPosts]);

  const handlePostReply = async (data) => {
    if (!thread || !isAuthenticated) return;
    setReplyError('');
    try {
      const newPost = await forumService.createForumPost(thread.slug, { content: data.replyContent });
      setPosts(prevPosts => [...prevPosts, newPost]);
      reset(); // Clear the form
    } catch (err) {
      setReplyError(err.response?.data?.detail || "Failed to post reply.");
    }
  };
  
  // TODO: Edit/Delete Post functionality

  if (loading) return <Loader text="Loading discussion..." />;
  if (error) return <p className="text-center text-red-500 p-4 bg-red-100 rounded">{error}</p>;
  if (!thread) return <p className="text-center text-gray-600 p-10">Thread not found.</p>;

  return (
    <div className="container-mx">
      <div className="my-6 bg-white p-6 rounded-lg shadow-md">
        <div className="mb-4 pb-4 border-b">
            <nav aria-label="breadcrumb" className="text-sm text-gray-500 mb-2">
                <Link to="/community/forums" className="hover:underline">Forums</Link>
                {' > '}
                {thread.category && (
                    <>
                        <Link to={`/community/forums/${thread.category.slug}`} className="hover:underline">{thread.category.name}</Link>
                        {' > '}
                    </>
                )}
                <span className="text-gray-700">{thread.title}</span>
            </nav>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800">{thread.title}</h1>
            <p className="text-xs text-gray-500 mt-1">
                Started by {thread.author?.username} on {formatDate(thread.created_at)}
                {thread.is_locked && <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-700 text-xs font-semibold rounded-full">Locked</span>}
            </p>
        </div>

        <div className="space-y-4">
          {posts.map(post => (
            <PostItem key={post.id} post={post} /* onEdit={handleEdit} onDelete={handleDelete} */ />
          ))}
        </div>

        {isAuthenticated && !thread.is_locked && (
          <div className="mt-8 pt-6 border-t">
            <h3 className="text-lg font-semibold text-gray-700 mb-3">Post a Reply</h3>
            {replyError && <p className="text-red-500 text-sm mb-2">{replyError}</p>}
            <form onSubmit={handleSubmit(handlePostReply)}>
              <div>
                <textarea
                  rows="5"
                  {...register("replyContent", { required: "Reply content cannot be empty." })}
                  className={`w-full p-3 border rounded-md focus:ring-blue-500 focus:border-blue-500 ${errors.replyContent ? 'border-red-500' : 'border-gray-300'}`}
                  placeholder="Write your reply..."
                />
                {errors.replyContent && <p className="text-xs text-red-500 mt-1">{errors.replyContent.message}</p>}
              </div>
              <div className="mt-3">
                <Button type="submit" variant="primary" isLoading={isSubmitting} disabled={isSubmitting}>
                  {isSubmitting ? 'Posting...' : 'Post Reply'}
                </Button>
              </div>
            </form>
          </div>
        )}
        {!isAuthenticated && !thread.is_locked && (
            <p className="mt-8 text-sm text-gray-600">
                <Link to="/auth/login" className="text-blue-600 hover:underline font-semibold">Log in</Link> or <Link to="/auth/register" className="text-blue-600 hover:underline font-semibold">register</Link> to post a reply.
            </p>
        )}
        {thread.is_locked && (
            <p className="mt-8 text-sm text-yellow-700 bg-yellow-50 p-3 rounded-md">This thread is locked. No new replies can be posted.</p>
        )}
      </div>
    </div>
  );
};

export default ForumThreadPage;