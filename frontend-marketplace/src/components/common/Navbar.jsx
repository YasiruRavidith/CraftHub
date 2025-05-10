// src/components/layout/Navbar.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
// Assuming you have Button component and lucide-react installed
// import Button from '../common/Button'; // No longer used in this version for Login/Register
import { Search, User, LogOut, LayoutGrid, Menu, X, ShoppingBag, Settings } from 'lucide-react';

const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);

  const handleLogout = () => {
    logout();
    setIsUserMenuOpen(false);
    setIsMobileMenuOpen(false);
    navigate('/');
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const activeLinkStyle = "bg-purple-700 text-gray-950";
  const inactiveLinkStyle = "hover:bg-purple-200 text-gray-950";

  const navLinkClasses = ({ isActive }) =>
    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive ? activeLinkStyle : inactiveLinkStyle
    }`;

  const mobileMenuBaseStyle = "block px-3 py-2 rounded-md text-base font-medium transition-colors";
  const mobileNavLinkClasses = ({ isActive }) =>
    `${mobileMenuBaseStyle} ${
      isActive ? "bg-teal-600 text-white" : "text-slate-700 hover:bg-orange-100 hover:text-teal-800"
    }`;

  const userMenuLinkClasses = ({ isActive }) =>
    `flex items-center w-full text-left px-4 py-2 text-sm text-slate-700 mt-1 hover:bg-orange-100 hover:text-teal-800 transition-colors ${
        isActive ? 'bg-orange-200 font-semibold' : ''
    }`;

  const userAvatarSrc = user?.profile?.profile_picture 
    ? user.profile.profile_picture
    : `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.username?.charAt(0) || 'U')}&background=F5EEDD&color=06202B&size=36&bold=true`;
    // Using encodeURIComponent for the name character, just in case, though usually not needed for a single char.

  return (
    <nav className="bg-gray-900 shadow-lg sticky top-0 z-50 ">
      <div className="container-mx mt-2 mb-2">
        <div className="flex items-center justify-between h-16">
          <div className="flex-shrink-0 ml-5 text-amber-300">
            <Link to="/" className="text-2xl font-bold text-white hover:text-orange-200 transition-colors">
                <div className="text-2xl font-bold text-white hover:text-orange-200 transition-colors"> Craft Hub</div>
             
            </Link>
          </div>

          <div className="hidden md:flex md:items-center md:space-x-2 lg:space-x-4">
            <NavLink to="/materials" className={navLinkClasses}><div className=" font-bold text-white hover:text-purple-950">Materials</div></NavLink>
            <NavLink to="/designs" className={navLinkClasses}><div className=" font-bold text-white hover:text-purple-950">Designs</div></NavLink>
            <NavLink to="/community/forums" className={navLinkClasses}><div className=" font-bold text-white hover:text-purple-950">Forums</div></NavLink>
          </div>

          <div className="flex items-center space-x-2 md:space-x-3">
            <div className="text-orange-100 hover:text-blue-500 p-2 rounded-full focus:outline-none focus:ring-2">
              
                <Search size={20} strokeWidth={2.5} />
              
            </div>

            {isAuthenticated && user ? ( // Added check for user object
              <div className="relative" ref={userMenuRef}>
                <div
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-teal-800 focus:ring-orange-200 mr-5"
                  aria-expanded={isUserMenuOpen}
                  aria-haspopup="true"
                >
                  <span className="sr-only">Open user menu</span>
                  <img
                    className="h-12 w-12 rounded-full object-cover border-2 border-transparent hover:border-orange-200"
                    src={userAvatarSrc} // Use the constructed variable
                    alt={user.username}
                  />
                </div>
                {isUserMenuOpen && (
                  <div
                    className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-xl py-1 bg-white ring-1 ring-opacity-5 focus:outline-none"
                    role="menu"
                    aria-orientation="vertical"
                    aria-labelledby="user-menu-button"
                  >
                    <div className="px-4 py-3 border-b border-slate-200">
                      <p className="text-sm text-slate-800 font-medium truncate">
                        {user.first_name || user.username}
                      </p>
                      <p className="text-xs text-slate-500 truncate ">{user.email}</p>
                    </div>
                    <NavLink to="/dashboard" className={userMenuLinkClasses} role="menuitem" onClick={() => setIsUserMenuOpen(false)}>
                      <LayoutGrid size={16} className="mr-2 text-slate-500" />Dashboard
                    </NavLink>
                    <NavLink to="/dashboard/profile" className={userMenuLinkClasses} role="menuitem" onClick={() => setIsUserMenuOpen(false)}>
                       <User size={16} className="mr-2 text-slate-500" />Your Profile
                    </NavLink>
                    <NavLink to="/dashboard/my-orders" className={userMenuLinkClasses} role="menuitem" onClick={() => setIsUserMenuOpen(false)}>
                       <ShoppingBag size={16} className="mr-2 text-slate-500" />My Orders
                    </NavLink>
                    <NavLink to="/dashboard/settings" className={userMenuLinkClasses} role="menuitem" onClick={() => setIsUserMenuOpen(false)}>
                       <Settings size={16} className="mr-2 text-slate-500" />Settings
                    </NavLink>
                    <div className="border-t border-slate-200 my-1"></div>
                    <div
                      onClick={handleLogout}
                      className="flex items-center w-full mt-3 text-left px-4 py-2 text-sm text-slate-700 hover:bg-orange-400 hover:text-red-700 transition-colors"
                      role="menuitem"
                    >
                      <LogOut size={16} className="mr-2 text-red-500" />Sign out
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="hidden md:flex items-center space-x-1 text-gray-950">
                <NavLink
                  to="/auth/login"
                  className="px-3 py-2 rounded-md text-sm font-medium bg-blue-700 text-gray-950 hover:bg-orange-300 transition-colors"
                >
                    <div className="px-4 py-1 rounded-md text-sm font-medium bg-blue-700 text-gray-950 hover:bg-orange-300 transition-colors">Login</div>
                  
                </NavLink>
                <NavLink
                  to="/auth/register"
                  className="px-3 py-2 rounded-md text-sm font-medium bg-blue-700  hover:bg-orange-300 transition-colors"
                >
                    <div className="px-2 py-1 rounded-md text-sm font-medium bg-blue-700 text-gray-950 hover:bg-orange-300 transition-colors">Register</div>
                  
                </NavLink>
              </div>
            )}

            <div className="md:hidden flex items-center">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                type="button"
                className="inline-flex items-center justify-center p-2 rounded-md text-orange-100 hover:text-white hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-orange-200"
                aria-controls="mobile-menu"
                aria-expanded={isMobileMenuOpen}
              >
                <span className="sr-only">Open main menu</span>
                {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {isMobileMenuOpen && (
        <div className="md:hidden absolute top-16 inset-x-0 bg-white shadow-lg z-40 p-2 space-y-1 sm:px-3 border-t border-teal-700" id="mobile-menu">
          <NavLink to="/materials" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>Materials</NavLink>
          <NavLink to="/designs" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>Designs</NavLink>
          <NavLink to="/community/forums" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>Forums</NavLink>
          <div className="pt-3 pb-2 space-y-1 border-t border-slate-200 mt-2">
            {isAuthenticated && user ? ( // Added check for user
              <>
                <NavLink to="/dashboard" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>
                  <LayoutGrid size={18} className="inline mr-2 mb-0.5" />Dashboard
                </NavLink>
                <NavLink to="/dashboard/profile" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>
                  <User size={18} className="inline mr-2 mb-0.5" />Your Profile
                </NavLink>
                 <NavLink to="/dashboard/my-orders" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>
                  <ShoppingBag size={18} className="inline mr-2 mb-0.5" />My Orders
                </NavLink>
                <button
                  onClick={handleLogout}
                  className="flex items-center w-full text-left px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-orange-100 hover:text-red-700"
                >
                  <LogOut size={18} className="inline mr-2 mb-0.5" />Sign out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/auth/login" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>Login</NavLink>
                <NavLink to="/auth/register" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>Register</NavLink>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;