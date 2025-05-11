// src/pages/listings_management/CreateListingPage.jsx
import React, { useState, useMemo } from 'react'; // Added useMemo
import { useNavigate, useLocation } from 'react-router-dom';
import ListingForm from '../../components/listings/ListingForm';
import productService from '../../services/productService';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../../components/common/Button';

const CreateListingPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  
  const queryParams = new URLSearchParams(location.search);
  let initialListingType = queryParams.get('type') || 'material';
  if (!['material', 'design'].includes(initialListingType)) {
    initialListingType = 'material';
  }
  // No need for useState for listingType if it's determined by query param and doesn't change on this page
  const listingType = initialListingType; 

  const [isLoading, setIsLoading] = useState(false);
  const [formApiError, setFormApiError] = useState('');

  // For a create form, initialData is typically empty or has some defaults
  // Memoize it to ensure a stable reference is passed to ListingForm
  const initialFormData = useMemo(() => {
    if (listingType === 'material') {
      return {
        unit: 'm', // Default unit for material
        minimum_order_quantity: 1,
        // Add other sensible defaults for material creation
      };
    } else if (listingType === 'design') {
      return {
        // Defaults for design creation
      };
    }
    return {};
  }, [listingType]); // Re-memoize if listingType could change (though it doesn't in this component's current logic)

  const handleCreateListing = async (formData) => {
    // ... (rest of your handleCreateListing logic remains the same) ...
    setIsLoading(true);
    setFormApiError('');
    console.log("--- FormData received in CreateListingPage before API call ---");
  for (let [key, value] of formData.entries()) {
    console.log(key, value); // Check 'main_image' again
  }
  console.log("-------------------------------------------------------------");
    try {
      let createdListing;
      if (listingType === 'material') {
        createdListing = await productService.createMaterial(formData);
        navigate(`/materials/${createdListing.slug}`);
      } else if (listingType === 'design') {
        setFormApiError('Design creation not yet implemented.');
        setIsLoading(false);
        return;
      } else {
        throw new Error('Invalid listing type');
      }
    } catch (error) {
      let errorMessage = `Failed to create ${listingType}. `;
      if (error.response && error.response.data) {
        const errorData = error.response.data;
        errorMessage += Object.entries(errorData)
          .map(([key, value]) => {
            const prettyKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            return `${prettyKey}: ${Array.isArray(value) ? value.join(', ') : value}`;
          })
          .join('; ');
      } else if (error.message) {
        errorMessage += error.message;
      }
      setFormApiError(errorMessage);
      console.error(`Create ${listingType} error:`, error);
    }
    setIsLoading(false);
  };

  // ... (authorization checks remain the same) ...
  const canCreateMaterial = user && ['seller', 'manufacturer', 'admin'].includes(user.user_type);
  const canCreateDesign = user && ['designer', 'admin'].includes(user.user_type);

  let canCreateCurrentType = false;
  if (listingType === 'material') canCreateCurrentType = canCreateMaterial;
  if (listingType === 'design') canCreateCurrentType = canCreateDesign;

  if (!user) {
    return <p className="text-red-500 p-4">Please log in to create a listing.</p>;
  }
  if (!canCreateCurrentType) {
    return <p className="text-red-500 p-4">You are not authorized to create this type of listing.</p>;
  }


  return (
    <div className="max-w-2xl mx-auto bg-white p-6 md:p-8 rounded-lg shadow-xl text-gray-950">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">
          Create New {listingType === 'material' ? 'Material' : 'Design'}
        </h1>
      </div>
      
      <ListingForm
        onSubmitForm={handleCreateListing}
        initialData={initialFormData} // Pass memoized initialData
        listingType={listingType}
        isLoading={isLoading}
        apiFormError={formApiError}
      />
    </div>
  );
};

export default CreateListingPage;