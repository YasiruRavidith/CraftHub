// src/pages/profile/EditProfilePage.jsx
import React, { useState, useEffect } from 'react';
import UserProfileForm from '../../components/specific/UserProfileForm';
import userService from '../../services/userService';
import Loader from '../../components/common/Loader';
import { useAuth } from '../../contexts/AuthContext'; // To pass user type if needed by form

const EditProfilePage = () => {
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth(); // User object from context

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await userService.getMyProfile();
        setProfileData(data);
      } catch (err) {
        setError('Failed to load profile data. Please try again.');
        console.error("Load profile error:",err);
      }
      setLoading(false);
    };
    fetchProfile();
  }, []);

  if (loading) return <Loader text="Loading profile for editing..." />;
  if (error) return <p className="text-center text-red-500 p-10 bg-red-50 rounded-md">{error}</p>;
  
  return (
    <div className="bg-white p-6 md:p-8 rounded-lg shadow-xl max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6 border-b pb-4">Edit Your Profile</h1>
      {profileData ? (
        // Pass the full user object if UserProfileForm needs user.user_type for conditional fields
        <UserProfileForm initialProfileData={profileData} />
      ) : (
        <p>Could not load profile data to edit. Ensure you are logged in and have a profile.</p>
      )}
    </div>
  );
};

export default EditProfilePage;