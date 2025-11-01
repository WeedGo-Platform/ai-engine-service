# Kiosk & Menu Display - Hardcoded Strings Analysis

## Files to Process:
1. WelcomeScreen.tsx - Has custom translation system
2. Cart.tsx
3. Checkout.tsx  
4. ProductBrowsing.tsx
5. ProductDetailsModal.tsx
6. OrderConfirmation.tsx
7. ProductRecommendations.tsx
8. AIAssistant.tsx
9. MenuDisplay.tsx

## Identified Hardcoded Strings:

### WelcomeScreen.tsx
- Uses custom translation object (lines 22-51)
- Needs migration to i18n system
- Strings: welcome, selectLanguage, orContinue, scanQR, signIn, continueAsGuest, touchToStart
- "Select Store" (line 87)

### Cart.tsx  
- "Your Cart is Empty" (line 37)
- "Add some products to get started" (line 38)
- "Your Cart" (line 61)
- "Order Summary" (line 148)
- "Subtotal" (line 151)
- "Tax (HST 13%)" (line 155)
- "Total" (line 160)
- "Pickup Location:" (line 171)

### Checkout.tsx
- "Complete Your Order" (line 104)
- "Order Summary" (line 114)
- "Subtotal" (line 134)
- "Tax (HST 13%)" (line 138)
- "Total" (line 142)
- "Contact Information" (line 150)
- "Optional - Help us notify you when your order is ready" (line 151)
- Placeholders: "Enter your name (optional)", "Enter your email (optional)", "Enter your phone number (optional)"

### ProductBrowsing.tsx
- "Browse Products" (line 299)
- "Search products..." placeholder (line 324)
- "Loading filters..." (lines 343, 368, 393)
- "Quick Filters" (line 412)
- "Sort By" (line 442)
- Sort options: "Name (A-Z)", "Price: Low to High", "Price: High to Low", "Size: Large to Small", "Most Popular"
- "Active Filters" (line 462)
- "No products found. Try adjusting your filters." (line 551)

### ProductDetailsModal.tsx
- Multiple field labels: "Product Identifiers", "Slug", "Categorization", "Category", "Subcategory", etc.
- "Pack: {size}" (line 449)
- "Quantity:" (line 462)
- "Out of Stock" (line 497)
- "Quick Overview", "Detailed Description" (lines 553, 561)
- "Flower Equivalent", "Extraction" (lines 571, 579)
- "Recommended" (line 612)
- "Complete Cannabinoid Profile" (line 624)
- "Per Unit:", "Per Volume:", "Range:" (lines 635, 641, 647)

### ProductRecommendations.tsx
- "Loading Recommendations..." (line 99)
- "Recommended for You" (line 122)
- "Out of Stock" (line 148)

### AIAssistant.tsx
- "Cannabis Assistant" (line 84)
- "Hi! I'm here to help..." message (line 25)
- "Ask me anything..." placeholder (line 148)

### OrderConfirmation.tsx
- "What's Next?" (line 52)
- "Retour à l'accueil dans" (line 73) - French hardcoded!

