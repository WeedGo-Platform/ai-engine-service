import React, { useState } from 'react';
import { getApiUrl } from '../../config/app.config';
import { ChevronLeft, Plus, Minus, Trash2, ShoppingCart } from 'lucide-react';
import { useKiosk } from '../../contexts/KioskContext';
import ProductRecommendations from './ProductRecommendations';
import ProductDetailsModal from './ProductDetailsModal';
import { formatCurrency } from '../../utils/currency';

interface CartProps {
  onBack: () => void;
  onCheckout: () => void;
  currentStore: any;
}

export default function Cart({ onBack, onCheckout, currentStore }: CartProps) {
  const {
    cart,
    updateCartItem,
    removeFromCart,
    clearCart,
    cartTotal,
    cartItemCount,
    sessionId
  } = useKiosk();

  const [selectedProduct, setSelectedProduct] = useState<any>(null);

  const taxRate = 0.13; // Ontario HST
  const subtotal = cartTotal;
  const tax = subtotal * taxRate;
  const total = subtotal + tax;

  if (cart.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 p-8">
        <ShoppingCart className="w-24 h-24 text-gray-300 dark:text-gray-600 mb-4" />
        <h2 className="text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-2">Your Cart is Empty</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-6">Add some products to get started</p>
        <button
          onClick={onBack}
          className="px-6 py-3 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 transition-colors"
        >
          Continue Shopping
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-gray-900 dark:text-white"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Your Cart</h1>
            <span className="text-sm text-gray-500 dark:text-gray-400">({cartItemCount} items)</span>
          </div>
          <button
            onClick={clearCart}
            className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium"
          >
            Clear Cart
          </button>
        </div>
      </div>

      {/* Cart Items */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
            {cart.map((item) => (
              <div
                key={item.id}
                className="flex items-center gap-4 p-4 border-b border-gray-200 dark:border-gray-700 last:border-b-0"
              >
                {/* Product Image */}
                <div className="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden flex-shrink-0">
                  <img
                    src={item.image || 'api/placeholder/80/80'}
                    alt={item.name}
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* Product Info */}
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-800 dark:text-white">{item.name}</h3>
                  <div className="flex gap-2 mt-1">
                    {item.thc && (
                      <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-2 py-1 rounded">
                        THC {item.thc}%
                      </span>
                    )}
                    {item.cbd && (
                      <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-1 rounded">
                        CBD {item.cbd}%
                      </span>
                    )}
                  </div>
                  <p className="text-primary-600 dark:text-primary-400 font-medium mt-1">
                    {formatCurrency(item.price)}
                  </p>
                </div>

                {/* Quantity Controls */}
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => updateCartItem(item.productId, item.quantity - 1)}
                    className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-gray-900 dark:text-white"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                  <span className="w-12 text-center font-semibold text-gray-900 dark:text-white">{item.quantity}</span>
                  <button
                    onClick={() => updateCartItem(item.productId, item.quantity + 1)}
                    className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-gray-900 dark:text-white"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>

                {/* Item Total */}
                <div className="text-right">
                  <p className="font-semibold text-lg text-gray-900 dark:text-white">
                    {formatCurrency(item.price * item.quantity)}
                  </p>
                </div>

                {/* Remove Button */}
                <button
                  onClick={() => removeFromCart(item.productId)}
                  className="p-2 text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>

          {/* Order Summary */}
          <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Order Summary</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-gray-600 dark:text-gray-400">
                <span>Subtotal</span>
                                <span>{formatCurrency(subtotal)}</span>
              </div>
              <div className="flex justify-between text-gray-600 dark:text-gray-400">
                <span>Tax (HST 13%)</span>
                <span>{formatCurrency(tax)}</span>
              </div>
              <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                <div className="flex justify-between text-xl font-bold text-gray-900 dark:text-white">
                  <span>Total</span>
                                    <span className="text-primary-600 dark:text-primary-400">{formatCurrency(total)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Store Info */}
          {currentStore && (
            <div className="mt-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-sm text-blue-800 dark:text-blue-300">
                <strong>Pickup Location:</strong> {currentStore.name}
              </p>
              <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                {typeof currentStore.address === 'string'
                  ? `${currentStore.address}, ${currentStore.city}`
                  : currentStore.address?.street
                    ? `${currentStore.address.street}, ${currentStore.address.city}, ${currentStore.address.province}`
                    : `${currentStore.city || ''}`
                }
              </p>
            </div>
          )}

          {/* Product Recommendations */}
          <div className="mt-6">
            <ProductRecommendations
              storeId={currentStore?.id || ''}
              sessionId={sessionId}
              onProductClick={setSelectedProduct}
            />
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="max-w-4xl mx-auto flex gap-4">
          <button
            onClick={onBack}
            className="flex-1 px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Continue Shopping
          </button>
          <button
            onClick={onCheckout}
            className="flex-1 px-6 py-3 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600 transition-colors font-semibold"
          >
            Proceed to Checkout
          </button>
        </div>
      </div>

      {/* Product Details Modal */}
      {selectedProduct && (
        <ProductDetailsModal
          product={selectedProduct}
          isOpen={!!selectedProduct}
          onClose={() => setSelectedProduct(null)}
        />
      )}
    </div>
  );
}