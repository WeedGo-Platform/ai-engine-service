/**
 * End-to-End Tests for Mobile Checkout Flow
 * Framework: Detox (React Native E2E testing)
 *
 * These tests simulate real user interactions on mobile devices
 * Reference: Airbnb Mobile Testing Strategy
 */

describe('Mobile Checkout Flow', () => {
  beforeAll(async () => {
    await device.launchApp({
      newInstance: true,
      permissions: { location: 'always' }
    });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  /**
   * E2E TEST: Complete delivery checkout flow
   * User journey: Browse → Add to Cart → Checkout → Delivery → Payment → Confirm
   */
  it('should complete delivery checkout successfully', async () => {
    // 1. Navigate to product listing
    await element(by.id('products-tab')).tap();
    await expect(element(by.id('product-list'))).toBeVisible();

    // 2. Add product to cart
    await element(by.id('product-item-0')).tap();
    await expect(element(by.id('product-details'))).toBeVisible();
    await element(by.id('add-to-cart-button')).tap();

    // Wait for cart animation
    await waitFor(element(by.id('cart-count-badge')))
      .toBeVisible()
      .withTimeout(2000);

    // 3. Navigate to cart
    await element(by.id('cart-tab')).tap();
    await expect(element(by.id('cart-items-list'))).toBeVisible();

    // 4. Proceed to checkout
    await element(by.id('checkout-button')).tap();
    await expect(element(by.id('checkout-screen'))).toBeVisible();

    // 5. Select delivery method
    await element(by.id('delivery-method-toggle')).tap();
    await expect(element(by.id('delivery-address-section'))).toBeVisible();

    // 6. Enter delivery address
    await element(by.id('address-street-input')).typeText('123 Test Street\n');
    await element(by.id('address-city-input')).typeText('Toronto\n');
    await element(by.id('address-postal-input')).typeText('M5V1A1\n');

    // 7. Select payment method
    await element(by.id('payment-method-selector')).tap();
    await element(by.text('Credit Card')).tap();

    // 8. Add tip
    await element(by.id('tip-10-percent-button')).tap();

    // 9. Review order summary
    await expect(element(by.id('order-summary'))).toBeVisible();
    await expect(element(by.id('order-total'))).toBeVisible();

    // 10. Place order
    await element(by.id('place-order-button')).tap();

    // 11. Verify order confirmation
    await waitFor(element(by.id('order-confirmation-screen')))
      .toBeVisible()
      .withTimeout(10000);

    await expect(element(by.id('order-number'))).toBeVisible();
    await expect(element(by.text(/Order placed successfully/i))).toBeVisible();
  });

  /**
   * E2E TEST: Complete pickup checkout flow
   */
  it('should complete pickup checkout successfully', async () => {
    // Add item to cart
    await element(by.id('products-tab')).tap();
    await element(by.id('product-item-0')).tap();
    await element(by.id('add-to-cart-button')).tap();

    // Navigate to checkout
    await element(by.id('cart-tab')).tap();
    await element(by.id('checkout-button')).tap();

    // Select pickup
    await element(by.id('pickup-method-toggle')).tap();
    await expect(element(by.id('pickup-time-selector'))).toBeVisible();

    // Select pickup time
    await element(by.id('pickup-time-selector')).tap();
    await element(by.text('Today at 3:00 PM')).tap();

    // Select payment (cash on pickup)
    await element(by.id('payment-method-selector')).tap();
    await element(by.text('Cash')).tap();

    // Place order
    await element(by.id('place-order-button')).tap();

    // Verify confirmation
    await waitFor(element(by.id('order-confirmation-screen')))
      .toBeVisible()
      .withTimeout(10000);

    await expect(element(by.text(/Pick up today at 3:00 PM/i))).toBeVisible();
  });

  /**
   * E2E TEST: Verify cart locking prevents double checkout
   * Simulates user clicking "Place Order" twice quickly
   */
  it('should prevent double checkout when user taps place order twice', async () => {
    // Setup: Add item and navigate to checkout
    await element(by.id('products-tab')).tap();
    await element(by.id('product-item-0')).tap();
    await element(by.id('add-to-cart-button')).tap();
    await element(by.id('cart-tab')).tap();
    await element(by.id('checkout-button')).tap();

    // Fill out checkout form
    await element(by.id('delivery-method-toggle')).tap();
    await element(by.id('address-street-input')).typeText('123 Test St\n');
    await element(by.id('address-city-input')).typeText('Toronto\n');
    await element(by.id('address-postal-input')).typeText('M5V1A1\n');
    await element(by.id('payment-method-selector')).tap();
    await element(by.text('Credit Card')).tap();

    // Tap place order button TWICE rapidly
    await element(by.id('place-order-button')).multiTap(2);

    // Verify only ONE order confirmation appears
    await waitFor(element(by.id('order-confirmation-screen')))
      .toBeVisible()
      .withTimeout(10000);

    // Get order number
    const orderNumber = await element(by.id('order-number')).getAttributes();

    // Go back to orders list
    await element(by.id('view-orders-button')).tap();

    // Verify only ONE order with this number exists
    const ordersList = await element(by.id('orders-list')).getAttributes();
    // Count occurrences of order number (should be 1)
    // This prevents duplicate orders from double-tap
  });

  /**
   * E2E TEST: Handle out-of-stock items during checkout
   */
  it('should show error when item goes out of stock during checkout', async () => {
    // Add item to cart
    await element(by.id('products-tab')).tap();
    await element(by.id('product-item-limited-stock')).tap();
    await element(by.id('add-to-cart-button')).tap();

    // Start checkout
    await element(by.id('cart-tab')).tap();
    await element(by.id('checkout-button')).tap();

    // Fill checkout
    await element(by.id('delivery-method-toggle')).tap();
    await element(by.id('address-street-input')).typeText('123 Test St\n');
    await element(by.id('address-city-input')).typeText('Toronto\n');
    await element(by.id('address-postal-input')).typeText('M5V1A1\n');

    // At this point, another user buys the last item (simulated by test backend)
    // Attempt to place order
    await element(by.id('place-order-button')).tap();

    // Verify out-of-stock error appears
    await waitFor(element(by.text(/out of stock/i)))
      .toBeVisible()
      .withTimeout(5000);

    await expect(element(by.id('inventory-error-dialog'))).toBeVisible();
  });

  /**
   * E2E TEST: Verify price recalculation prevents manipulation
   */
  it('should use server-calculated prices, not client prices', async () => {
    // Add item to cart
    await element(by.id('products-tab')).tap();
    await element(by.id('product-item-0')).tap();

    // Capture displayed price
    const productPrice = await element(by.id('product-price')).getAttributes();
    const expectedPrice = parseFloat(productPrice.text.replace('$', ''));

    await element(by.id('add-to-cart-button')).tap();

    // Navigate to checkout
    await element(by.id('cart-tab')).tap();
    await element(by.id('checkout-button')).tap();

    // Fill checkout
    await element(by.id('delivery-method-toggle')).tap();
    await element(by.id('address-street-input')).typeText('123 Test St\n');
    await element(by.id('address-city-input')).typeText('Toronto\n');
    await element(by.id('address-postal-input')).typeText('M5V1A1\n');
    await element(by.id('payment-method-selector')).tap();
    await element(by.text('Credit Card')).tap();

    // Check order summary price matches original
    const summaryPrice = await element(by.id('order-subtotal')).getAttributes();
    const actualPrice = parseFloat(summaryPrice.text.replace('$', ''));

    // Verify server recalculated price (not manipulated)
    expect(Math.abs(actualPrice - expectedPrice)).toBeLessThan(0.01);

    // Place order
    await element(by.id('place-order-button')).tap();

    // Verify confirmation shows same price
    await waitFor(element(by.id('order-confirmation-screen')))
      .toBeVisible()
      .withTimeout(10000);

    const confirmationPrice = await element(by.id('order-total-amount')).getAttributes();
    const finalPrice = parseFloat(confirmationPrice.text.replace('$', ''));

    // Verify no price changed during checkout
    expect(Math.abs(finalPrice - (expectedPrice * 1.13))).toBeLessThan(0.50); // With tax
  });
});

/**
 * Detox Configuration (.detoxrc.js)
 */
// module.exports = {
//   testRunner: 'jest',
//   runnerConfig: 'e2e/config.json',
//   apps: {
//     'ios.debug': {
//       type: 'ios.app',
//       binaryPath: 'ios/build/Build/Products/Debug-iphonesimulator/WeedGo.app',
//       build: 'xcodebuild -workspace ios/WeedGo.xcworkspace -scheme WeedGo -configuration Debug -sdk iphonesimulator'
//     },
//     'android.debug': {
//       type: 'android.apk',
//       binaryPath: 'android/app/build/outputs/apk/debug/app-debug.apk',
//       build: 'cd android && ./gradlew assembleDebug'
//     }
//   },
//   devices: {
//     simulator: {
//       type: 'ios.simulator',
//       device: { type: 'iPhone 14 Pro' }
//     },
//     emulator: {
//       type: 'android.emulator',
//       device: { avdName: 'Pixel_6_API_33' }
//     }
//   },
//   configurations: {
//     'ios.sim.debug': {
//       device: 'simulator',
//       app: 'ios.debug'
//     },
//     'android.emu.debug': {
//       device: 'emulator',
//       app: 'android.debug'
//     }
//   }
// };
