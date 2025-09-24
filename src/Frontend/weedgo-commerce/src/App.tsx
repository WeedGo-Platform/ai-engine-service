import React, { Suspense, lazy, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { Toaster } from 'react-hot-toast';
import { store } from '@store/index';
import { restoreSession } from '@features/auth/authSlice';
import { restoreCart } from '@features/cart/cartSlice';
import { TemplateProvider } from '@templates/TemplateProvider';
import { TenantProvider } from '@contexts/TenantContext';
import { StoreProvider } from '@contexts/StoreContext';
import { AgeVerificationProvider } from '@contexts/AgeVerificationContext';
import LoadingScreen from '@components/common/LoadingScreen';
import MainLayout from '@layouts/MainLayout';
import ErrorBoundary from '@components/ErrorBoundary';

// Lazy load pages
const Home = lazy(() => import('@pages/Home'));
const ProductsPage = lazy(() => import('@pages/ProductsPage'));
const ProductDetail = lazy(() => import('@pages/ProductDetail'));
const ProductDetailSEO = lazy(() => import('@pages/ProductDetailSEO'));
const Cart = lazy(() => import('@pages/Cart'));
const Checkout = lazy(() => import('@pages/Checkout'));
const Login = lazy(() => import('@pages/Login'));
const Register = lazy(() => import('@pages/Register'));
const Profile = lazy(() => import('@pages/Profile'));
const OrderTracking = lazy(() => import('@pages/OrderTracking'));
const OrderHistory = lazy(() => import('@pages/OrderHistory'));
const AgeVerification = lazy(() => import('@pages/AgeVerification'));

function App() {
  useEffect(() => {
    // Restore user session and cart on app load
    store.dispatch(restoreSession());
    store.dispatch(restoreCart());

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <TemplateProvider>
          <TenantProvider>
            <StoreProvider>
              <AgeVerificationProvider>
                <Router>
              <Suspense fallback={<LoadingScreen />}>
                <MainLayout>
                  <Routes>
                {/* Public Routes */}
                <Route path="/" element={<Home />} />
                <Route path="/products" element={<ProductsPage />} />
                {/* SEO-friendly product routes */}
                <Route path="/dispensary-near-me/:city/:slug" element={<ProductDetailSEO />} />
                <Route path="/cannabis/:category/:slug" element={<ProductDetailSEO />} />
                <Route path="/product/:identifier" element={<ProductDetailSEO />} />

                {/* Legacy SKU route for backward compatibility */}
                <Route path="/products/:sku" element={<ProductDetail />} />
                <Route path="/cart" element={<Cart />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/age-verification" element={<AgeVerification />} />

                {/* Protected Routes */}
                <Route path="/checkout" element={<Checkout />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/orders" element={<OrderHistory />} />
                <Route path="/track/:orderId" element={<OrderTracking />} />

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </MainLayout>
          </Suspense>

          {/* Global Toast Notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                iconTheme: {
                  primary: '#4CAF50',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#F44336',
                  secondary: '#fff',
                },
              },
            }}
          />
        </Router>
              </AgeVerificationProvider>
            </StoreProvider>
          </TenantProvider>
        </TemplateProvider>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;
