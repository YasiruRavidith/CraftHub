import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import AppRouter from './router/index.jsx';
import { AuthProvider } from './contexts/AuthContext.jsx'; // We'll create this
import { CartProvider } from './contexts/CartContext.jsx';

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <AppRouter />
      </CartProvider>
      
    </AuthProvider>
  );
}

export default App;