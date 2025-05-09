// src/layouts/MainLayout.jsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/layout/Navbar.jsx';
import Footer from '../components/layout/Footer.jsx';

const MainLayout = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow container-mx py-6"> {/* Used .container-mx from global.css */}
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};

export default MainLayout;