import React, { useEffect, useState } from 'react';
import { CheckCircle, ShoppingBag, MapPin, Clock, Home } from 'lucide-react';
import { useKiosk } from '../../contexts/KioskContext';

interface OrderConfirmationProps {
  orderId: string;
  onNewOrder: () => void;
  onReturnHome?: () => void;
  currentStore: any;
}

export default function OrderConfirmation({
  orderId,
  onNewOrder,
  onReturnHome,
  currentStore
}: OrderConfirmationProps) {
  const { language } = useKiosk();
  const [countdown, setCountdown] = useState(30);

  // Generate order number from order ID
  const orderNumber = `K${new Date().toISOString().slice(0, 10).replace(/-/g, '')}${orderId.slice(0, 4).toUpperCase()}`;

  // Auto-redirect countdown
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          // Reset to welcome screen
          if (onReturnHome) {
            onReturnHome();
          } else {
            onNewOrder();
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [onReturnHome, onNewOrder]);

  const translations: Record<string, any> = {
    en: {
      thankYou: 'Thank You!',
      orderConfirmed: 'Your order has been confirmed',
      orderNumber: 'Order Number',
      pickupReady: 'Ready for Pickup',
      pickupLocation: 'Pickup Location',
      whatNext: "What's Next?",
      step1: 'Proceed to the counter',
      step2: 'Show your order number',
      step3: 'Collect your order',
      newOrder: 'Start New Order',
      returnHome: 'Return to Home',
      redirecting: 'Returning to home in',
      seconds: 'seconds'
    },
    fr: {
      thankYou: 'Merci!',
      orderConfirmed: 'Votre commande a été confirmée',
      orderNumber: 'Numéro de commande',
      pickupReady: 'Prêt pour le ramassage',
      pickupLocation: 'Lieu de ramassage',
      whatNext: 'Et après?',
      step1: 'Rendez-vous au comptoir',
      step2: 'Montrez votre numéro de commande',
      step3: 'Récupérez votre commande',
      newOrder: 'Nouvelle commande',
      returnHome: "Retour à l'accueil",
      redirecting: "Retour à l'accueil dans",
      seconds: 'secondes'
    },
    zh: {
      thankYou: '谢谢！',
      orderConfirmed: '您的订单已确认',
      orderNumber: '订单号',
      pickupReady: '准备取货',
      pickupLocation: '取货地点',
      whatNext: '下一步？',
      step1: '前往柜台',
      step2: '显示您的订单号',
      step3: '领取您的订单',
      newOrder: '开始新订单',
      returnHome: '返回首页',
      redirecting: '返回首页',
      seconds: '秒'
    }
  };

  const t = translations[language] || translations['en'];

  return (
    <div className="h-full flex flex-col items-center justify-center bg-gradient-to-br from-green-50 to-primary-50 p-8">
      <div className="max-w-2xl w-full">
        {/* Success Animation */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-32 h-32 bg-green-100 rounded-full mb-6">
            <CheckCircle className="w-20 h-20 text-green-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">{t.thankYou}</h1>
          <p className="text-xl text-gray-600">{t.orderConfirmed}</p>
        </div>

        {/* Order Details Card */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
          {/* Order Number */}
          <div className="text-center mb-6 pb-6 border-b">
            <p className="text-gray-500 mb-2">{t.orderNumber}</p>
            <p className="text-4xl font-bold text-primary-600">{orderNumber}</p>
          </div>

          {/* Status */}
          <div className="flex items-center justify-center gap-2 mb-6">
            <Clock className="w-5 h-5 text-green-600" />
            <span className="text-lg font-semibold text-green-600">{t.pickupReady}</span>
          </div>

          {/* Pickup Location */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <MapPin className="w-5 h-5 text-primary-600 mt-1" />
              <div>
                <p className="font-semibold text-gray-800">{t.pickupLocation}</p>
                <p className="text-gray-600">{currentStore?.name || 'Store'}</p>
                {currentStore && (
                  <p className="text-sm text-gray-500">
                    {typeof currentStore.address === 'string'
                      ? `${currentStore.address}, ${currentStore.city}`
                      : currentStore.address?.street
                        ? `${currentStore.address.street}, ${currentStore.address.city}, ${currentStore.address.province}`
                        : `${currentStore.city || ''}`
                    }
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Next Steps */}
          <div>
            <h3 className="font-semibold text-gray-800 mb-3">{t.whatNext}</h3>
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-semibold">
                  1
                </div>
                <p className="text-gray-600">{t.step1}</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-semibold">
                  2
                </div>
                <p className="text-gray-600">{t.step2}</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-semibold">
                  3
                </div>
                <p className="text-gray-600">{t.step3}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={onNewOrder}
            className="flex-1 px-6 py-4 bg-white border-2 border-primary-600 text-primary-600 rounded-xl font-semibold hover:bg-primary-50 transition-colors flex items-center justify-center gap-2"
          >
            <ShoppingBag className="w-5 h-5" />
            {t.newOrder}
          </button>
          <button
            onClick={onReturnHome || onNewOrder}
            className="flex-1 px-6 py-4 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-colors flex items-center justify-center gap-2"
          >
            <Home className="w-5 h-5" />
            {t.returnHome}
          </button>
        </div>

        {/* Auto-redirect countdown */}
        <div className="text-center mt-6 text-gray-500">
          <p>
            {t.redirecting} <span className="font-semibold">{countdown}</span> {t.seconds}
          </p>
        </div>
      </div>
    </div>
  );
}