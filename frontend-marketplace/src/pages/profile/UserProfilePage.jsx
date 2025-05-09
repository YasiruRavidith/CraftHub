// src/pages/profile/UserProfilePage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../../components/common/Button';
import { formatDate } from '../../utils/formatters';

const UserProfilePage = () => {
  const { user } = useAuth();

  if (!user) {
    return <p>Loading user profile...</p>; // Or redirect if not logged in (handled by PrivateRoute)
  }

  // The 'user' from AuthContext contains basic user info from login/register
  // The 'user.profile' object comes from your Django backend's UserSerializer
  const profile = user.profile || {};

  return (
    <div className="bg-white p-6 md:p-8 rounded-lg shadow-xl max-w-3xl mx-auto">
      <div className="flex flex-col md:flex-row items-center md:items-start mb-8">
        <img
          src={profile.profile_picture || `https://ui-avatars.com/api/?name=${user.username}&background=random&size=128`}
          alt={`${user.username}'s profile`}
          className="w-32 h-32 rounded-full object-cover mb-4 md:mb-0 md:mr-8 border-4 border-blue-200"
        />
        <div>
          <h1 className="text-3xl font-bold text-gray-800">{user.first_name} {user.last_name}</h1>
          <p className="text-md text-gray-600">@{user.username} ({user.user_type})</p>
          <p className="text-sm text-gray-500">{user.email}</p>
          {profile.company_name && <p className="text-sm text-gray-500 mt-1">Company: {profile.company_name}</p>}
        </div>
        <Link to="/dashboard/profile/edit" className="md:ml-auto mt-4 md:mt-0">
            <Button variant="outline">Edit Profile</Button>
        </Link>
      </div>

      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">About Me</h2>
          <p className="text-gray-600 leading-relaxed">{profile.bio || "No biography provided."}</p>
        </div>

        {profile.website && (
          <div>
            <h3 className="text-lg font-medium text-gray-700">Website</h3>
            <a href={profile.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{profile.website}</a>
          </div>
        )}
        
        <div>
            <h3 className="text-lg font-medium text-gray-700">Contact Information</h3>
            <p className="text-gray-600">Phone: {profile.phone_number || "N/A"}</p>
        </div>

        <div>
            <h3 className="text-lg font-medium text-gray-700">Address</h3>
            <p className="text-gray-600">
                {profile.address_line1 || ""} {profile.address_line2 || ""} <br />
                {profile.city || ""} {profile.state_province || ""} {profile.postal_code || ""} <br />
                {profile.country || "Address not fully specified."}
            </p>
        </div>

        {user.user_type === 'designer' && profile.design_portfolio_url && (
            <div>
                <h3 className="text-lg font-medium text-gray-700">Portfolio</h3>
                <a href={profile.design_portfolio_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{profile.design_portfolio_url}</a>
            </div>
        )}
        {user.user_type === 'manufacturer' && profile.manufacturing_capabilities && (
            <div>
                <h3 className="text-lg font-medium text-gray-700">Manufacturing Capabilities</h3>
                <p className="text-gray-600">{profile.manufacturing_capabilities}</p>
            </div>
        )}


        <p className="text-xs text-gray-400 mt-4">Member since: {formatDate(user.date_joined || profile.created_at)}</p>
      </div>
    </div>
  );
};

export default UserProfilePage;