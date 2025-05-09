// src/config/routes.js
export const ROUTE_PATHS = {
  HOME: '/',
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  FORGOT_PASSWORD: '/auth/forgot-password', // Example

  MATERIALS_SEARCH: '/materials',
  MATERIAL_DETAIL: '/materials/:slug', // Use :slug or :id
  DESIGNS_SEARCH: '/designs',
  DESIGN_DETAIL: '/designs/:slug',

  DASHBOARD: '/dashboard',
  DASHBOARD_PROFILE: '/dashboard/profile',
  DASHBOARD_EDIT_PROFILE: '/dashboard/profile/edit',
  DASHBOARD_MY_ORDERS: '/dashboard/my-orders',
  DASHBOARD_ORDER_DETAIL: '/dashboard/orders/:orderId',
  DASHBOARD_MY_LISTINGS: '/dashboard/my-listings', // Generic or split
  DASHBOARD_MY_MATERIALS: '/dashboard/my-materials',
  DASHBOARD_MY_DESIGNS: '/dashboard/my-designs',
  DASHBOARD_CREATE_LISTING: '/dashboard/listings/create',

  FORUMS: '/community/forums',
  FORUM_THREAD: '/community/forums/:categorySlug/:threadSlug', // Example if category is in URL
  // OR FORUM_THREAD: '/community/threads/:threadSlug',

  NOT_FOUND: '/404', // Or handle with '*' in router
  UNAUTHORIZED: '/unauthorized',
};

// Helper function to generate URLs with params
export const generatePath = (path, params = {}) => {
  let url = path;
  for (const key in params) {
    url = url.replace(`:${key}`, params[key]);
  }
  return url;
};