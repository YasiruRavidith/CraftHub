// src/components/layout/Navbar.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Search, User, LogOut, LayoutGrid, Menu, X, ShoppingBag, Settings, ShoppingCart } from 'lucide-react'; // Added ShoppingCart
import { useCart } from '../../contexts/CartContext';

const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);
  // const { cartItemCount } = useCart(); // Placeholder for cart context to get item count

  const { cartItemCount } = useCart();

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

  // Adjusted link styles for your dark navbar (bg-gray-900)
  const activeLinkStyle = "bg-purple-700 text-white"; // Your active style
  const inactiveLinkStyle = "hover:bg-purple-200 text-white hover:text-gray-950"; // Your inactive style for main nav links

  const navLinkClasses = ({ isActive }) =>
    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive ? activeLinkStyle : inactiveLinkStyle
    }`;

  // Mobile menu is on a white background, so styles are different
  const mobileMenuBaseStyle = "block px-3 py-2 rounded-md text-base font-medium transition-colors";
  const mobileNavLinkClasses = ({ isActive }) =>
    `${mobileMenuBaseStyle} ${
      isActive ? "bg-teal-600 text-white" : "text-slate-700 hover:bg-orange-100 hover:text-teal-800"
    }`;

  // User dropdown menu (white background)
  const userMenuLinkClasses = ({ isActive }) =>
    `flex items-center w-full text-left px-4 py-2 text-sm text-slate-700 mt-1 hover:bg-orange-100 hover:text-teal-800 transition-colors ${
        isActive ? 'bg-orange-200 font-semibold' : ''
    }`;

  const userAvatarSrc = user?.profile?.profile_picture 
    ? user.profile.profile_picture
    : `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.username?.charAt(0) || 'U')}&background=F5EEDD&color=06202B&size=36&bold=true`;

  return (
    <nav className="bg-gray-900 shadow-lg sticky top-0 z-50 "> {/* Your dark navbar background */}
      <div className="container-mx mt-2 mb-2">
        <div className="flex items-center justify-between h-16">
          <div className="flex-shrink-0 ml-5"> {/* text-amber-300 removed for Link */}
            <Link to="/" className="text-2xl font-bold text-white hover:text-orange-200 transition-colors">
                Craft Hub {/* Changed from nested div */}
            </Link>
          </div>

          {/* Desktop Navigation Links */}
          <div className="hidden md:flex md:items-center md:space-x-2 lg:space-x-4">
            <NavLink to="/materials" className={navLinkClasses}>
                <span className="font-medium">Materials</span> {/* Use span if div was for styling */}
            </NavLink>
            <NavLink to="/designs" className={navLinkClasses}>
                <span className="font-medium">Designs</span>
            </NavLink>
            <NavLink to="/community/forums" className={navLinkClasses}>
                <span className="font-medium">Forums</span>
            </NavLink>
          </div>

          {/* Right side of Navbar */}
          <div className="flex items-center space-x-3 md:space-x-4">
            {/* Search Icon Button */}
            <button className="text-orange-100 hover:text-white p-2 rounded-full focus:outline-none focus:ring-2 focus:ring-orange-200">
                <Search size={20} strokeWidth={2.5} />
            </button>

            {/* Cart Icon Link - Show if user is a buyer or always if you have a guest cart */}
            {isAuthenticated && user?.user_type === 'buyer' && ( // Example: Only show for buyers
                 <NavLink 
                    to="/cart" 
                    className="text-orange-100 hover:text-white relative p-2 rounded-full focus:outline-none focus:ring-2 focus:ring-orange-200"
                    aria-label="View Shopping Cart"
                >
                    <ShoppingCart size={22} strokeWidth={2.5} />
                    {cartItemCount > 0 && (
                        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center leading-none">
                            {cartItemCount > 9 ? '9+' : cartItemCount}
                        </span>
                    )}
                </NavLink>
            )}
            {!isAuthenticated && ( // Show cart icon for guests too, if you have guest cart
                <NavLink to="/cart" className="text-orange-100 hover:text-white relative p-2 rounded-full focus:outline-none focus:ring-2 focus:ring-orange-200">
                    <ShoppingCart size={22} strokeWidth={2.5} />
                </NavLink>
            )}


            {/* User Menu or Login/Register Links */}
            {isAuthenticated && user ? (
              <div className="relative" ref={userMenuRef}>
                <button // Changed from div to button for accessibility
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-orange-200" // Adjusted ring offset
                  aria-expanded={isUserMenuOpen}
                  aria-haspopup="true"
                  id="user-menu-button" // Added id for aria-labelledby
                >
                  <span className="sr-only">Open user menu</span>
                  <img
                    className="h-10 w-10 rounded-full object-cover border-2 border-transparent hover:border-orange-200" // Slightly smaller avatar
                    src={userAvatarSrc}
                    alt={user.username}
                  />
                </button>
                {isUserMenuOpen && (
                  <div
                    className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-xl py-1 bg-white ring-1 ring-gray-900 ring-opacity-5 focus:outline-none" // Adjusted ring
                    role="menu"
                    aria-orientation="vertical"
                    aria-labelledby="user-menu-button"
                  >
                    {/* ... (user dropdown content - keep as is from previous version) ... */}
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
                    <button // Changed from div to button for accessibility and semantics
                      onClick={handleLogout}
                      className="flex items-center w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-orange-100 hover:text-red-700 transition-colors"
                      role="menuitem"
                    >
                      <LogOut size={16} className="mr-2 text-red-500" />Sign out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="hidden md:flex items-center space-x-1">
                <NavLink
                  to="/auth/login"
                  className="px-4 py-2 rounded-md text-sm font-medium text-orange-100 hover:bg-gray-700 hover:text-white transition-colors"
                >
                  Login
                </NavLink>
                <NavLink
                  to="/auth/register"
                  className="px-4 py-2 rounded-md text-sm font-medium bg-orange-200 text-gray-900 hover:bg-orange-300 transition-colors"
                >
                  Register
                </NavLink>
              </div>
            )}

            {/* Mobile Menu Button */}
            <div className="md:hidden flex items-center">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                type="button"
                className="inline-flex items-center justify-center p-2 rounded-md text-orange-100 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-orange-200"
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

      {/* Mobile Menu (white background) */}
      {isMobileMenuOpen && (
        <div className="md:hidden absolute top-16 inset-x-0 bg-white shadow-lg z-40 p-2 space-y-1 sm:px-3 border-t border-gray-700" id="mobile-menu">
          {/* ... (mobile menu links - keep as is, they are on white bg) ... */}
          <NavLink to="/materials" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>Materials</NavLink>
          <NavLink to="/designs" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>Designs</NavLink>
          <NavLink to="/community/forums" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>Forums</NavLink>
          <NavLink to="/cart" className={mobileNavLinkClasses} onClick={() => setIsMobileMenuOpen(false)}>
            <ShoppingCart size={18} className="inline mr-2 mb-0.5" />
            My Cart {cartItemCount > 0 && <span className="ml-1 bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">{cartItemCount}</span>}
          </NavLink>
          <div className="pt-3 pb-2 space-y-1 border-t border-slate-200 mt-2">
            {isAuthenticated && user ? (
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