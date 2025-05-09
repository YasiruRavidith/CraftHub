// src/pages/listings_management/CreateListingPage.jsx
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import ListingForm from '../../components/listings/ListingForm';
import productService from '../../services/productService'; // Assuming createMaterial and createDesign
import { useAuth } from '../../contexts/AuthContext';

const CreateListingPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const queryParams = new URLSearchParams(location.search);
  const listingType = queryParams.get('type') || 'material'; // Default to material

  const [isLoading, setIsLoading] = useState(false);
  const [formError, setFormError] = useState('');

  const handleCreateListing = async (formData) => {
    setIsLoading(true);
    setFormError('');
    try {
      let createdListing;
      if (listingType === 'material') {
        // The backend expects seller_id. It's automatically set via perform_create in MaterialViewSet.
        // So we don't need to explicitly pass user.id if the backend sets it based on request.user.
        // If your serializer requires seller_id, you'd append it to formData here.
        // formData.append('seller_id', user.id); // Only if DRF serializer needs it explicitly
        createdListing = await productService.createMaterial(formData);
        navigate(`/materials/${createdListing.slug}`); // Or to MyMaterialsPage
      } else if (listingType === 'design') {
        // formData.append('designer_id', user.id); // Only if DRF serializer needs it explicitly
        // createdListing = await productService.createDesign(formData); // Implement this service
        // navigate(`/designs/${createdListing.slug}`);
        setFormError('Design creation not yet implemented.'); // Placeholder
        setIsLoading(false);
        return;
      } else {
        throw new Error('Invalid listing type');
      }
      // console.log('Listing created:', createdListing);
    } catch (error) {
      let errorMessage = `Failed to create ${listingType}.`;
      if (error.response && error.response.data) {
        errorMessage = Object.entries(error.response.data)
          .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
          .join('; ');
      } else if (error.message) {
        errorMessage = error.message;
      }
      setFormError(errorMessage);
      console.error(`Create ${listingType} error:`, error);
    }
    setIsLoading(false);
  };

  if (!user || (listingType === 'material' && !['seller', 'manufacturer', 'admin'].includes(user.user_type)) || (listingType === 'design' && !['designer', 'admin'].includes(user.user_type)) ) {
    return <p className="text-red-500 p-4">You are not authorized to create this type of listing.</p>;
  }

  return (
    <div className="max-w-2xl mx-auto bg-white p-6 md:p-8 rounded-lg shadow-xl">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        Create New {listingType === 'material' ? 'Material' : 'Design'}
      </h1>
      {formError && <p className="text-sm text-red-600 bg-red-100 p-3 rounded-md mb-4">{formError}</p>}
      <ListingForm
        onSubmitForm={handleCreateListing}
        listingType={listingType}
        isLoading={isLoading}
      />
    </div>
  );
};

export default CreateListingPage;