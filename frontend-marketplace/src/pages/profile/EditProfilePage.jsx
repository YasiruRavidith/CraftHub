// src/pages/profile/EditProfilePage.jsx
import React, { useState, useEffect } from 'react';
import UserProfileForm from '../../components/specific/UserProfileForm';
import userService from '../../services/userService';
import Loader from '../../components/common/Loader';
import { useAuth } from '../../contexts/AuthContext';

const EditProfilePage = () => {
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth(); // Get current user to know their type for form rendering

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await userService.getMyProfile();
        // The backend /accounts/profiles/me/ returns the Profile model fields.
        // It might not include the profile_picture URL directly if the FileField is just a path.
        // The UserSerializer for 'user' in AuthContext should ideally provide a full URL.
        // For now, assume 'data' is the profile object and picture URL might need construction.
        setProfileData(data);
      } catch (err) {
        setError('Failed to load profile data. Please try again.');
        console.error(err);
      }
      setLoading(false);
    };
    fetchProfile();
  }, []);

  if (loading) return <Loader text="Loading profile for editing..." />;
  if (error) return <p className="text-center text-red-500 p-10">{error}</p>;
  // The UserProfileForm component itself uses the 'user' from AuthContext to show/hide fields
  // initialProfileData is passed to pre-fill the form.

  return (
    <div className="bg-white p-6 md:p-8 rounded-lg shadow-xl max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Edit Your Profile</h1>
      {profileData ? (
        <UserProfileForm initialProfileData={profileData} />
      ) : (
        <p>Could not load profile data to edit.</p>
      )}
    </div>
  );
};

export default EditProfilePage;