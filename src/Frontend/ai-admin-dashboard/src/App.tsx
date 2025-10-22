import React from 'react';
import { createBrowserRouter, RouterProvider, Link, Outlet, useLocation, Navigate, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import {
  Home, Package, ShoppingCart, Users, FileText, Leaf, Menu, X, LogOut, Settings,
  Building2, Store, Tag, Sparkles, Upload, ChevronRight, PanelLeftClose, PanelLeft, Database, Truck, AppWindow, MessageSquare, ScrollText, Moon, Sun, CreditCard
} from 'lucide-react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { StoreProvider, useStoreContext } from './contexts/StoreContext';
import { PaymentProvider } from './contexts/PaymentContext';
import { useTheme } from './hooks/useTheme';
import ProtectedRoute from './components/ProtectedRoute';
import StoreSelectionModal from './components/StoreSelectionModal';
import ChatWidget from './components/ChatWidget';
import ChangePasswordModal from './components/ChangePasswordModal';
import PaymentErrorBoundary from './components/PaymentErrorBoundary';
import LanguageSelector from './components/LanguageSelector';
import './i18n/config'; // Initialize i18n
import { useTranslation } from 'react-i18next';

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
import TenantReview from './pages/TenantReview';
import StoreManagement from './pages/StoreManagement';
import StoreSettings from './pages/StoreSettings';
import StoreHoursManagement from './pages/StoreHoursManagement';
import Promotions from './pages/Promotions';
import Recommendations from './pages/Recommendations';
import POS from './pages/POS';
import ProvincialCatalogVirtual from './pages/ProvincialCatalogVirtual';
import ProvincialCatalogImproved from './pages/ProvincialCatalogImproved';
import DatabaseManagement from './pages/DatabaseManagement';
import DeliveryManagement from './pages/DeliveryManagement';
import AIManagement from './pages/AIManagement';
import VoiceAPITest from './pages/VoiceAPITest';
import Apps from './pages/Apps';
import Communications from './pages/Communications';
import LogViewer from './pages/LogViewer';
import Payments from './pages/Payments';

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
  const { t } = useTranslation('common');
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const [showStoreModal, setShowStoreModal] = React.useState(false);
  const [showPasswordModal, setShowPasswordModal] = React.useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, loading, isSuperAdmin, isTenantAdmin, isStoreManager } = useAuth();
  const { currentStore, selectStore } = useStoreContext();
  const { isDark, toggleTheme } = useTheme();
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
    // Debug logging (development only)
    if (process.env.NODE_ENV === 'development') {
      console.log('Navigation Debug:', {
        user,
        isStoreManager: isStoreManager(),
        isTenantAdmin: isTenantAdmin(),
        isSuperAdmin: isSuperAdmin(),
        stores: user?.stores,
        store_role: user?.store_role
      });
    }
    
    // For store managers only (not tenant admin or super admin), show specific menu items
    let items = [];
    if (isStoreManager() && !isTenantAdmin() && !isSuperAdmin()) {
      items = [
        { name: t('navigation.dashboard'), href: '/dashboard', icon: Home, permission: 'all' },
        { name: t('navigation.apps'), href: '/dashboard/apps', icon: AppWindow, permission: 'store' },
        { name: t('navigation.organization'), href: '/dashboard/tenants', icon: Building2, permission: 'store_manager' },
        { name: t('navigation.inventory'), href: '/dashboard/inventory', icon: Package, permission: 'store' },
        { name: t('navigation.accessories'), href: '/dashboard/accessories', icon: Package, permission: 'store' },
        { name: t('navigation.orders'), href: '/dashboard/orders', icon: ShoppingCart, permission: 'store' },
        { name: t('navigation.payments'), href: '/dashboard/payments', icon: CreditCard, permission: 'store' },
        { name: t('navigation.customers'), href: '/dashboard/customers', icon: Users, permission: 'store' },
        { name: t('navigation.purchaseOrders'), href: '/dashboard/purchase-orders', icon: FileText, permission: 'store' },
        { name: t('navigation.promotions'), href: '/dashboard/promotions', icon: Tag, permission: 'store' },
        { name: t('navigation.recommendations'), href: '/dashboard/recommendations', icon: Sparkles, permission: 'store' },
        { name: t('navigation.communications'), href: '/dashboard/communications', icon: MessageSquare, permission: 'store' },
      ];
    } else {
      // For admins (tenant admin and super admin), show all applicable items
      items = [
        { name: t('navigation.dashboard'), href: '/dashboard', icon: Home, permission: 'all' },
        { name: t('navigation.apps'), href: '/dashboard/apps', icon: AppWindow, permission: 'store' },
        { name: isTenantAdmin() && !isSuperAdmin() ? t('navigation.organization') : t('navigation.tenants'), href: '/dashboard/tenants', icon: Building2, permission: 'admin' },
        { name: t('navigation.products'), href: '/dashboard/products', icon: Leaf, permission: 'store' },
        { name: t('navigation.inventory'), href: '/dashboard/inventory', icon: Package, permission: 'store' },
        { name: t('navigation.accessories'), href: '/dashboard/accessories', icon: Package, permission: 'store' },
        { name: t('navigation.orders'), href: '/dashboard/orders', icon: ShoppingCart, permission: 'store' },
        { name: t('navigation.payments'), href: '/dashboard/payments', icon: CreditCard, permission: 'store' },
        { name: t('navigation.customers'), href: '/dashboard/customers', icon: Users, permission: 'store' },
        { name: t('navigation.purchaseOrders'), href: '/dashboard/purchase-orders', icon: FileText, permission: 'store' },
        { name: t('navigation.promotions'), href: '/dashboard/promotions', icon: Tag, permission: 'store' },
        { name: t('navigation.recommendations'), href: '/dashboard/recommendations', icon: Sparkles, permission: 'store' },
        { name: t('navigation.communications'), href: '/dashboard/communications', icon: MessageSquare, permission: 'store' },
        { name: t('navigation.deliveries'), href: '/dashboard/deliveries', icon: Truck, permission: 'store' },
        { name: t('navigation.aiConfiguration'), href: '/dashboard/ai', icon: Settings, permission: 'all' },
        { name: t('navigation.provincialCatalog'), href: '/dashboard/provincial-catalog', icon: Upload, permission: 'super_admin' },
        { name: t('navigation.database'), href: '/dashboard/database', icon: Database, permission: 'super_admin' },
        { name: t('navigation.systemLogs'), href: '/dashboard/logs', icon: ScrollText, permission: 'super_admin' },
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
  }, [isSuperAdmin, isTenantAdmin, isStoreManager, t]);

  // Loading state is now handled by ProtectedRoute
  // Authentication check is also handled by ProtectedRoute

  // Double-check authentication in Layout as a safety measure
  if (!isAuthenticated) {
    return null; // ProtectedRoute should handle this, but adding as safety
  }

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden transition-colors duration-200">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 ${sidebarCollapsed ? 'w-20' : 'w-64'} bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } transition-all duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-primary-600 dark:bg-primary-500 rounded-lg flex items-center justify-center flex-shrink-0">
                <Leaf className="h-5 w-5 text-white" />
              </div>
              {!sidebarCollapsed && (
                <span className="ml-3 text-xl font-semibold text-gray-900 dark:text-white transition-opacity duration-300">Pot Palace</span>
              )}
            </div>
            <div className="flex items-center">
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="hidden lg:block text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1.5 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-all"
              >
                {sidebarCollapsed ? <PanelLeft className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
              </button>
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 ml-2"
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
                      ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <item.icon
                    className={`${sidebarCollapsed ? '' : 'mr-3'} h-5 w-5 flex-shrink-0 ${
                      isActive ? 'text-primary-600 dark:text-primary-400' : 'text-gray-400 dark:text-gray-500 group-hover:text-gray-500 dark:group-hover:text-gray-400'
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
          <div className="flex flex-shrink-0 border-t border-gray-200 dark:border-gray-700 p-4">
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
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : 'Not Logged In'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{user?.email || 'No user session'}</p>
                  <p className="text-xs font-medium text-primary-600 dark:text-primary-400 capitalize">
                    {(() => {
                      if (!user) return 'No Active Session';
                      if (isSuperAdmin()) return t('roles.superAdmin');
                      if (isTenantAdmin()) return t('roles.tenantAdmin');
                      if (isStoreManager()) return t('roles.storeManager');
                      return t('roles.user');
                    })()}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col bg-gray-50 dark:bg-gray-900">
        {/* Top bar */}
        <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            >
              <Menu className="h-6 w-6" />
            </button>
            
            <div className="flex-1 flex items-center">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">Admin Dashboard</h2>

              {/* Store Selection and Breadcrumb */}
              {(isSuperAdmin() || isTenantAdmin()) && (
                <div className="ml-8 flex items-center">
                  <button
                    onClick={() => setShowStoreModal(true)}
                    className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-all"
                    title="Select Store"
                  >
                    <Store className="h-5 w-5" />
                  </button>

                  {currentStore && (
                    <div className="ml-2 flex items-center text-sm text-gray-600 dark:text-gray-300">
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
                        className="ml-2 text-accent-600 dark:text-accent-400 hover:text-accent-700 dark:hover:text-accent-300 text-xs font-medium"
                      >
                        {t('buttons.change')}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Fixed store display for store managers and staff */}
              {isStoreManager() && !isTenantAdmin() && !isSuperAdmin() && (
                <div className="ml-8 flex items-center">
                  <div className="p-2 text-gray-400 dark:text-gray-500">
                    <Store className="h-5 w-5" />
                  </div>
                  {currentStore ? (
                    <div className="ml-2 flex items-center text-sm text-gray-600 dark:text-gray-300">
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
              <LanguageSelector />
              <button
                onClick={toggleTheme}
                className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-all"
                title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              >
                {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>
              <button
                onClick={() => setShowPasswordModal(true)}
                className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-all"
                title="Change Password"
              >
                <Settings className="h-5 w-5" />
              </button>
              <button
                onClick={async () => {
                  await logout();
                  navigate('/login');
                }}
                className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-all"
                title="Logout"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className={`flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900 ${location.pathname === '/dashboard/apps' ? 'pr-4' : 'p-6 sm:p-6 lg:p-8 pr-8'}`}>
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

      {/* Password Change Modal */}
      <ChangePasswordModal
        isOpen={showPasswordModal}
        onClose={() => setShowPasswordModal(false)}
        onSuccess={async () => {
          // Already handled in modal - user will be logged out
        }}
      />
    </div>
  );
}

// Create router (React Router v7)
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
      { path: 'tenants/review', element: <TenantReview /> },
      { path: 'tenants/:tenantCode/settings', element: <TenantSettings /> },
      {
        path: 'tenants/:tenantCode/payment-settings',
        element: (
          <PaymentErrorBoundary showDetails={process.env.NODE_ENV === 'development'}>
            <PaymentProvider>
              <TenantPaymentSettings />
            </PaymentProvider>
          </PaymentErrorBoundary>
        )
      },
      { path: 'tenants/:tenantCode/stores', element: <StoreManagement /> },
      { path: 'stores/:storeCode/settings', element: <StoreSettings /> },
      { path: 'stores/:storeCode/hours', element: <StoreHoursManagement /> },
      { path: 'products', element: <Products /> },
      { path: 'inventory', element: <Inventory /> },
      { path: 'accessories', element: <Accessories /> },
      { path: 'orders', element: <Orders /> },
      {
        path: 'payments',
        element: (
          <PaymentErrorBoundary showDetails={process.env.NODE_ENV === 'development'}>
            <PaymentProvider>
              <Payments />
            </PaymentProvider>
          </PaymentErrorBoundary>
        )
      },
      { path: 'customers', element: <Customers /> },
      { path: 'purchase-orders', element: <PurchaseOrders /> },
      { path: 'promotions', element: <Promotions /> },
      { path: 'recommendations', element: <Recommendations /> },
      { path: 'communications', element: <Communications /> },
      { path: 'deliveries', element: <DeliveryManagement /> },
      { path: 'ai', element: <AIManagement /> },
      { path: 'voice-test', element: <VoiceAPITest /> },
      {
        path: 'provincial-catalog',
        element: (
          <ProtectedRoute requiredPermissions={['system:super_admin']}>
            <ProvincialCatalogImproved />
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
      {
        path: 'logs',
        element: (
          <ProtectedRoute requiredPermissions={['system:super_admin']}>
            <LogViewer />
          </ProtectedRoute>
        )
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />  // Catch-all route redirects to landing
  }
]);

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