import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { 
  Home, Package, ShoppingCart, Users, FileText, 
  TrendingUp, Leaf, Menu, X, LogOut, Settings 
} from 'lucide-react';

// Import pages
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Inventory from './pages/Inventory';
import Orders from './pages/Orders';
import Customers from './pages/Customers';
import PurchaseOrders from './pages/PurchaseOrders';

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

function App() {
  const [sidebarOpen, setSidebarOpen] = React.useState(true);

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Products', href: '/products', icon: Leaf },
    { name: 'Inventory', href: '/inventory', icon: Package },
    { name: 'Orders', href: '/orders', icon: ShoppingCart },
    { name: 'Customers', href: '/customers', icon: Users },
    { name: 'Purchase Orders', href: '/purchase-orders', icon: FileText },
  ];

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
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
              <nav className="flex-1 space-y-1 px-2 py-4">
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
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
                      src="https://ui-avatars.com/api/?name=Admin+User&background=10b981&color=fff"
                      alt="Admin"
                    />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-white">Admin User</p>
                    <p className="text-xs font-medium text-green-200">admin@potpalace.ca</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main content */}
          <div className="flex flex-1 flex-col lg:pl-64">
            {/* Top bar */}
            <header className="bg-white shadow-sm">
              <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="lg:hidden text-gray-500 hover:text-gray-700"
                >
                  <Menu className="h-6 w-6" />
                </button>
                
                <div className="flex items-center">
                  <h2 className="text-lg font-semibold text-gray-900">WeedGo Admin Dashboard</h2>
                </div>

                <div className="flex items-center space-x-4">
                  <button className="text-gray-500 hover:text-gray-700">
                    <Settings className="h-5 w-5" />
                  </button>
                  <button className="text-gray-500 hover:text-gray-700">
                    <LogOut className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </header>

            {/* Page content */}
            <main className="flex-1 p-4 sm:p-6 lg:p-8">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/products" element={<Products />} />
                <Route path="/inventory" element={<Inventory />} />
                <Route path="/orders" element={<Orders />} />
                <Route path="/customers" element={<Customers />} />
                <Route path="/purchase-orders" element={<PurchaseOrders />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>
        </div>
      </Router>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;