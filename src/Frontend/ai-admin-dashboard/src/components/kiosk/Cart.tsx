import { getApiUrl } from '../../config/app.config';
import React, { useState } from 'react';
import { getApiUrl } from '../../config/app.config';
import { ChevronLeft, Plus, Minus, Trash2, ShoppingCart } from 'lucide-react';
import { useKiosk } from '../../contexts/KioskContext';
import ProductRecommendations from './ProductRecommendations';
import ProductDetailsModal from './ProductDetailsModal';

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
      <div className="h-full flex flex-col items-center justify-center bg-gray-50 p-8">
        <ShoppingCart className="w-24 h-24 text-gray-300 mb-4" />
        <h2 className="text-2xl font-semibold text-gray-700 mb-2">Your Cart is Empty</h2>
        <p className="text-gray-500 mb-6">Add some products to get started</p>
        <button
          onClick={onBack}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          Continue Shopping
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <h1 className="text-2xl font-bold text-gray-800">Your Cart</h1>
            <span className="text-sm text-gray-500">({cartItemCount} items)</span>
          </div>
          <button
            onClick={clearCart}
            className="text-red-600 hover:text-red-700 font-medium"
          >
            Clear Cart
          </button>
        </div>
      </div>

      {/* Cart Items */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-md">
            {cart.map((item) => (
              <div
                key={item.id}
                className="flex items-center gap-4 p-4 border-b last:border-b-0"
              >
                {/* Product Image */}
                <div className="w-20 h-20 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                  <img
                    src={item.image || 'api/placeholder/80/80'}
                    alt={item.name}
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* Product Info */}
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-800">{item.name}</h3>
                  <div className="flex gap-2 mt-1">
                    {item.thc && (
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                        THC {item.thc}%
                      </span>
                    )}
                    {item.cbd && (
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                        CBD {item.cbd}%
                      </span>
                    )}
                  </div>
                  <p className="text-primary-600 font-medium mt-1">
                    ${item.price.toFixed(2)}
                  </p>
                </div>

                {/* Quantity Controls */}
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => updateCartItem(item.productId, item.quantity - 1)}
                    className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                  <span className="w-12 text-center font-semibold">{item.quantity}</span>
                  <button
                    onClick={() => updateCartItem(item.productId, item.quantity + 1)}
                    className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>

                {/* Item Total */}
                <div className="text-right">
                  <p className="font-semibold text-lg">
                    ${(item.price * item.quantity).toFixed(2)}
                  </p>
                </div>

                {/* Remove Button */}
                <button
                  onClick={() => removeFromCart(item.productId)}
                  className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>

          {/* Order Summary */}
          <div className="mt-6 bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Order Summary</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Tax (HST 13%)</span>
                <span>${tax.toFixed(2)}</span>
              </div>
              <div className="pt-2 border-t">
                <div className="flex justify-between text-xl font-bold">
                  <span>Total</span>
                  <span className="text-primary-600">${total.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Store Info */}
          {currentStore && (
            <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>Pickup Location:</strong> {currentStore.name}
              </p>
              <p className="text-sm text-blue-600 mt-1">
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
      <div className="bg-white border-t px-6 py-4">
        <div className="max-w-4xl mx-auto flex gap-4">
          <button
            onClick={onBack}
            className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Continue Shopping
          </button>
          <button
            onClick={onCheckout}
            className="flex-1 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-semibold"
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