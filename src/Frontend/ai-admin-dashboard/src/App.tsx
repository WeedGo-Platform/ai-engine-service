import React from 'react';
import { createBrowserRouter, RouterProvider, Link, Outlet, useLocation, Navigate, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import {
  Home, Package, ShoppingCart, Users, FileText,
  TrendingUp, Leaf, Menu, X, LogOut, Settings,
  Building2, Store, Tag, Sparkles, Upload, ChevronRight
} from 'lucide-react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { StoreProvider, useStoreContext } from './contexts/StoreContext';
import ProtectedRoute from './components/ProtectedRoute';
import StoreSelectionModal from './components/StoreSelectionModal';

// Import pages
import Login from './pages/Login';
import Landing from './pages/Landing';
import TenantSignup from './pages/TenantSignup';
import UserRegistration from './pages/UserRegistration';
import Verification from './pages/Verification';
import SignupSuccess from './pages/SignupSuccess';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Inventory from './pages/Inventory';
import Accessories from './pages/Accessories';
import Orders from './pages/Orders';
import Customers from './pages/Customers';
import PurchaseOrders from './pages/PurchaseOrders';
import TenantManagement from './pages/TenantManagement';
import TenantSettings from './pages/TenantSettings';
import TenantPaymentSettings from './pages/TenantPaymentSettings';
import StoreManagement from './pages/StoreManagement';
import StoreSettings from './pages/StoreSettings';
import StoreHoursManagement from './pages/StoreHoursManagement';
import Promotions from './pages/Promotions';
import Recommendations from './pages/Recommendations';
import POS from './pages/POS';
import ProvincialCatalogVirtual from './pages/ProvincialCatalogVirtual';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Layout component
function Layout() {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [showStoreModal, setShowStoreModal] = React.useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, loading, isSuperAdmin, isTenantAdmin, isStoreManager } = useAuth();
  const { currentStore, selectStore } = useStoreContext();
  const [selectedTenant, setSelectedTenant] = React.useState<{id: string, name: string} | null>(null);

  // Set tenant for tenant admins automatically
  React.useEffect(() => {
    if (isTenantAdmin() && !isSuperAdmin() && user?.tenant_id) {
      // For tenant admins, set their tenant automatically
      const tenantName = user?.tenants?.[0]?.name || 'Tenant';
      setSelectedTenant({ id: user.tenant_id, name: tenantName });
    }
  }, [user, isTenantAdmin, isSuperAdmin]);

  // Check authentication status and redirect if not authenticated
  React.useEffect(() => {
    if (!loading && !isAuthenticated) {
      navigate('/');  // Redirect to landing page instead of login
    }
  }, [loading, isAuthenticated, navigate]);

  // Build navigation based on user permissions
  const navigation = React.useMemo(() => {
    // Debug logging
    console.log('Navigation Debug:', {
      user,
      isStoreManager: isStoreManager(),
      isTenantAdmin: isTenantAdmin(),
      isSuperAdmin: isSuperAdmin(),
      stores: user?.stores,
      store_role: user?.store_role
    });
    
    // For store managers only (not tenant admin or super admin), show specific menu items
    if (isStoreManager() && !isTenantAdmin() && !isSuperAdmin()) {
      return [
        { name: 'Dashboard', href: '/dashboard', icon: Home, permission: 'all' },
        { name: 'POS', href: '/dashboard/pos', icon: ShoppingCart, permission: 'store' },
        { name: 'Organization', href: '/dashboard/tenants', icon: Building2, permission: 'store_manager' },
        { name: 'Inventory', href: '/dashboard/inventory', icon: Package, permission: 'store' },
        { name: 'Accessories', href: '/dashboard/accessories', icon: Package, permission: 'store' },
        { name: 'Orders', href: '/dashboard/orders', icon: ShoppingCart, permission: 'store' },
        { name: 'Customers', href: '/dashboard/customers', icon: Users, permission: 'store' },
        { name: 'Purchase Orders', href: '/dashboard/purchase-orders', icon: FileText, permission: 'store' },
        { name: 'Promotions', href: '/dashboard/promotions', icon: Tag, permission: 'store' },
        { name: 'Recommendations', href: '/dashboard/recommendations', icon: Sparkles, permission: 'store' },
      ];
    }

    // For admins (tenant admin and super admin), show all applicable items
    const items = [
      { name: 'Dashboard', href: '/dashboard', icon: Home, permission: 'all' },
      { name: 'POS', href: '/dashboard/pos', icon: ShoppingCart, permission: 'store' },
      { name: isTenantAdmin() && !isSuperAdmin() ? 'Organization' : 'Tenants', href: '/dashboard/tenants', icon: Building2, permission: 'admin' },
      { name: 'Products', href: '/dashboard/products', icon: Leaf, permission: 'store' },
      { name: 'Inventory', href: '/dashboard/inventory', icon: Package, permission: 'store' },
      { name: 'Accessories', href: '/dashboard/accessories', icon: Package, permission: 'store' },
      { name: 'Orders', href: '/dashboard/orders', icon: ShoppingCart, permission: 'store' },
      { name: 'Customers', href: '/dashboard/customers', icon: Users, permission: 'store' },
      { name: 'Purchase Orders', href: '/dashboard/purchase-orders', icon: FileText, permission: 'store' },
      { name: 'Promotions', href: '/dashboard/promotions', icon: Tag, permission: 'store' },
      { name: 'Recommendations', href: '/dashboard/recommendations', icon: Sparkles, permission: 'store' },
      { name: 'Provincial Catalog', href: '/dashboard/provincial-catalog', icon: Upload, permission: 'super_admin' },
    ];

    // Filter based on permissions
    return items.filter(item => {
      if (item.permission === 'all') return true;
      if (item.permission === 'super_admin') return isSuperAdmin();
      if (item.permission === 'admin') return isSuperAdmin() || isTenantAdmin();
      if (item.permission === 'tenant') return isSuperAdmin() || isTenantAdmin();
      if (item.permission === 'store') return isSuperAdmin() || isTenantAdmin() || isStoreManager();
      if (item.permission === 'store_manager') return isStoreManager();
      return true;
    });
  }, [isSuperAdmin, isTenantAdmin, isStoreManager]);

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  // If not authenticated after loading, the useEffect will redirect
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-green-900 transform ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center justify-between px-4 bg-green-800">
            <div className="flex items-center">
              <Leaf className="h-8 w-8 text-green-400" />
              <span className="ml-2 text-xl font-bold text-white">Pot Palace</span>
            </div>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden text-white hover:text-green-200"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-2 py-4 overflow-y-auto">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                onClick={() => window.innerWidth < 1024 && setSidebarOpen(false)}
                className="group flex items-center px-2 py-2 text-sm font-medium rounded-md text-green-100 hover:bg-green-800 hover:text-white transition-colors"
              >
                <item.icon
                  className="mr-3 h-5 w-5 flex-shrink-0 text-green-400 group-hover:text-green-300"
                  aria-hidden="true"
                />
                {item.name}
              </Link>
            ))}
          </nav>

          {/* User section */}
          <div className="flex flex-shrink-0 border-t border-green-800 p-4">
            <div className="flex items-center">
              <div>
                <img
                  className="inline-block h-9 w-9 rounded-full"
                  src={`https://ui-avatars.com/api/?name=${user?.first_name || 'Not'}+${user?.last_name || 'Logged'}&background=10b981&color=fff`}
                  alt="User Avatar"
                />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-white">
                  {user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : 'Not Logged In'}
                </p>
                <p className="text-xs font-medium text-green-200">{user?.email || 'No user session'}</p>
                <p className="text-xs font-medium text-green-300 capitalize">
                  {(() => {
                    if (!user) return 'No Active Session';
                    if (isSuperAdmin()) return 'Super Admin';
                    if (isTenantAdmin()) return 'Tenant Admin';
                    if (isStoreManager()) return 'Store Manager';
                    return user?.role?.replace('_', ' ') || 'User';
                  })()}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Top bar */}
        <header className="bg-white shadow-sm">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden text-gray-500 hover:text-gray-700"
            >
              <Menu className="h-6 w-6" />
            </button>
            
            <div className="flex-1 flex items-center">
              <h2 className="text-lg font-semibold text-gray-900">WeedGo Admin Dashboard</h2>

              {/* Store Selection and Breadcrumb */}
              {(isSuperAdmin() || isTenantAdmin()) && (
                <div className="ml-8 flex items-center">
                  <button
                    onClick={() => setShowStoreModal(true)}
                    className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Select Store"
                  >
                    <Store className="h-5 w-5" />
                  </button>

                  {currentStore && (
                    <div className="ml-2 flex items-center text-sm text-gray-600">
                      {/* Show tenant only for super admins */}
                      {isSuperAdmin() && selectedTenant && (
                        <>
                          <span className="font-medium">{selectedTenant.name}</span>
                          <ChevronRight className="h-4 w-4 mx-1" />
                        </>
                      )}
                      <span className="font-medium">{currentStore.name}</span>
                      <button
                        onClick={() => setShowStoreModal(true)}
                        className="ml-2 text-blue-600 hover:text-blue-700 text-xs underline"
                      >
                        Change
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Fixed store display for store managers and staff */}
              {isStoreManager() && !isTenantAdmin() && !isSuperAdmin() && (
                <div className="ml-8 flex items-center">
                  <div className="p-2 text-gray-400">
                    <Store className="h-5 w-5" />
                  </div>
                  {currentStore ? (
                    <div className="ml-2 flex items-center text-sm text-gray-600">
                      <span className="font-medium">{currentStore.name}</span>
                    </div>
                  ) : (
                    <div className="ml-2 flex items-center text-sm text-gray-500">
                      <span className="italic">Loading store...</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex items-center space-x-4">
              <button className="text-gray-500 hover:text-gray-700">
                <Settings className="h-5 w-5" />
              </button>
              <button 
                onClick={async () => {
                  await logout();
                  navigate('/login');
                }}
                className="text-gray-500 hover:text-gray-700"
                title="Logout"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className={`flex-1 overflow-y-auto ${location.pathname === '/dashboard/pos' ? '' : 'p-4 sm:p-6 lg:p-8'}`}>
          <Outlet />
        </main>
      </div>

      {/* Store Selection Modal */}
      {(isSuperAdmin() || isTenantAdmin()) && (
        <StoreSelectionModal
          isOpen={showStoreModal}
          onSelect={async (tenantId, storeId, storeName, tenantName) => {
            setSelectedTenant({ id: tenantId, name: tenantName || 'Unknown Tenant' });
            // Pass the store name along with the ID to ensure breadcrumb displays immediately
            await selectStore(storeId, storeName);
            setShowStoreModal(false);
          }}
          onClose={() => setShowStoreModal(false)}
        />
      )}
    </div>
  );
}

// Create router with future flags for v7 compatibility
const router = createBrowserRouter([
  {
    path: '/',
    element: <Landing />
  },
  {
    path: '/login',
    element: <Login />
  },
  {
    path: '/signup',
    element: <TenantSignup />
  },
  {
    path: '/user-registration',
    element: <UserRegistration />
  },
  {
    path: '/verification',
    element: <Verification />
  },
  {
    path: '/signup-success',
    element: <SignupSuccess />
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'pos', element: <POS /> },
      { 
        path: 'tenants', 
        element: <TenantManagement />
      },
      { path: 'tenants/:tenantCode/settings', element: <TenantSettings /> },
      { path: 'tenants/:tenantCode/payment-settings', element: <TenantPaymentSettings /> },
      { path: 'tenants/:tenantCode/stores', element: <StoreManagement /> },
      { path: 'stores/:storeCode/settings', element: <StoreSettings /> },
      { path: 'stores/:storeCode/hours', element: <StoreHoursManagement /> },
      { path: 'products', element: <Products /> },
      { path: 'inventory', element: <Inventory /> },
      { path: 'accessories', element: <Accessories /> },
      { path: 'orders', element: <Orders /> },
      { path: 'customers', element: <Customers /> },
      { path: 'purchase-orders', element: <PurchaseOrders /> },
      { path: 'promotions', element: <Promotions /> },
      { path: 'recommendations', element: <Recommendations /> },
      { 
        path: 'provincial-catalog', 
        element: (
          <ProtectedRoute requiredPermissions={['system:super_admin']}>
            <ProvincialCatalogVirtual />
          </ProtectedRoute>
        )
      },
    ],
  },
], {
  future: {
    v7_startTransition: true,
    v7_relativeSplatPath: true
  }
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <StoreProvider>
          <RouterProvider router={router} />
          <ReactQueryDevtools initialIsOpen={false} />
        </StoreProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;