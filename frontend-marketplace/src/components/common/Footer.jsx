// src/components/layout/Footer.jsx
import React from 'react';
import { Link } from 'react-router-dom';
// import { FaFacebookF, FaTwitter, FaLinkedinIn, FaInstagram } from 'react-icons/fa'; // Example using react-icons

const Footer = () => {
  return (
    <footer className="bg-violet-950 text-slate-300 pt-16 pb-8">
      <div className="container-mx">
        <div className="flex flex-col items-center mb-10">
          <Link to="/" className="text-3xl font-bold text-white mb-4">
            B2BMarket
          </Link>
          <p className="text-center max-w-md text-sm mb-6">
            Your central hub for sourcing, design, and manufacturing in the apparel industry.
          </p>
          {/* Social Media Links */}
          <div className="flex space-x-6 mb-8">
            {/* Example with react-icons. Install: npm install react-icons */}
            {/* <a href="#" className="text-slate-400 hover:text-teal-300 text-xl" aria-label="Facebook"><FaFacebookF /></a>
            <a href="#" className="text-slate-400 hover:text-teal-300 text-xl" aria-label="Twitter"><FaTwitter /></a>
            <a href="#" className="text-slate-400 hover:text-teal-300 text-xl" aria-label="LinkedIn"><FaLinkedinIn /></a>
            <a href="#" className="text-slate-400 hover:text-teal-300 text-xl" aria-label="Instagram"><FaInstagram /></a> */}
            <a href="#" className="text-slate-400 hover:text-teal-300 text-xl" aria-label="Facebook">FB</a>
            <a href="#" className="text-slate-400 hover:text-teal-300 text-xl" aria-label="Twitter">TW</a>
            <a href="#" className="text-slate-400 hover:text-teal-300 text-xl" aria-label="LinkedIn">LI</a>
            <a href="#" className="text-slate-400 hover:text-teal-300 text-xl" aria-label="Instagram">IG</a>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex flex-wrap justify-center gap-x-6 gap-y-3 mb-10 text-sm">
          <Link to="/about" className="hover:text-teal-300 transition-colors">About Us</Link>
          <Link to="/materials" className="hover:text-teal-300 transition-colors">Browse Materials</Link>
          <Link to="/designs" className="hover:text-teal-300 transition-colors">Discover Designs</Link>
          <Link to="/contact" className="hover:text-teal-300 transition-colors">Contact</Link>
          <Link to="/faq" className="hover:text-teal-300 transition-colors">FAQ</Link>
          <Link to="/terms" className="hover:text-teal-300 transition-colors">Terms of Service</Link>
          <Link to="/privacy" className="hover:text-teal-300 transition-colors">Privacy Policy</Link>
        </nav>

        <div className="border-t border-slate-700 pt-8 text-center text-xs text-slate-500">
          <p>© {new Date().getFullYear()} B2B Garment Marketplace. A Fictional Company.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;