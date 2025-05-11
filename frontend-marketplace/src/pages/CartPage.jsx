// src/pages/CartPage.jsx
import React, { useState } from 'react'; // Removed useEffect as cart comes from context
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import { useCart } from '../contexts/CartContext.jsx'; // Import useCart
import Button from '../components/common/Button';
import { ShoppingCart, XCircle, MinusCircle, PlusCircle } from 'lucide-react';
import { formatCurrency } from '../utils/formatters';
import orderService from '../services/orderService';

const CartPage = () => {
  const { isAuthenticated } = useAuth();
  const { 
    cartItems, 
    updateItemQuantity, 
    removeItemFromCart, 
    clearCart,
    cartSubtotal, // Use subtotal from context
  } = useCart();
  
  const navigate = useNavigate();
  const location = useLocation();
  const [isProcessing, setIsProcessing] = useState(false); // For checkout button

  const shippingEstimate = cartItems.length > 0 ? 5.00 : 0; // Placeholder
  const taxEstimate = cartSubtotal * 0.08; // Placeholder 8% tax
  const orderTotal = cartSubtotal + shippingEstimate + taxEstimate;

  const handleQuantityChange = (itemId, itemType, currentQuantity, change) => {
    const newQuantity = currentQuantity + change;
    if (newQuantity >= 1) {
      updateItemQuantity(itemId, itemType, newQuantity);
    } else if (newQuantity === 0) {
      // Optionally confirm before removing or just remove
      removeItemFromCart(itemId, itemType);
    }
  };

  const handleCheckout = async () => { // Make it async
  if (!isAuthenticated) {
    alert("Please log in to proceed to checkout.");
    navigate('/auth/login', { state: { from: location } });
    return;
  }
  setIsProcessing(true);
  try {
    // Prepare cart items for the backend
    const orderItemsPayload = cartItems.map(item => ({
      [item.type === 'material' ? 'material_id' : 'design_id']: item.id,
      quantity: item.quantity,
      unit_price: item.price, // Or ensure you have the correct price at time of order
      // Add custom_item_description if your cart items can be custom
    }));

    const createdOrder = await orderService.createOrderFromCart(orderItemsPayload);
    console.log("Order created successfully:", createdOrder);
    alert(`Order ${createdOrder.id.substring(0,8)} placed successfully!`);
    clearCart(); // Clear cart on successful order
    navigate(`/dashboard/orders/${createdOrder.id}`); // Navigate to order detail page
  } catch (error) {
    alert("Failed to place order. Please try again. " + (error.response?.data?.detail || Object.values(error.response?.data || {}).flat().join(' ')));
    console.error("Checkout error:", error);
  }
  setIsProcessing(false);
  };

  return (
    <div className="container-mx py-8">
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-slate-300">
        <h1 className="text-3xl font-bold text-purple-700 flex items-center">
          <ShoppingCart size={32} className="mr-3" /> Your Shopping Cart
        </h1>
        {cartItems.length > 0 && (
          <Button 
            variant="ghost" 
            className="text-sm text-red-600 hover:text-red-800"
            onClick={clearCart} // Use clearCart from context
          >
            <XCircle size={16} className="mr-1"/> Clear Cart
          </Button>
        )}
      </div>

      {cartItems.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-lg shadow-md">
          <ShoppingCart size={64} className="mx-auto text-slate-300 mb-6" />
          <h2 className="text-2xl font-semibold text-slate-700 mb-3">Your cart is empty.</h2>
          <p className="text-slate-500 mb-6">Looks like you haven't added any items to your cart yet.</p>
          <Link to="/materials">
            <Button variant="primary" className="bg-purple-600 hover:bg-purple-700">
              Browse Materials
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Cart Items List */}
          <div className="lg:col-span-2 bg-white p-4 sm:p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Items ({cartItems.reduce((acc, item) => acc + item.quantity, 0)})</h2>
            <ul className="divide-y divide-slate-200">
              {cartItems.map(item => (
                <li key={`${item.type}-${item.id}`} className="py-4 flex flex-col sm:flex-row items-start space-y-3 sm:space-y-0 sm:space-x-4">
                  <img 
                    src={item.image || `https://via.placeholder.com/100?text=${item.name ? encodeURIComponent(item.name.substring(0,10)) : 'Item'}`} 
                    alt={item.name} 
                    className="w-24 h-24 sm:w-20 sm:h-20 object-cover rounded-md border border-slate-200" 
                  />
                  <div className="flex-grow">
                    <Link to={`/${item.type === 'design' ? 'designs' : 'materials'}/${item.slug}`} className="text-md font-semibold text-purple-700 hover:underline">
                      {item.name}
                    </Link>
                    <p className="text-xs text-slate-500">Price: {formatCurrency(item.price)} {item.unit}</p>
                    <div className="flex items-center mt-2">
                      <label htmlFor={`quantity-${item.id}-${item.type}`} className="text-xs text-slate-500 mr-2 sr-only">Qty:</label>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="p-1 text-slate-500 hover:text-purple-600"
                        onClick={() => handleQuantityChange(item.id, item.type, item.quantity, -1)}
                        aria-label="Decrease quantity"
                      >
                        <MinusCircle size={18}/>
                      </Button>
                      <input 
                        type="number" // Could be text for better control, but number is fine
                        id={`quantity-${item.id}-${item.type}`}
                        value={item.quantity} 
                        readOnly // Prevent direct typing, use buttons
                        className="w-12 p-1 text-sm text-center border-y border-slate-300 focus:outline-none"
                      />
                       <Button 
                        size="sm" 
                        variant="ghost" 
                        className="p-1 text-slate-500 hover:text-purple-600"
                        onClick={() => handleQuantityChange(item.id, item.type, item.quantity, 1)}
                        aria-label="Increase quantity"
                      >
                        <PlusCircle size={18}/>
                      </Button>
                    </div>
                  </div>
                  <div className="text-left sm:text-right mt-2 sm:mt-0">
                    <p className="text-md font-semibold text-slate-800">
                      {formatCurrency(item.quantity * parseFloat(item.price))}
                    </p>
                    <button 
                      onClick={() => removeItemFromCart(item.id, item.type)}
                      className="text-xs text-red-500 hover:text-red-700 hover:underline mt-1 flex items-center"
                    >
                      <XCircle size={14} className="mr-1"/>Remove
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white p-6 rounded-lg shadow-md sticky top-24">
              <h2 className="text-xl font-semibold text-slate-800 mb-4 border-b pb-3">Order Summary</h2>
              <div className="space-y-2 text-sm text-slate-600">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span>{formatCurrency(cartSubtotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Shipping (Estimate)</span>
                  <span>{formatCurrency(shippingEstimate)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tax (Estimate)</span>
                  <span>{formatCurrency(taxEstimate)}</span>
                </div>
                <div className="border-t pt-3 mt-3 flex justify-between font-semibold text-lg text-slate-800">
                  <span>Order Total</span>
                  <span>{formatCurrency(orderTotal)}</span>
                </div>
              </div>
              <Button 
                variant="primary" 
                className="w-full mt-6 bg-purple-600 hover:bg-purple-700"
                onClick={handleCheckout}
                isLoading={isProcessing}
                disabled={isProcessing || cartItems.length === 0}
              >
                {isProcessing ? "Processing..." : "Proceed to Checkout"}
              </Button>
              {!isAuthenticated && cartItems.length > 0 && (
                <p className="text-xs text-center mt-3 text-slate-500">
                  You'll be asked to <Link to="/auth/login" state={{from: location}} className="text-purple-600 hover:underline">Login</Link> or <Link to="/auth/register" state={{from: location}} className="text-purple-600 hover:underline">Register</Link> to complete your order.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CartPage;