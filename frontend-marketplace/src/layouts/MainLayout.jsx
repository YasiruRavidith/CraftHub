// src/layouts/MainLayout.jsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/common/Navbar.jsx';
import Footer from '../components/common/Footer.jsx';

const MainLayout = () => {
  return (
    <div className="flex flex-col min-h-screen w-full bg-gray-500">
      <Navbar />
      <main className="flex-grow container-mx py-6"> {/* Used .container-mx from global.css */}
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};

export default MainLayout;