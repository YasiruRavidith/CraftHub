// src/services/forumService.js
import apiClient from './apiClient';

const getForumCategories = async (params = {}) => {
  try {
    const response = await apiClient.get('/community/forum-categories/', { params });
    return response.data; // Expects DRF paginated response or simple list
  } catch (error) {
    console.error('Error fetching forum categories:', error.response?.data || error.message);
    throw error;
  }
};

const getForumCategoryBySlug = async (slug) => {
    try {
      const response = await apiClient.get(`/community/forum-categories/${slug}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching category ${slug}:`, error.response?.data || error.message);
      throw error;
    }
  };

const getForumThreads = async (params = {}) => {
  // params can include category_slug, author__username, etc.
  try {
    const response = await apiClient.get('/community/forum-threads/', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching forum threads:', error.response?.data || error.message);
    throw error;
  }
};

const getForumThreadBySlug = async (slug) => {
  try {
    // This should return thread details including posts (from ForumThreadDetailSerializer)
    const response = await apiClient.get(`/community/forum-threads/${slug}/`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching thread ${slug}:`, error.response?.data || error.message);
    throw error;
  }
};

const createForumThread = async (threadData) => {
  // threadData: { category_slug, title, initial_post_content }
  try {
    const response = await apiClient.post('/community/forum-threads/', threadData);
    return response.data;
  } catch (error) {
    console.error('Error creating forum thread:', error.response?.data || error.message);
    throw error;
  }
};

const createForumPost = async (threadSlug, postData) => {
  // postData: { content }
  // thread_id is derived from threadSlug on backend or passed explicitly if API structure differs
  try {
    // The API endpoint might be /community/forum-threads/<slug>/create-post/
    // Or /community/forum-posts/ with thread_id in postData
    const response = await apiClient.post(`/community/forum-threads/${threadSlug}/create-post/`, postData);
    // Or if using ForumPostViewSet directly:
    // const response = await apiClient.post('/community/forum-posts/', { thread_id: threadIdFromSlug, ...postData });
    return response.data;
  } catch (error) {
    console.error('Error creating forum post:', error.response?.data || error.message);
    throw error;
  }
};

export default {
  getForumCategories,
  getForumCategoryBySlug,
  getForumThreads,
  getForumThreadBySlug,
  createForumThread,
  createForumPost,
};