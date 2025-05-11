// src/pages/MaterialDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom'; // Added useNavigate, useLocation, Link
import productService from '../services/productService';
import Loader from '../components/common/Loader';
import Button from '../components/common/Button';
import { formatCurrency } from '../utils/formatters'; // Removed formatDate as it's not used here
import { useAuth } from '../contexts/AuthContext'; // Import useAuth
import { ShoppingCart, MessageSquare, AlertCircle } from 'lucide-react'; // Icons
import { useCart } from '../contexts/CartContext.jsx';


const MaterialDetailPage = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const location = useLocation(); // To redirect back after login

  const [material, setMaterial] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  const { isAuthenticated, user } = useAuth(); // Still need for login prompt & user type checks

 

  useEffect(() => {
    const fetchMaterial = async () => {
      setLoading(true);
      setError('');
      setShowLoginPrompt(false); // Reset prompt on new material load
      try {
        const data = await productService.getMaterialBySlug(slug);
        setMaterial(data);
      } catch (err) {
        if (err.response && err.response.status === 404) {
            setError('Material not found.');
        } else {
            setError('Failed to fetch material details. Please try again.');
        }
        console.error("Fetch material error:", err);
      }
      setLoading(false);
    };
    if (slug) {
      fetchMaterial();
    }
  }, [slug]);

  const handleActionRequiredLogin = (actionCallback) => {
    if (!isAuthenticated) {
      setShowLoginPrompt(true);
      // Alternative: Redirect to login immediately
      // navigate('/auth/login', { state: { from: location } });
      return;
    }
    setShowLoginPrompt(false);
    actionCallback();
  };

  const handleAddToCartOrRFQ = () => {
    // Placeholder logic
    // TODO: Implement actual add to cart or RFQ logic
    // This might involve:
    // 1. Checking user.user_type (e.g., only 'buyer' can add to cart/RFQ)
    // 2. Opening a modal for quantity/options
    // 3. Calling a cartService or rfqService
    if (user?.user_type !== 'buyer') {
        alert("Only buyers can perform this action.");
        return;
    }
    alert(`Action: Add ${material.name} to Cart/RFQ queue (for user ${user.username}). Quantity needed.`);
    console.log("Add to Cart / RFQ for material:", material.id, "by user:", user.id);
  };

  const handleActualAddToCart = () => {
    if (user?.user_type !== 'buyer') {
        alert("Only buyers can add items to the cart or request quotes.");
        return;
    }
    if (material.stock_quantity === 0) {
        alert("This material is out of stock.");
        return;
    }
    
    // Construct the product object for the cart
    const productToAdd = {
        id: material.id || material.slug, // Prefer ID if available
        type: 'material',
        name: material.name,
        price: material.price_per_unit,
        unit: material.unit,
        image: material.main_image_url,
        slug: material.slug,
        // Add any other necessary details from 'material' object
        // that you want to store in the cart item.
    };
    // addItemToCart(productToAdd, 1); // Add 1 quantity
    // alert(`${material.name} added to cart!`);
    
    // THIS IS WHERE THE ERROR WAS. `addItemToCart` is not defined yet.
    // It needs to be destructured from `useCart()` at the component's top level.
    // For now, let's just log. We will fix the addItemToCart call in the next step.
    console.log("Attempting to add to cart:", productToAdd);
    alert("Add to cart functionality will be fully implemented with useCart().");
  };

   const cartContext = useCart();

  const handleContactSeller = () => {
    // Placeholder logic
    // TODO: Implement contact seller functionality
    // This might involve:
    // 1. Opening a messaging modal
    // 2. Navigating to a chat page with the seller (e.g., /dashboard/messages/new?recipient=${material.seller?.id}&subject=Inquiry about ${material.name})
    if (!material.seller) {
        alert("Seller information is not available for this material.");
        return;
    }
    alert(`Action: Contact seller ${material.seller?.username} about ${material.name}.`);
    console.log("Contact Seller for material:", material.id, "Seller:", material.seller?.id);
    // Example navigation to a hypothetical chat page
    // navigate(`/dashboard/messages/new?recipient=${material.seller.id}&material=${material.id}`);
  };


  if (loading) return <div className="min-h-[60vh] flex items-center justify-center"><Loader text="Loading material details..." /></div>;
  if (error && !material) return ( // Show error prominently if material couldn't be loaded
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-10">
        <AlertCircle size={48} className="text-red-500 mb-4" />
        <p className="text-xl text-red-600 font-semibold">{error}</p>
    </div>
    );
  if (!material) return ( // Should ideally be caught by error state if fetch fails
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-10">
        <p className="text-xl text-slate-600">Material not found.</p>
    </div>
    );

  // Determine if current user is the seller of this material
  const isOwner = isAuthenticated && user?.id === material.seller?.id;

  return (
    <div className="container-mx py-8">
      {showLoginPrompt && (
        <div className="mb-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 text-yellow-700 rounded-md shadow">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-yellow-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm">
                You need to be logged in to perform this action.
                <Link to="/auth/login" state={{ from: location }} className="font-medium underline hover:text-yellow-600 ml-2">
                  Login here
                </Link>
                {' or '}
                <Link to="/auth/register" state={{ from: location }} className="font-medium underline hover:text-yellow-600">
                  Register
                </Link>
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-8 bg-white p-6 rounded-lg shadow-xl">
        {/* Image Column */}
        <div className="md:col-span-1">
          <img
            src={material.main_image_url || `https://via.placeholder.com/600x400?text=${encodeURIComponent(material.name)}`}
            alt={material.name}
            className="w-full h-auto max-h-[500px] object-cover rounded-lg shadow-md sticky top-24" // Sticky for image while scrolling details
          />
          {/* TODO: Image gallery for material.additional_images */}
        </div>

        {/* Details Column */}
        <div className="md:col-span-2">
          <p className="text-xs text-purple-600 uppercase tracking-wider mb-1">
            {material.category?.name || 'Uncategorized'}
          </p>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-950 mb-2">{material.name}</h1>
          <p className="text-sm text-slate-500 mb-4">
            Sold by: <Link to={`/profiles/${material.seller?.username}`} className="text-teal-700 hover:underline">{material.seller?.username || 'N/A'}</Link>
          </p>
          
          {/* TODO: Add Rating Display Component here if material has average_rating & review_count */}

          <div className="mb-6 p-4 bg-purple-50 rounded-md border border-purple-200">
            <p className="text-3xl font-bold text-purple-700">
                {formatCurrency(material.price_per_unit, material.currency || 'USD')} 
                <span className="text-base font-normal text-slate-600"> / {material.unit}</span>
            </p>
            {material.minimum_order_quantity > 0 && ( // Show even if 1
                 <p className="text-sm text-slate-600 mt-1">Minimum Order: {material.minimum_order_quantity} {material.unit}{material.minimum_order_quantity > 1 ? 's' : ''}</p>
            )}
          </div>

          <div className="prose prose-sm max-w-none text-slate-700 mb-6 leading-relaxed">
            <p>{material.description || "No detailed description available."}</p>
          </div>
          
          <h3 className="text-lg font-semibold mb-3 text-slate-800 border-b pb-2">Material Specifications:</h3>
          <ul className="space-y-2 text-sm text-slate-600 mb-6">
            {material.composition && <li><strong>Composition:</strong> {material.composition}</li>}
            {material.weight_gsm && <li><strong>Weight:</strong> {material.weight_gsm} GSM</li>}
            {material.width_cm && <li><strong>Width:</strong> {material.width_cm} cm</li>}
            {material.country_of_origin && <li><strong>Origin:</strong> {material.country_of_origin}</li>}
            {material.lead_time_days !== null && <li><strong>Lead Time:</strong> {material.lead_time_days} days</li>}
            {material.stock_quantity !== null && (
              <li>
                <strong>Stock:</strong> 
                <span className={material.stock_quantity > 0 ? 'text-green-600' : 'text-red-600'}>
                  {material.stock_quantity > 0 ? ` ${material.stock_quantity} available` : ' Out of Stock'}
                </span>
              </li>
            )}
            {material.sku && <li><strong>SKU:</strong> {material.sku}</li>}
          </ul>

          {/* TODO: Certifications display (map over material.certifications) */}
          {/* TODO: Tags display (map over material.tags) */}

          {!isOwner && ( // Don't show action buttons if the current user is the seller
            <div className="mt-8 pt-6 border-t border-slate-200 flex flex-col sm:flex-row sm:space-x-4 space-y-3 sm:space-y-0">
              <Button 
              variant="primary" 
              size="lg" 
              className="w-full sm:w-auto bg-purple-600 hover:bg-purple-700 flex items-center justify-center"
              onClick={() => handleActionRequiredLogin(() => {
                  // Correct way to call addItemToCart:
                  if (user?.user_type !== 'buyer') {
                      alert("Only buyers can add items to the cart or request quotes.");
                      return;
                  }
                  if (material.stock_quantity === 0) {
                      alert("This material is out of stock.");
                      return;
                  }
                  const productToAdd = {
                      id: material.id || material.slug, type: 'material', name: material.name,
                      price: material.price_per_unit, unit: material.unit,
                      image: material.main_image_url, slug: material.slug,
                  };
                  cartContext.addItemToCart(productToAdd, 1); // Use from cartContext
                  alert(`${material.name} added to cart!`);
              })}
              disabled={material.stock_quantity === 0}
            >
              <ShoppingCart size={20} className="mr-2" /> 
              {material.stock_quantity === 0 ? 'Out of Stock' : (user?.user_type === 'buyer' ? 'Add to Cart / RFQ' : 'Request Info')}
            </Button>
              <Button 
                variant="outline" 
                size="lg" 
                className="w-full sm:w-auto text-purple-700 border-purple-600 hover:bg-purple-50 flex items-center justify-center"
                onClick={() => handleActionRequiredLogin(handleContactSeller)}
              >
                <MessageSquare size={20} className="mr-2" />
                Contact Seller
              </Button>
            </div>
          )}
           {isOwner && (
             <div className="mt-8 pt-6 border-t border-slate-200">
                <p className="text-sm text-slate-500 italic">You are the seller of this material.</p>
                <Link to={`/dashboard/listings/material/${material.slug}/edit`}> {/* Placeholder for edit link */}
                    <Button variant='outline' className="mt-2">Edit Listing</Button>
                </Link>
             </div>
           )}
        </div>
      </div>
      
      {/* TODO: Seller Information Section (Could be a separate component) */}
      <div className="mt-12 bg-white p-6 rounded-lg shadow-lg">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">About The Seller</h2>
        <p className="text-slate-600">Seller details will be displayed here.</p>
        {/* Fetch and display material.seller.profile information */}
      </div>

      {/* TODO: Reviews and Ratings Section (Could be a separate component) */}
      <div className="mt-12">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">Reviews & Ratings</h2>
        <p className="text-slate-600 bg-white p-6 rounded-lg shadow-lg">Customer reviews will appear here.</p>
        {/* Component to list reviews and allow adding a review */}
      </div>
    </div>
  );
};

export default MaterialDetailPage;