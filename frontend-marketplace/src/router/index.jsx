// src/router/index.jsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

import MainLayout from '../layouts/MainLayout.jsx';
import AuthLayout from '../layouts/AuthLayout.jsx';
import DashboardLayout from '../layouts/DashboardLayout.jsx'; // Assuming this is created

import HomePage from '../pages/HomePage.jsx';
import LoginPage from '../pages/LoginPage.jsx';
import RegisterPage from '../pages/RegisterPage.jsx';
import NotFoundPage from '../pages/NotFoundPage.jsx';
import MaterialSearchPage from '../pages/MaterialSearchPage.jsx'; // Example
// Dashboard Pages (placeholders for now)
import UserProfilePage from '../pages/profile/UserProfilePage.jsx'; // Example path
import MyOrdersPage from '../pages/orders_management/MyOrdersPage.jsx'; // Example path
import SellerDashboardPage from '../pages/dashboards/SellerDashboardPage.jsx'; // Example
import EditProfilePage from '../pages/profile/EditProfilePage.jsx';
import MyMaterialsPage from '../pages/listings_management/MyMaterialsPage.jsx';

import CreateListingPage from '../pages/listings_management/CreateListingPage.jsx';
import OrderDetailPage from '../pages/orders_management/OrderDetailPage.jsx';
import ForumsPage from '../pages/community/ForumsPage.jsx';
import ForumThreadPage from '../pages/community/ForumThreadPage.jsx';

import PrivateRoute from './PrivateRoute.jsx';

const router = createBrowserRouter([
  {
    element: <MainLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: 'materials', element: <MaterialSearchPage /> },
      { path: 'community/forums', element: <ForumsPage /> },
      //{ path: 'community/forums/:categorySlug/:threadSlug', element: <ForumThreadPage /> },
      { path: 'community/threads/:threadSlug', element: <ForumThreadPage /> },
      // { path: 'materials/:slug', element: <MaterialDetailPage /> },
      // { path: 'designs', element: <DesignSearchPage /> },
      // { path: 'designs/:slug', element: <DesignDetailPage /> },
      // { path: 'community/forums', element: <ForumsPage /> },
      // { path: 'community/forums/:threadSlug', element: <ForumThreadPage /> },
      // { path: 'portfolios/:username', element: <UserPortfolioPage /> },
      { path: '*', element: <NotFoundPage /> }, // Catch-all inside MainLayout
    ],
  },
  {
    path: '/auth',
    element: <AuthLayout />,
    children: [
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
    ],
  },
  {
    path: '/dashboard',
    element: <PrivateRoute><DashboardLayout /></PrivateRoute>,
    children: [
      { index: true, element: <SellerDashboardPage /> }, // Example default dashboard
      { path: 'profile', element: <UserProfilePage /> },
      { path: 'profile/edit', element: <EditProfilePage /> },
      { path: 'my-orders', element: <MyOrdersPage /> },
      { path: 'my-materials', element: <MyMaterialsPage /> },
      { path: 'listings/create', element: <CreateListingPage /> },
      { path: 'orders/:orderId', element: <OrderDetailPage /> },
      // Add more role-specific routes if needed
      // e.g. { path: 'my-materials', element: <PrivateRoute allowedUserTypes={['seller', 'manufacturer']}><MyMaterialsPage /></PrivateRoute> },
    ],
  },
  // A top-level catch-all if no layout matches, or handle in MainLayout's *
  // { path: '*', element: <NotFoundPage /> }
]);

const AppRouter = () => {
  return <RouterProvider router={router} />;
};

export default AppRouter;