// src/router/index.jsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

// --- Layouts ---
import MainLayout from '../layouts/MainLayout.jsx';
import AuthLayout from '../layouts/AuthLayout.jsx';
import DashboardLayout from '../layouts/DashboardLayout.jsx';

// --- General Pages ---
import HomePage from '../pages/HomePage.jsx';
import LoginPage from '../pages/LoginPage.jsx';
import RegisterPage from '../pages/RegisterPage.jsx';
import NotFoundPage from '../pages/NotFoundPage.jsx';

// --- Listing (Product) Pages ---
import MaterialSearchPage from '../pages/MaterialSearchPage.jsx';
import MaterialDetailPage from '../pages/MaterialDetailPage.jsx'; // Assuming this exists or will be created
import DesignSearchPage from '../pages/DesignSearchPage.jsx';
import DesignDetailPage from '../pages/DesignDetailPage.jsx';   // Assuming this exists or will be created

// --- Community Pages ---
import ForumsPage from "../pages/community/ForumsPage.jsx";
import ForumThreadPage from '../pages/community/ForumThreadPage.jsx';
// import UserPortfoliosPage from '../pages/community/UserPortfoliosPage.jsx'; // Placeholder

// --- Dashboard Pages ---
// Main Dashboards
import SellerDashboardPage from '../pages/dashboards/SellerDashboardPage.jsx'; // Example default
// import BuyerDashboardPage from '../pages/dashboards/BuyerDashboardPage.jsx';
// import DesignerDashboardPage from '../pages/dashboards/DesignerDashboardPage.jsx';
// import ManufacturerDashboardPage from '../pages/dashboards/ManufacturerDashboardPage.jsx';

// Profile
import UserProfilePage from '../pages/profile/UserProfilePage.jsx';
import EditProfilePage from '../pages/profile/EditProfilePage.jsx';

// Listings Management
import MyMaterialsPage from '../pages/listings_management/MyMaterialsPage.jsx';
import MyDesignsPage from '../pages/listings_management/MyDesignsPage.jsx'; // New
import CreateListingPage from '../pages/listings_management/CreateListingPage.jsx';
// import EditListingPage from '../pages/listings_management/EditListingPage.jsx'; // Placeholder

// Orders Management
import MyOrdersPage from '../pages/orders_management/MyOrdersPage.jsx';
import OrderDetailPage from '../pages/orders_management/OrderDetailPage.jsx';
// import CreateRFQPage from '../pages/orders_management/CreateRFQPage.jsx'; // Placeholder

// --- Router Configuration ---
import PrivateRoute from './PrivateRoute.jsx';
// import { ROUTE_PATHS } from '../config/routes.js'; // Optional: Using string paths directly for now

const router = createBrowserRouter([
  {
    element: <MainLayout />, // Wraps all public-facing pages
    children: [
      { path: '/', element: <HomePage /> },
      { path: 'materials', element: <MaterialSearchPage /> },
      { path: 'materials/:slug', element: <MaterialDetailPage /> }, // Use :slug or :id
      { path: 'designs', element: <DesignSearchPage /> },
      { path: 'designs/:slug', element: <DesignDetailPage /> },   // Use :slug or :id
      { path: 'community/forums', element: <ForumsPage /> },
      { path: 'community/threads/:threadSlug', element: <ForumThreadPage /> },
      // Example for portfolios
      // { path: 'portfolios/:username', element: <UserPortfoliosPage /> },
      { path: '*', element: <NotFoundPage /> }, // Catch-all for unknown routes under MainLayout
    ],
  },
  {
    path: '/auth', // Group for authentication pages
    element: <AuthLayout />,
    children: [
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      // { path: 'forgot-password', element: <ForgotPasswordPage /> },
    ],
  },
  {
    path: '/dashboard', // Group for all authenticated dashboard sections
    element: <PrivateRoute><DashboardLayout /></PrivateRoute>,
    children: [
      // Default dashboard page (can be user-type specific later)
      { index: true, element: <SellerDashboardPage /> }, // Example: defaults to seller dashboard
      
      // Profile
      { path: 'profile', element: <UserProfilePage /> },
      { path: 'profile/edit', element: <EditProfilePage /> },
      
      // Listings Management
      { path: 'my-materials', element: <MyMaterialsPage /> },
      { path: 'my-designs', element: <MyDesignsPage /> }, // New
      { path: 'listings/create', element: <CreateListingPage /> },
      // { path: 'listings/material/:slug/edit', element: <EditListingPage type="material" /> },
      // { path: 'listings/design/:slug/edit', element: <EditListingPage type="design" /> },
      
      // Orders Management
      { path: 'my-orders', element: <MyOrdersPage /> },
      { path: 'orders/:orderId', element: <OrderDetailPage /> },
      // { path: 'rfqs/create', element: <CreateRFQPage /> },

      // Collaborations (Example placeholders)
      // { path: 'projects', element: <CollaborationProjectsPage /> },
      // { path: 'projects/:projectId', element: <ProjectDetailPage /> },

      // Settings (Example placeholder)
      // { path: 'settings', element: <SettingsPage /> },

      // Add more dashboard sub-routes here based on user roles and features
      // Example: An admin might have a different set of routes or a different index.
    ],
  },
  // A top-level catch-all if no path group matches (e.g. /foo - this will show NotFoundPage without MainLayout)
  // Usually, the '*' inside MainLayout is sufficient for typical 404 handling.
  // { path: '*', element: <NotFoundPage /> } 
]);

const AppRouter = () => {
  return <RouterProvider router={router} />;
};

export default AppRouter;