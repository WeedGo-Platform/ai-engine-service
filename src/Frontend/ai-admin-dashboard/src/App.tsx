import React from 'react';
import { createBrowserRouter, RouterProvider, Link, Outlet, useLocation, Navigate, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import {
  Home, Package, ShoppingCart, Users, FileText, Leaf, Menu, X, LogOut, Settings,
  Building2, Store, Tag, Sparkles, Upload, ChevronRight, PanelLeftClose, PanelLeft, Database, Truck, AppWindow, MessageSquare, Brain
} from 'lucide-react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { StoreProvider, useStoreContext } from './contexts/StoreContext';
import ProtectedRoute from './components/ProtectedRoute';
import StoreSelectionModal from './components/StoreSelectionModal';
import ChatWidget from './components/ChatWidget';

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
import DatabaseManagement from './pages/DatabaseManagement';
import DeliveryManagement from './pages/DeliveryManagement';
import AIManagement from './pages/AIManagement';
import VoiceAPITest from './pages/VoiceAPITest';
import Apps from './pages/Apps';
import Communications from './pages/Communications';

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
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
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

  // Authentication is already handled by ProtectedRoute wrapper

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
    let items = [];
    if (isStoreManager() && !isTenantAdmin() && !isSuperAdmin()) {
      items = [
        { name: 'Dashboard', href: '/dashboard', icon: Home, permission: 'all' },
        { name: 'Apps', href: '/dashboard/apps', icon: AppWindow, permission: 'store' },
        { name: 'Organization', href: '/dashboard/tenants', icon: Building2, permission: 'store_manager' },
        { name: 'Inventory', href: '/dashboard/inventory', icon: Package, permission: 'store' },
        { name: 'Accessories', href: '/dashboard/accessories', icon: Package, permission: 'store' },
        { name: 'Orders', href: '/dashboard/orders', icon: ShoppingCart, permission: 'store' },
        { name: 'Customers', href: '/dashboard/customers', icon: Users, permission: 'store' },
        { name: 'Purchase Orders', href: '/dashboard/purchase-orders', icon: FileText, permission: 'store' },
        { name: 'Promotions', href: '/dashboard/promotions', icon: Tag, permission: 'store' },
        { name: 'Recommendations', href: '/dashboard/recommendations', icon: Sparkles, permission: 'store' },
        { name: 'Communications', href: '/dashboard/communications', icon: MessageSquare, permission: 'store' },
      ];
    } else {
      // For admins (tenant admin and super admin), show all applicable items
      items = [
        { name: 'Dashboard', href: '/dashboard', icon: Home, permission: 'all' },
        { name: 'Apps', href: '/dashboard/apps', icon: AppWindow, permission: 'store' },
        { name: isTenantAdmin() && !isSuperAdmin() ? 'Organization' : 'Tenants', href: '/dashboard/tenants', icon: Building2, permission: 'admin' },
        { name: 'Products', href: '/dashboard/products', icon: Leaf, permission: 'store' },
        { name: 'Inventory', href: '/dashboard/inventory', icon: Package, permission: 'store' },
        { name: 'Accessories', href: '/dashboard/accessories', icon: Package, permission: 'store' },
        { name: 'Orders', href: '/dashboard/orders', icon: ShoppingCart, permission: 'store' },
        { name: 'Customers', href: '/dashboard/customers', icon: Users, permission: 'store' },
        { name: 'Purchase Orders', href: '/dashboard/purchase-orders', icon: FileText, permission: 'store' },
        { name: 'Promotions', href: '/dashboard/promotions', icon: Tag, permission: 'store' },
        { name: 'Recommendations', href: '/dashboard/recommendations', icon: Sparkles, permission: 'store' },
        { name: 'Communications', href: '/dashboard/communications', icon: MessageSquare, permission: 'store' },
        { name: 'Deliveries', href: '/dashboard/deliveries', icon: Truck, permission: 'store' },
        { name: 'AI Configuration', href: '/dashboard/ai', icon: Settings, permission: 'all' },
        { name: 'AGI Management', href: '/dashboard/agi', icon: Brain, permission: 'all' },
        { name: 'Provincial Catalog', href: '/dashboard/provincial-catalog', icon: Upload, permission: 'super_admin' },
        { name: 'Database', href: '/dashboard/database', icon: Database, permission: 'super_admin' },
      ];
    }

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

  // Loading state is now handled by ProtectedRoute
  // Authentication check is also handled by ProtectedRoute

  // Double-check authentication in Layout as a safety measure
  if (!isAuthenticated) {
    return null; // ProtectedRoute should handle this, but adding as safety
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
      <div className={`fixed inset-y-0 left-0 z-50 ${sidebarCollapsed ? 'w-20' : 'w-64'} bg-white border-r border-gray-200 transform ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } transition-all duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center justify-between px-4 border-b border-gray-200">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <Leaf className="h-5 w-5 text-white" />
              </div>
              {!sidebarCollapsed && (
                <span className="ml-3 text-xl font-semibold text-gray-900 transition-opacity duration-300">Pot Palace</span>
              )}
            </div>
            <div className="flex items-center">
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="hidden lg:block text-gray-400 hover:text-gray-600 p-1.5 hover:bg-gray-50 rounded-lg transition-all"
              >
                {sidebarCollapsed ? <PanelLeft className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
              </button>
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden text-gray-500 hover:text-gray-700 ml-2"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href ||
                              (item.href !== '/dashboard' && location.pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => window.innerWidth < 1024 && setSidebarOpen(false)}
                  title={sidebarCollapsed ? item.name : undefined}
                  className={`group flex items-center ${sidebarCollapsed ? 'justify-center px-2' : 'px-3'} py-2.5 text-sm font-medium rounded-lg transition-all ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <item.icon
                    className={`${sidebarCollapsed ? '' : 'mr-3'} h-5 w-5 flex-shrink-0 ${
                      isActive ? 'text-primary-600' : 'text-gray-400 group-hover:text-gray-500'
                    }`}
                    aria-hidden="true"
                  />
                  {!sidebarCollapsed && (
                    <span className="transition-opacity duration-300">{item.name}</span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* User section */}
          <div className="flex flex-shrink-0 border-t border-gray-200 p-4">
            <div className={`flex items-center ${sidebarCollapsed ? 'justify-center' : ''} w-full`}>
              <div>
                <img
                  className={`inline-block ${sidebarCollapsed ? 'h-8 w-8' : 'h-10 w-10'} rounded-full`}
                  src={`https://ui-avatars.com/api/?name=${user?.first_name || 'Not'}+${user?.last_name || 'Logged'}&background=71717a&color=fff`}
                  alt="User Avatar"
                  title={sidebarCollapsed ? `${user?.first_name} ${user?.last_name}` : undefined}
                />
              </div>
              {!sidebarCollapsed && (
                <div className="ml-3 flex-1 transition-opacity duration-300">
                  <p className="text-sm font-medium text-gray-900">
                    {user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : 'Not Logged In'}
                  </p>
                  <p className="text-xs text-gray-500">{user?.email || 'No user session'}</p>
                  <p className="text-xs font-medium text-primary-600 capitalize">
                    {(() => {
                      if (!user) return 'No Active Session';
                      if (isSuperAdmin()) return 'Super Admin';
                      if (isTenantAdmin()) return 'Tenant Admin';
                      if (isStoreManager()) return 'Store Manager';
                      return user?.role?.replace('_', ' ') || 'User';
                    })()}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Top bar */}
        <header className="bg-white border-b border-gray-200">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden text-gray-500 hover:text-gray-700"
            >
              <Menu className="h-6 w-6" />
            </button>
            
            <div className="flex-1 flex items-center">
              <h2 className="text-lg font-medium text-gray-900">Admin Dashboard</h2>

              {/* Store Selection and Breadcrumb */}
              {(isSuperAdmin() || isTenantAdmin()) && (
                <div className="ml-8 flex items-center">
                  <button
                    onClick={() => setShowStoreModal(true)}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-all"
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
                        className="ml-2 text-accent-600 hover:text-accent-700 text-xs font-medium"
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

            <div className="flex items-center space-x-2">
              <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-all">
                <Settings className="h-5 w-5" />
              </button>
              <button
                onClick={async () => {
                  await logout();
                  navigate('/login');
                }}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-all"
                title="Logout"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className={`flex-1 overflow-y-auto ${location.pathname === '/dashboard/apps' ? '' : 'p-6 sm:p-6 lg:p-8'}`}>
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

      {/* Chat Widget with Voice Support */}
      <ChatWidget />
    </div>
  );
}

// Create router with future flags for v7 compatibility
const router = createBrowserRouter([
  {
    path: '/',
    element: <Landing />  // Landing page remains unprotected
  },
  {
    path: '/login',
    element: <Login />  // Login page must be accessible without auth
  },
  {
    path: '/signup',
    element: <TenantSignup />  // Signup page must be accessible without auth
  },
  {
    path: '/user-registration',
    element: <UserRegistration />  // Registration page must be accessible without auth
  },
  {
    path: '/verification',
    element: <Verification />  // Verification page must be accessible without auth
  },
  {
    path: '/signup-success',
    element: <SignupSuccess />  // Success page must be accessible without auth
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
      { path: 'apps', element: <Apps /> },
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
      { path: 'communications', element: <Communications /> },
      { path: 'deliveries', element: <DeliveryManagement /> },
      { path: 'ai', element: <AIManagement /> },
      {
        path: 'agi',
        element: (() => {
          const AGIDashboard = React.lazy(() => import('./pages/agi/AGIDashboard'));
          return (
            <React.Suspense fallback={<div className="flex items-center justify-center h-screen">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>}>
              <AGIDashboard />
            </React.Suspense>
          );
        })()
      },
      { path: 'voice-test', element: <VoiceAPITest /> },
      {
        path: 'provincial-catalog',
        element: (
          <ProtectedRoute requiredPermissions={['system:super_admin']}>
            <ProvincialCatalogVirtual />
          </ProtectedRoute>
        )
      },
      {
        path: 'database',
        element: (
          <ProtectedRoute requiredPermissions={['system:super_admin']}>
            <DatabaseManagement />
          </ProtectedRoute>
        )
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />  // Catch-all route redirects to landing
  }
], {
  future: {
    v7_relativeSplatPath: true,
    v7_startTransition: true
  }
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <StoreProvider>
          <RouterProvider router={router} />
          <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              success: {
                style: {
                  background: '#10b981',
                  color: 'white',
                  fontWeight: '500'
                },
                iconTheme: {
                  primary: 'white',
                  secondary: '#10b981'
                }
              },
              error: {
                style: {
                  background: '#ef4444',
                  color: 'white',
                  fontWeight: '500'
                },
                iconTheme: {
                  primary: 'white',
                  secondary: '#ef4444'
                }
              }
            }}
          />
        </StoreProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;