// src/services/userService.js
import apiClient from './apiClient';

const getMyProfile = async () => {
  try {
    const response = await apiClient.get('/accounts/profiles/me/');
    return response.data;
  } catch (error) {
    console.error('Error fetching my profile:', error.response?.data || error.message);
    throw error;
  }
};

const updateMyProfile = async (formDataPayload) => { // Expecting formDataPayload to be FormData instance
  try {
    // Axios will automatically set the Content-Type to multipart/form-data
    // when the payload is an instance of FormData.
    const response = await apiClient.patch('/accounts/profiles/me/', formDataPayload);
    return response.data;
  } catch (error) {
    console.error('Error updating my profile:', error.response?.data || error.message);
    // For better debugging of the 400 error from DRF about non-file data:
    if (error.response && error.response.data && error.response.data.profile_picture) {
        console.error("Profile picture error details:", error.response.data.profile_picture);
    }
    throw error;
  }
};

const getUserPublicProfile = async (userIdOrUsername) => {
  try {
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