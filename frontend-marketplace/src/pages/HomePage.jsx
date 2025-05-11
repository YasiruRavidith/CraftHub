// src/pages/HomePage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/common/Button'; // Assuming your Button component uses variants or can take className

const HomePage = () => {
  return (
    // Using Orange-200 as the main background for the page content area
    // If MainLayout provides a global background, this might just be for a section
    <div className=" bg-[url(/src/assets/AdobeStock_1182440091_Preview.jpeg)] bg-no-repeat bg-cover bg-center bg-fixed ">
      {/* Using orange-100 for a slightly softer orange background. Adjust if orange-200 is preferred. */}
      {/* The min-h calculation is a rough way to ensure content fills screen assuming combined navbar/footer height of 8rem */}
      <div className='text-center py-10 md:py-20 min-h-[calc(100vh-2rem)] flex flex-col justify-center bg-purple-800/10 backdrop-blur-sm'>
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-white mb-6">
        Craft Hub
      </h1>
      <p className="text-lg md:text-xl text-purple-200 mb-10 max-w-2xl mx-auto">
        Discover, connect, and collaborate with manufacturers, designers, and material suppliers in the global garment industry.
      </p>
      <div className="space-y-4 sm:space-y-0 sm:space-x-6">
        <Link to="/materials">
          {/* Modify Button component or pass classes if variant="custom" is not supported */}
          <Button
            size="lg"
            // If your Button has a variant that matches teal-800, use that.
            // Otherwise, apply classes directly.
            className="bg-teal-800 hover:bg-teal-900 text-white"
          >
            Browse Materials
          </Button>
        </Link>
        <Link to="/auth/register">
          <Button
            size="lg"
            // Using teal-300 for accent, with dark text for contrast
            className="bg-teal-300 hover:bg-teal-400 text-slate-950 border-2 border-teal-300 hover:border-teal-500"
          >
            Join as a Member
          </Button>
        </Link>
      </div>

      {/* Featured items section */}
      <div className="mt-16 md:mt-24">
        <h2 className="text-3xl font-semibold text-pink-500 mb-8">
          Featured Highlights
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8 max-w-5xl mx-auto">
          {/* Placeholder cards - apply new theme */}
          <div className="p-6 bg-white rounded-xl shadow-lg transform hover:scale-105 transition-transform duration-300">
            <h3 className="text-xl font-semibold text-teal-800 mb-2">Innovative Fabrics</h3>
            <p className="text-sm text-slate-700">Explore our latest collection of sustainable and tech-forward materials.</p>
          </div>
          <div className="p-6 bg-white rounded-xl shadow-lg transform hover:scale-105 transition-transform duration-300">
            <h3 className="text-xl font-semibold text-teal-800 mb-2">Top Designers</h3>
            <p className="text-sm text-slate-700">Connect with creative minds shaping the future of fashion.</p>
          </div>
          <div className="p-6 bg-white rounded-xl shadow-lg transform hover:scale-105 transition-transform duration-300">
            <h3 className="text-xl font-semibold text-teal-800 mb-2">Trusted Manufacturers</h3>
            <p className="text-sm text-slate-700">Find reliable partners for your production needs.</p>
          </div>
        </div>
      </div>

      </div>

      
    </div>
  );
};

export default HomePage;