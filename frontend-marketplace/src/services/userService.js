// src/services/userService.js
import apiClient from './apiClient';

// Profile data for the currently authenticated user
const getMyProfile = async () => {
  try {
    // The 'user' object from login/register often includes the profile.
    // This endpoint is specifically for fetching/updating the Profile model instance.
    // Your backend endpoint for the current user's profile might be /accounts/profiles/me/
    const response = await apiClient.get('/accounts/profiles/me/');
    return response.data;
  } catch (error) {
    console.error('Error fetching my profile:', error.response?.data || error.message);
    throw error;
  }
};

const updateMyProfile = async (profileData) => {
  try {
    // For FileUploads (like profile_picture), you need to send FormData
    // This example assumes JSON data for now. Handle FormData separately if needed.
    let dataToSend = profileData;
    let headers = { 'Content-Type': 'application/json' };

    if (profileData.profile_picture instanceof File) {
        const formData = new FormData();
        Object.keys(profileData).forEach(key => {
            if (key === 'profile_picture' && profileData[key] instanceof File) {
                formData.append(key, profileData[key], profileData[key].name);
            } else if (profileData[key] !== null && profileData[key] !== undefined) {
                formData.append(key, profileData[key]);
            }
        });
        dataToSend = formData;
        headers = {}; // Axios will set Content-Type for FormData
    }

    const response = await apiClient.patch('/accounts/profiles/me/', dataToSend, { headers });
    return response.data;
  } catch (error) {
    console.error('Error updating my profile:', error.response?.data || error.message);
    throw error;
  }
};

// To get a public profile of another user (if you implement this)
const getUserPublicProfile = async (userIdOrUsername) => {
  try {
    // Example endpoint: /accounts/profiles/<userIdOrUsername>/
    const response = await apiClient.get(`/accounts/profiles/${userIdOrUsername}/`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching profile for ${userIdOrUsername}:`, error.response?.data || error.message);
    throw error;
  }
};


export default {
  getMyProfile,
  updateMyProfile,
  getUserPublicProfile,
};