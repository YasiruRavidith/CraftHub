// src/components/specific/UserProfileForm.jsx
import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import Input from '../common/Input';
import Button from '../common/Button';
import userService from '../../services/userService';
import { useAuth } from '../../contexts/AuthContext'; // To update user context after save

const UserProfileForm = ({ initialProfileData }) => {
  const { user, updateUserContext } = useAuth(); // Get user for initial data and context update
  const { register, handleSubmit, reset, setValue, formState: { errors, isDirty } } = useForm({
    defaultValues: initialProfileData || {}, // Load initial data if provided
  });
  const [apiError, setApiError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [imagePreview, setImagePreview] = useState(initialProfileData?.profile_picture_url || null);
  const navigate = useNavigate();

  useEffect(() => {
    if (initialProfileData) {
      reset(initialProfileData); // Set form values from fetched profile
      if(initialProfileData.profile_picture) { // Assuming backend sends URL for existing picture
        setImagePreview(initialProfileData.profile_picture);
      }
    }
  }, [initialProfileData, reset]);


  const handleImageChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setValue('profile_picture_file', file); // Store file object for submission
      setImagePreview(URL.createObjectURL(file));
    }
  };


  const onSubmit = async (data) => {
    setApiError('');
    setSuccessMessage('');
    setLoading(true);

    // Prepare data for API. If profile_picture_file exists, it's a new upload.
    // Otherwise, if profile_picture (URL) is in 'data' and no new file, backend might handle it or ignore.
    // For simplicity, our service will handle FormData if 'profile_picture_file' is a File.

    const formDataToSubmit = { ...data };
    if (data.profile_picture_file instanceof File) {
        formDataToSubmit.profile_picture = data.profile_picture_file;
    } else {
        // If no new file is uploaded, don't send the profile_picture field
        // unless you want to send the existing URL (backend must handle this).
        // Or to clear it, send null (backend needs to support clearing).
        // For this example, if no new file, we won't send the 'profile_picture' field.
        // The backend PATCH should only update fields that are sent.
        // If you want to clear the image, you'd need a separate mechanism or send profile_picture: null
        delete formDataToSubmit.profile_picture; // Don't send old URL if no new file
    }
    delete formDataToSubmit.profile_picture_file; // Remove the temporary field

    try {
      const updatedProfile = await userService.updateMyProfile(formDataToSubmit);
      setSuccessMessage('Profile updated successfully!');
      // Update user in AuthContext if profile data is part of the user object there
      if (user && updatedProfile) {
        // Assuming the backend returns the full updated profile which might be nested in user
        // Or, the UserSerializer on backend returns the user with updated profile.
        // For now, let's assume updateMyProfile returns the profile data and user in AuthContext has a profile field.
        const updatedUserForContext = { ...user, profile: updatedProfile };
        updateUserContext(updatedUserForContext);
      }
      setTimeout(() => navigate('/dashboard/profile'), 1500); // Redirect after a delay
    } catch (err) {
      let errorMessage = "Failed to update profile.";
      if (err.response && err.response.data) {
        errorMessage = Object.entries(err.response.data)
          .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
          .join('; ');
      } else if (err.message) {
        errorMessage = err.message;
      }
      setApiError(errorMessage);
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" encType="multipart/form-data">
      {apiError && <p className="text-sm text-red-600 bg-red-100 p-3 rounded-md">{apiError}</p>}
      {successMessage && <p className="text-sm text-green-600 bg-green-100 p-3 rounded-md">{successMessage}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Input label="Company Name" id="company_name" {...register("company_name")} error={errors.company_name} />
        <Input label="Phone Number" id="phone_number" {...register("phone_number")} error={errors.phone_number} />
      </div>

      <div>
        <label htmlFor="profile_picture" className="block text-sm font-medium text-gray-700 mb-1">Profile Picture</label>
        {imagePreview && <img src={imagePreview} alt="Profile Preview" className="w-32 h-32 rounded-full object-cover mb-2" />}
        <input
          type="file"
          id="profile_picture"
          accept="image/*"
          onChange={handleImageChange} // This uses setValue, so no need for formRegister
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        {errors.profile_picture_file && <p className="mt-1 text-xs text-red-600">{errors.profile_picture_file.message}</p>}
      </div>

      <div>
        <label htmlFor="bio" className="block text-sm font-medium text-gray-700 mb-1">Bio</label>
        <textarea
          id="bio"
          rows="4"
          {...register("bio")}
          className={`mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${errors.bio ? 'border-red-500' : ''}`}
        />
        {errors.bio && <p className="mt-1 text-xs text-red-600">{errors.bio.message}</p>}
      </div>

      <Input label="Website" id="website" type="url" {...register("website")} error={errors.website} placeholder="https://example.com"/>

      <fieldset className="border p-4 rounded-md">
        <legend className="text-sm font-medium text-gray-700 px-1">Address</legend>
        <div className="space-y-4 mt-2">
            <Input label="Address Line 1" id="address_line1" {...register("address_line1")} error={errors.address_line1} />
            <Input label="Address Line 2" id="address_line2" {...register("address_line2")} error={errors.address_line2} />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input label="City" id="city" {...register("city")} error={errors.city} />
                <Input label="State/Province" id="state_province" {...register("state_province")} error={errors.state_province} />
                <Input label="Postal Code" id="postal_code" {...register("postal_code")} error={errors.postal_code} />
            </div>
            <Input label="Country" id="country" {...register("country")} error={errors.country} />
        </div>
      </fieldset>

      {/* User type specific fields */}
      {user?.user_type === 'designer' && (
        <Input label="Design Portfolio URL" id="design_portfolio_url" type="url" {...register("design_portfolio_url")} error={errors.design_portfolio_url} placeholder="https://myportfolio.com"/>
      )}
      {user?.user_type === 'manufacturer' && (
         <div>
            <label htmlFor="manufacturing_capabilities" className="block text-sm font-medium text-gray-700 mb-1">Manufacturing Capabilities</label>
            <textarea
              id="manufacturing_capabilities"
              rows="3"
              {...register("manufacturing_capabilities")}
              className={`mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${errors.manufacturing_capabilities ? 'border-red-500' : ''}`}
            />
            {errors.manufacturing_capabilities && <p className="mt-1 text-xs text-red-600">{errors.manufacturing_capabilities.message}</p>}
        </div>
      )}


      <div className="flex justify-end space-x-3">
        <Button type="button" variant="ghost" onClick={() => navigate('/dashboard/profile')}>Cancel</Button>
        <Button type="submit" variant="primary" isLoading={loading} disabled={loading || !isDirty}>
          {loading ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </form>
  );
};

export default UserProfileForm;