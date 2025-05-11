// src/contexts/CartContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';

const CartContext = createContext(null);

const CART_STORAGE_KEY = 'b2bMarketplaceCart';

export const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState(() => {
    // Load cart from localStorage on initial load
    try {
      const localData = localStorage.getItem(CART_STORAGE_KEY);
      return localData ? JSON.parse(localData) : [];
    } catch (error) {
      console.error("Could not parse cart from localStorage", error);
      return [];
    }
  });

  // Save cart to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cartItems));
  }, [cartItems]);

  const addItemToCart = (product, quantity = 1) => {
    setCartItems(prevItems => {
      const existingItem = prevItems.find(item => item.id === product.id && item.type === product.type);
      if (existingItem) {
        // If item already exists, update quantity
        return prevItems.map(item =>
          item.id === product.id && item.type === product.type
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      } else {
        // Add new item
        // Ensure product has an 'id' and a 'type' ('material' or 'design')
        // Also include necessary display info like name, price, image, slug
        return [...prevItems, { 
            ...product, // Spread product details
            id: product.id || product.slug, // Ensure unique identifier
            type: product.type || (product.price_per_unit ? 'material' : 'design'), // Determine type
            quantity,
            // Store relevant product details for cart display
            name: product.name || product.title,
            price: parseFloat(product.price_per_unit || product.price || 0).toFixed(2),
            unit: product.unit || (product.price_per_unit ? '' : '(license)'),
            image: product.main_image_url || product.thumbnail_image_url,
            slug: product.slug
        }];
      }
    });
    console.log("Added to cart:", product, "Quantity:", quantity);
  };

  const updateItemQuantity = (itemId, itemType, newQuantity) => {
    setCartItems(prevItems =>
      prevItems.map(item =>
        item.id === itemId && item.type === itemType
          ? { ...item, quantity: Math.max(1, newQuantity) } // Ensure quantity is at least 1
          : item
      )
    );
  };

  const removeItemFromCart = (itemId, itemType) => {
    setCartItems(prevItems => prevItems.filter(item => !(item.id === itemId && item.type === itemType)));
  };

  const clearCart = () => {
    setCartItems([]);
  };

  const cartItemCount = cartItems.reduce((count, item) => count + item.quantity, 0);

  const cartSubtotal = cartItems.reduce(
    (total, item) => total + item.quantity * parseFloat(item.price),
    0
  );

  const value = {
    cartItems,
    addItemToCart,
    updateItemQuantity,
    removeItemFromCart,
    clearCart,
    cartItemCount,
    cartSubtotal,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (context === undefined || context === null) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};