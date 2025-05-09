// src/layouts/DashboardLayout.jsx
import React from 'react';
import { Outlet, NavLink, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Button from '../components/common/Button';
// Placeholder icons (replace with actual SVGs or an icon library)
const UserIcon = () => <span className="mr-2">👤</span>;
const OrdersIcon = () => <span className="mr-2">📦</span>;
const ListingsIcon = () => <span className="mr-2">🏷️</span>;
const SettingsIcon = () => <span className="mr-2">⚙️</span>;
const LogoutIcon = () => <span className="mr-2">🚪</span>;


const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // Dynamically generate sidebar links based on user type
  const getSidebarLinks = () => {
    const commonLinks = [
      { to: '/dashboard/profile', label: 'Profile', icon: <UserIcon /> },
      { to: '/dashboard/my-orders', label: 'My Orders', icon: <OrdersIcon /> },
      { to: '/dashboard/settings', label: 'Settings', icon: <SettingsIcon /> }, // Placeholder
    ];

    let userSpecificLinks = [];
    if (user?.user_type === 'seller' || user?.user_type === 'manufacturer') {
      userSpecificLinks = [
        { to: '/dashboard/my-materials', label: 'My Materials', icon: <ListingsIcon /> },
        { to: '/dashboard/rfqs', label: 'Received RFQs', icon: <ListingsIcon /> }, // Placeholder
      ];
    } else if (user?.user_type === 'designer') {
      userSpecificLinks = [
        { to: '/dashboard/my-designs', label: 'My Designs', icon: <ListingsIcon /> },
        { to: '/dashboard/my-portfolio', label: 'My Portfolio', icon: <ListingsIcon /> }, // Placeholder
      ];
    } else if (user?.user_type === 'buyer') {
        userSpecificLinks = [
            { to: '/dashboard/my-rfqs', label: 'My RFQs', icon: <ListingsIcon /> }, // Placeholder
        ];
    }
    return [...commonLinks, ...userSpecificLinks];
  };

  const sidebarLinks = getSidebarLinks();

  return (
    <div className="flex h-screen bg-gray-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 text-gray-100 flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <Link to="/dashboard" className="text-xl font-bold hover:text-white">
            {user?.profile?.company_name || user?.username || 'Dashboard'}
          </Link>
        </div>
        <nav className="flex-grow p-2 space-y-1">
          {sidebarLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/dashboard'} // For exact match on dashboard index
              className={({ isActive }) =>
                `flex items-center px-3 py-2.5 rounded-md text-sm font-medium hover:bg-gray-700 hover:text-white transition-colors
                ${isActive ? 'bg-blue-600 text-white' : 'text-gray-300'}`
              }
            >
              {link.icon}
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-700">
          <Button onClick={handleLogout} variant="ghost" className="w-full text-gray-300 hover:bg-red-600 hover:text-white justify-start">
            <LogoutIcon /> Logout
          </Button>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white shadow-sm p-4 flex justify-between items-center">
          {/* Could have breadcrumbs or page title here */}
          <h1 className="text-xl font-semibold text-gray-700">Welcome, {user?.first_name || user?.username}!</h1>
          {/* Other header elements like notifications, user menu */}
          <Link to="/">
            <Button variant="outline" size="sm">Back to Site</Button>
          </Link>
        </header>
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-200 p-6">
          <Outlet /> {/* Page content renders here */}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;