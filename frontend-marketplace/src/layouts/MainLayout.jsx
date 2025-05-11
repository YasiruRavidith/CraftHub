// src/layouts/MainLayout.jsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/common/Navbar.jsx';
import Footer from '../components/common/Footer.jsx';


const MainLayout = () => {
  return (
    <div className="flex flex-col min-h-screen bg-[url(/src/assets/AdobeStock_1182440091_Preview.jpeg)] bg-no-repeat bg-cover bg-center bg-fixed"> {/* Default body background will apply here unless overridden */}
      <Navbar /> {/* This has its own bg-teal-800 */}
      
      {/* Main content area - explicitly give it a background if needed, or let body's bg show */}
      <main className="flex-grow container-mx px-5 py-1 bg-purple-800/10 backdrop-blur-2xl"> {/* Using your Orange-100 for main content background */}
                                                               {/* OR use bg-slate-50, bg-white, or remove if body bg-gray-100 is desired */}
        <Outlet />
      </main>
      
      <Footer /> {/* This has its own bg-slate-900 / bg-slate-950 */}
    </div>
  );
};

export default MainLayout;

