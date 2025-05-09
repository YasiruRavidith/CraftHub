import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../common/Button'; // Assuming Button component exists

const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="container-mx flex justify-between items-center py-3">
        <Link to="/" className="text-2xl font-bold text-blue-600 hover:text-blue-700">
          B2BMarket
        </Link>
        <div className="hidden md:flex space-x-6 items-center">
          <NavLink to="/materials" className={({isActive}) => `text-gray-600 hover:text-blue-600 ${isActive ? 'text-blue-600 font-semibold' : ''}`}>Materials</NavLink>
          <NavLink to="/designs" className={({isActive}) => `text-gray-600 hover:text-blue-600 ${isActive ? 'text-blue-600 font-semibold' : ''}`}>Designs</NavLink>
          <NavLink to="/community/forums" className={({isActive}) => `text-gray-600 hover:text-blue-600 ${isActive ? 'text-blue-600 font-semibold' : ''}`}>Forums</NavLink>
        </div>
        <div className="flex items-center space-x-3">
          {isAuthenticated ? (
            <>
              <span className="text-sm text-gray-700 hidden sm:inline">Welcome, {user?.username || 'User'}!</span>
              <NavLink to="/dashboard">
                <Button variant="outline" size="sm">Dashboard</Button>
              </NavLink>
              <Button onClick={logout} variant="secondary" size="sm">
                Logout
              </Button>
            </>
          ) : (
            <>
              <NavLink to="/auth/login">
                <Button variant="ghost" size="sm">Login</Button>
              </NavLink>
              <NavLink to="/auth/register">
                <Button variant="primary" size="sm">Register</Button>
              </NavLink>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;