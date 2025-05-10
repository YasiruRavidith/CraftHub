// src/components/specific/UserProfileForm.jsx
import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import Input from '../common/Input';
import Button from '../common/Button';
import userService from '../../services/userService';
import { useAuth } from '../../contexts/AuthContext';

const UserProfileForm = ({ initialProfileData }) => {
  const { user, updateUserContext } = useAuth();
  const {
    register,
    handleSubmit,
    reset,
    watch, // To watch file input changes
    formState: { errors, isDirty }
  } = useForm({
    defaultValues: initialProfileData || {},
  });

  const [apiError, setApiError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [imagePreview, setImagePreview] = useState(initialProfileData?.profile_picture || null);

  // Watch the file input for changes to update the preview
  const profilePictureFileInput = watch('profile_picture_file_input');

  useEffect(() => {
    if (initialProfileData) {
      const defaults = { ...initialProfileData };
      delete defaults.profile_picture; // Don't set file input with a URL
      reset(defaults); // Set form values from fetched profile, makes form !isDirty initially
      setImagePreview(initialProfileData.profile_picture || null);
    }
  }, [initialProfileData, reset]);

  useEffect(() => {
    // This effect updates the preview when the file input changes
    if (profilePictureFileInput && profilePictureFileInput.length > 0 && profilePictureFileInput[0] instanceof File) {
      const file = profilePictureFileInput[0];
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    } else if ((!profilePictureFileInput || profilePictureFileInput.length === 0) && initialProfileData?.profile_picture) {
      setImagePreview(initialProfileData.profile_picture);
    } else if (!profilePictureFileInput || profilePictureFileInput.length === 0) {
      setImagePreview(null);
    }
  }, [profilePictureFileInput, initialProfileData]);


  const onSubmit = async (dataFromForm) => {
    setApiError('');
    setSuccessMessage('');
    setLoading(true);

    const payload = new FormData(); // 'payload' is defined here

    console.log("Data from react-hook-form (dataFromForm):", dataFromForm);

    // Append all non-file fields from the form data
    Object.keys(dataFromForm).forEach(key => {
      if (key !== 'profile_picture_file_input') { // Exclude the react-hook-form field for file input
        if (dataFromForm[key] !== null && dataFromForm[key] !== undefined) {
            // For fields that might be empty strings but you want to send them (e.g. bio can be set to empty)
            // Or specifically check for empty strings if you want to omit them:
            // if (dataFromForm[key] !== null && dataFromForm[key] !== undefined && dataFromForm[key] !== '') {
            payload.append(key, dataFromForm[key]);
        } else if (dataFromForm[key] === null && initialProfileData && initialProfileData[key] !== null) {
            // If user explicitly cleared a field that had a value, send empty string to clear on backend
            // (Backend must support clearing fields with empty string or null)
            payload.append(key, '');
        }
      }
    });

    // Append the new profile picture file if one was selected
    if (dataFromForm.profile_picture_file_input && dataFromForm.profile_picture_file_input.length > 0) {
        const file = dataFromForm.profile_picture_file_input[0];
        console.log("File object being prepared:", file);
        console.log("Is it a File instance?", file instanceof File);
        if (file instanceof File) {
            payload.append('profile_picture', file, file.name); // Key 'profile_picture' for the backend
        } else {
            console.error("The selected item in 'profile_picture_file_input' is NOT a File object!", file);
            setApiError("Invalid file selected for profile picture.");
            setLoading(false);
            return; // Stop submission
        }
    }
    // Note: If you want to allow REMOVING an image, you need specific logic here.
    // e.g., if a "remove image" checkbox is checked, you might append 'profile_picture': '' or null.
    // For now, if no new file, the PATCH request won't include 'profile_picture',
    // and the backend should not change the existing image.

    console.log("FormData payload entries before sending to userService:");
    for (let [key, value] of payload.entries()) {
        console.log(`FormData: ${key} =`, value);
    }

    try {
      const updatedProfile = await userService.updateMyProfile(payload);
      setSuccessMessage('Profile updated successfully!');
      
      const updatedUserForContext = { 
        ...user, 
        profile: updatedProfile,
        // If your UserSerializer on backend returns updated top-level user fields in profile update response
        // you could update them here too. For now, assuming profile is nested.
        // first_name: updatedProfile.user?.first_name || user.first_name, 
        // last_name: updatedProfile.user?.last_name || user.last_name,
      };
      updateUserContext(updatedUserForContext);
      
      const newDefaults = { ...updatedProfile };
      delete newDefaults.profile_picture; // Don't set file input with a URL
      reset(newDefaults); // Resets form values and makes isDirty false
      setImagePreview(updatedProfile.profile_picture || null);

    } catch (err) {
      let errorMessage = "Failed to update profile.";
      if (err.response && err.response.data) {
          console.error("Profile update error data:", err.response.data);
          if (typeof err.response.data === 'string') {
            errorMessage = err.response.data;
          } else {
            errorMessage = Object.entries(err.response.data)
              .map(([key, value]) => {
                const prettyKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                return `${prettyKey}: ${Array.isArray(value) ? value.join(', ') : value}`;
              })
              .join('; ');
          }
      } else if (err.message) {
          errorMessage = err.message;
      }
      setApiError(errorMessage);
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 text-gray-950">
      {apiError && <p className="text-sm text-red-600 bg-red-100 p-3 rounded-md">{apiError}</p>}
      {successMessage && <p className="text-sm text-green-600 bg-green-100 p-3 rounded-md">{successMessage}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Input 
          label="Company Name (Optional)" 
          id="company_name" 
          {...register("company_name")} 
          error={errors.company_name} 
        />
        <Input 
          label="Phone Number (Optional)" 
          id="phone_number" 
          {...register("phone_number")} 
          error={errors.phone_number} 
        />
      </div>

      <div>
        <label htmlFor="profile_picture_file_input" className="block text-sm font-medium text-gray-700 mb-1">
            Profile Picture
        </label>
        {imagePreview && (
          <img 
            src={imagePreview} 
            alt="Profile Preview" 
            className="w-32 h-32 rounded-full object-cover mb-2 border-2 border-gray-200" 
          />
        )}
        <input
          type="file"
          id="profile_picture_file_input" // This is the name react-hook-form uses
          accept="image/png, image/jpeg, image/gif" // Restrict file types
          {...register("profile_picture_file_input")} // Register with RHF
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
        />
        {errors.profile_picture_file_input && <p className="mt-1 text-xs text-red-600">{errors.profile_picture_file_input.message}</p>}
      </div>

      <div>
        <label htmlFor="bio" className="block text-sm font-medium text-gray-700 mb-1">Bio (Optional)</label>
        <textarea
          id="bio"
          rows="4"
          {...register("bio")}
          className={`mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${errors.bio ? 'border-red-500' : ''}`}
          placeholder="Tell us a bit about yourself or your company..."
        />
        {errors.bio && <p className="mt-1 text-xs text-red-600">{errors.bio.message}</p>}
      </div>

      <Input 
        label="Website (Optional)" 
        id="website" 
        type="url" 
        {...register("website", {
          pattern: {
            value: /^(ftp|http|https):\/\/[^ "]+$/,
            message: "Enter a valid URL (e.g., https://example.com)"
          }
        })}
        error={errors.website} 
        placeholder="https://example.com"
      />

      <fieldset className="border p-4 rounded-md mt-2">
        <legend className="text-sm font-medium text-gray-700 px-1">Address (Optional)</legend>
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

      {/* User type specific fields - Render based on user.user_type */}
      {user?.user_type === 'designer' && (
        <Input 
          label="Design Portfolio URL (Optional)" 
          id="design_portfolio_url" 
          type="url" 
          {...register("design_portfolio_url", {
            pattern: {
              value: /^(ftp|http|https):\/\/[^ "]+$/,
              message: "Enter a valid URL"
            }
          })} 
          error={errors.design_portfolio_url} 
          placeholder="https://myportfolio.com"
        />
      )}
      {user?.user_type === 'manufacturer' && (
         <div>
            <label htmlFor="manufacturing_capabilities" className="block text-sm font-medium text-gray-700 mb-1">
              Manufacturing Capabilities (Optional)
            </label>
            <textarea
              id="manufacturing_capabilities"
              rows="3"
              {...register("manufacturing_capabilities")}
              className={`mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${errors.manufacturing_capabilities ? 'border-red-500' : ''}`}
              placeholder="Describe your manufacturing strengths..."
            />
            {errors.manufacturing_capabilities && <p className="mt-1 text-xs text-red-600">{errors.manufacturing_capabilities.message}</p>}
        </div>
      )}

      <div className="flex justify-end space-x-3 pt-4 border-t mt-6">
        <Button type="button" variant="ghost" onClick={() => {
          reset(initialProfileData || {}); // Reset to initial on cancel
          setImagePreview(initialProfileData?.profile_picture || null);
          navigate('/dashboard/profile');
        }}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" isLoading={loading} disabled={loading || !isDirty}>
          {loading ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </form>
  );
};

export default UserProfileForm;