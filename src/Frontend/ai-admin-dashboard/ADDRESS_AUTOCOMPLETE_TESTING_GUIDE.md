# Address Autocomplete Testing Guide
**Date:** October 13, 2025
**Feature:** Address Autocomplete for "Create New Store" Form
**Status:** ✅ **IMPLEMENTED - READY FOR TESTING**

---

## Implementation Summary

### ✅ Completed Tasks

1. **Created AddressAutocomplete Component** (`/src/components/AddressAutocomplete.tsx`)
   - Debounced search (300ms delay)
   - Keyboard navigation (↑↓ Enter Escape)
   - Loading states and error handling
   - Clear button and visual feedback
   - Accessibility features (ARIA labels, keyboard focus)

2. **Integrated into StoreManagement Form** (`/src/pages/StoreManagement.tsx`)
   - Replaced plain street address input
   - Auto-populates city and postal code
   - Captures coordinates for delivery calculations
   - Syncs province with address selection

3. **Form State Updates**
   - Added coordinates state
   - Updated form submission to include location data
   - Made city and postal code read-only

---

## Backend API Status

### ✅ Geocoding Service - HEALTHY

**Endpoint:** `http://localhost:5024/api/geocoding/autocomplete`

**Health Check:**
```bash
curl http://localhost:5024/api/geocoding/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "mapbox_geocoding",
  "api_key_configured": true,
  "statistics": {
    "cache_size": 0,
    "api_calls": 0,
    "cache_hits": 0,
    "cache_hit_rate": "0.0%",
    "cache_ttl_hours": 24.0,
    "rate_limit_available_tokens": 100.0,
    "rate_limit_max_tokens": 100,
    "rate_limit_requests_last_window": 0,
    "rate_limit_max_per_window": 100,
    "rate_limit_utilization": "0.0%",
    "rate_limit_delays": 0
  }
}
```

### ✅ Test Query - WORKING

**Test Command:**
```bash
curl "http://localhost:5024/api/geocoding/autocomplete?query=123%20Main%20Toronto&limit=3"
```

**Sample Response:**
```json
[
  {
    "id": "address.4687616445403320",
    "place_name": "123 Main Street, Toronto, Ontario M4C 4Y2, Canada",
    "address": {
      "street": "123 Main Street",
      "city": "Toronto",
      "province": "Ontario",
      "postal_code": "M4C 4Y2",
      "country": "Canada"
    },
    "coordinates": {
      "latitude": 43.682822,
      "longitude": -79.299724
    },
    "relevance": 0.885185
  }
]
```

---

## Testing Checklist

### Phase 1: Component Testing

#### 1.1 Basic Functionality
- [ ] **Start the admin dashboard**
  ```bash
  cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Frontend/ai-admin-dashboard
  npm start
  ```

- [ ] **Navigate to Store Management**
  - Login to admin dashboard
  - Go to "Tenant Management"
  - Select a tenant
  - Click "New Store" button

- [ ] **Test Address Autocomplete Input**
  - Input field should have map pin icon on left
  - Input field should be focused and ready to type
  - Placeholder text: "Start typing an address..."

#### 1.2 Search Functionality
- [ ] **Type less than 3 characters**
  - Type "12"
  - Verify: No API call is made (check Network tab)
  - Verify: Helper text appears: "Type at least 3 characters to search"

- [ ] **Type 3+ characters**
  - Type "123 Main Toronto"
  - Verify: Loading spinner appears (right side of input)
  - Verify: Dropdown appears with suggestions after ~300ms
  - Verify: Suggestions show street, city, province, postal code
  - Verify: Map pin icon appears next to each suggestion

- [ ] **Debouncing**
  - Type quickly: "123 Ma"
  - Verify: Only ONE API call is made after 300ms delay
  - Check Network tab: Should see single request, not multiple

#### 1.3 Selection
- [ ] **Click on a suggestion**
  - Click on first suggestion
  - Verify: Street address field updates
  - Verify: City field updates (read-only)
  - Verify: Postal code field updates (read-only)
  - Verify: Province dropdown updates to match
  - Verify: Dropdown closes
  - Verify: Input field shows full address

- [ ] **Keyboard navigation**
  - Type "123 Main Toronto"
  - Press ↓ (down arrow) - first suggestion highlights
  - Press ↓ again - second suggestion highlights
  - Press ↑ (up arrow) - back to first suggestion
  - Press Enter - suggestion is selected
  - Verify: All fields update correctly

- [ ] **Escape key**
  - Type "123 Main Toronto"
  - Wait for suggestions
  - Press Escape
  - Verify: Dropdown closes
  - Verify: Input field retains typed text

#### 1.4 Error Handling
- [ ] **No results**
  - Type "zzzzz99999"
  - Wait for response
  - Verify: "No addresses found" message appears
  - Verify: Helpful message: "Try a different search or check your spelling"

- [ ] **API error** (simulate by stopping backend)
  - Stop the backend API: `pkill -f api_server.py`
  - Type "123 Main Toronto"
  - Verify: Error message appears
  - Verify: Error icon (red triangle) appears
  - Verify: Form can still be submitted manually
  - **Restart backend:** `cd /Backend && python api_server.py`

#### 1.5 Clear Button
- [ ] **Clear input**
  - Type "123 Main Toronto"
  - Select a suggestion
  - Verify: X button appears on right side
  - Click X button
  - Verify: Input clears
  - Verify: City and postal code clear
  - Verify: Coordinates reset
  - Verify: Focus returns to input field

### Phase 2: Form Integration Testing

#### 2.1 Form State
- [ ] **Address auto-fill**
  - Type "456 Queen St Toronto"
  - Select first suggestion
  - Verify: All address fields populate:
    - Street Address: "456 Queen Street"
    - City: "Toronto" (read-only)
    - Postal Code: "M5V 2A3" (read-only)
    - Province: "ON" (dropdown syncs)

- [ ] **Read-only fields**
  - Try to type in City field
  - Verify: Field is read-only (cursor shows "not-allowed")
  - Verify: Background is gray (disabled appearance)
  - Verify: "Auto-filled" text appears below field
  - Try to type in Postal Code field
  - Verify: Same behavior as City field

- [ ] **Coordinates capture**
  - Type "789 Bay St Toronto"
  - Select a suggestion
  - Open Browser DevTools Console
  - Check state: Should see coordinates stored
  - Example: `{latitude: 43.6532, longitude: -79.3832}`

#### 2.2 Form Submission
- [ ] **Submit with autocomplete data**
  - Fill in required fields:
    - Store Name: "Test Store 123"
    - Province: "ON"
    - Address: Use autocomplete to select "123 Yonge St Toronto"
    - Phone: "416-555-0123"
    - Email: "test@example.com"
  - Click "Create Store"
  - Verify: Form submits successfully
  - Verify: No validation errors
  - Open Network tab and check request payload
  - Verify: Includes `location: {latitude: ..., longitude: ...}`

- [ ] **Submit without coordinates**
  - Manually type address (don't use autocomplete)
  - Type in Street Address: "123 Fake Street"
  - City and postal code will be empty (read-only)
  - Verify: Form validation catches missing city/postal code
  - OR: Manually fill city/postal code if validation allows
  - Submit form
  - Verify: Submission works (location may be undefined/null)

#### 2.3 Edit Existing Store
- [ ] **Load existing store data**
  - Create a store with autocomplete
  - Click "Edit" on the store
  - Verify: Address fields populate correctly
  - Verify: City and postal code are read-only
  - Verify: Can update address using autocomplete
  - Save changes
  - Verify: Updates are saved correctly

### Phase 3: UX Testing

#### 3.1 Responsiveness
- [ ] **Desktop view**
  - Test on full-screen browser (1920x1080)
  - Verify: Dropdown width matches input width
  - Verify: Suggestions are readable
  - Verify: No horizontal scrolling

- [ ] **Tablet view**
  - Resize browser to 768px width
  - Test autocomplete
  - Verify: Layout adjusts properly
  - Verify: Dropdown is usable

- [ ] **Mobile view** (if accessible)
  - Resize browser to 375px width
  - Test autocomplete
  - Verify: Touch interactions work
  - Verify: Dropdown doesn't overflow screen

#### 3.2 Dark Mode
- [ ] **Toggle dark mode**
  - Enable dark mode in admin dashboard
  - Test address autocomplete
  - Verify: Input field uses dark styling
  - Verify: Dropdown uses dark styling
  - Verify: Text is readable (white text on dark background)
  - Verify: Icons are visible

#### 3.3 Loading States
- [ ] **Visual feedback during search**
  - Type "123 Main"
  - Observe loading spinner
  - Verify: Spinner is centered and visible
  - Verify: Spinner stops when results load
  - Verify: Smooth transition from loading to results

#### 3.4 Performance
- [ ] **Search speed**
  - Type "123 Main Toronto"
  - Measure time from typing to results appearing
  - Should be < 1 second (300ms debounce + ~200-500ms API)
  - Verify: Feels responsive

- [ ] **Cache effectiveness**
  - Type "123 Main Toronto"
  - Select a suggestion
  - Clear the field
  - Type "123 Main Toronto" again
  - Check Network tab: Should see cache hit (faster response)
  - Verify: Results appear instantly or very quickly

### Phase 4: Edge Cases

#### 4.1 Special Characters
- [ ] **Test with special characters**
  - Type "123 O'Connor St Ottawa"
  - Verify: Autocomplete works
  - Type "123 Rue Saint-Jean Québec"
  - Verify: French characters are handled correctly

#### 4.2 Long Addresses
- [ ] **Test with very long street names**
  - Type "123 Extremely Long Street Name That Goes On Forever"
  - Verify: Input doesn't break layout
  - Verify: Dropdown truncates long text with ellipsis

#### 4.3 Multiple Matches
- [ ] **Test with ambiguous query**
  - Type "Main St"
  - Verify: Shows multiple suggestions
  - Verify: Each suggestion is clearly different
  - Verify: Can select any suggestion

#### 4.4 Rapid Input Changes
- [ ] **Test rapid typing**
  - Type "123 Main Toronto"
  - Immediately clear and type "456 Queen Toronto"
  - Verify: Only shows results for "456 Queen Toronto"
  - Verify: Previous search is cancelled (check Network tab)

### Phase 5: Accessibility Testing

#### 5.1 Keyboard Navigation
- [ ] **Tab navigation**
  - Press Tab to focus on address input
  - Verify: Input field is focused (visible outline)
  - Type and use arrow keys to navigate suggestions
  - Press Tab to move to next field
  - Verify: Dropdown closes

- [ ] **Screen reader** (if available)
  - Enable screen reader (VoiceOver on Mac, NVDA on Windows)
  - Navigate to address input
  - Verify: Input field is announced
  - Type and wait for suggestions
  - Verify: Suggestions are announced
  - Navigate with arrow keys
  - Verify: Selected suggestion is announced

#### 5.2 ARIA Labels
- [ ] **Inspect ARIA attributes** (DevTools)
  - Check input field has proper labels
  - Check dropdown has `role="listbox"`
  - Check suggestions have `role="option"`
  - Check `aria-selected` attribute updates correctly

### Phase 6: Integration with Backend

#### 6.1 API Endpoint Verification
- [ ] **Check API response structure**
  - Open Network tab
  - Type "123 Main Toronto"
  - Click on the API request
  - Verify response format matches:
    ```json
    [
      {
        "id": "...",
        "place_name": "...",
        "address": { "street", "city", "province", "postal_code", "country" },
        "coordinates": { "latitude", "longitude" },
        "relevance": 0.XX
      }
    ]
    ```

- [ ] **Check API headers**
  - Verify: `Content-Type: application/json`
  - Verify: Authorization headers if required

#### 6.2 Rate Limiting
- [ ] **Test rate limit handling**
  - Make 100+ rapid searches (if possible)
  - Verify: Requests are throttled gracefully
  - Verify: No errors shown to user
  - Verify: Requests queue properly

#### 6.3 Store Creation End-to-End
- [ ] **Full store creation flow**
  1. Navigate to Tenant Management
  2. Select a tenant
  3. Click "New Store"
  4. Fill in all required fields:
     - Store Name: "Integration Test Store"
     - Province: "ON"
     - Address: Use autocomplete "123 Yonge St Toronto"
     - Phone: "416-555-0100"
     - Email: "integration@test.com"
     - License Number: "LIC-12345"
  5. Submit form
  6. Verify: Store is created successfully
  7. Verify: Store appears in list with correct address
  8. Click on store to view details
  9. Verify: Address and coordinates are saved
  10. Check database (if accessible):
      ```sql
      SELECT name, address, location FROM stores ORDER BY created_at DESC LIMIT 1;
      ```
  11. Verify: `location` contains `{latitude, longitude}`

---

## Expected Results Summary

### ✅ Success Criteria

1. **Functionality**
   - Address autocomplete loads suggestions in < 1 second
   - Suggestions are accurate and relevant
   - Selecting a suggestion populates all address fields
   - Coordinates are captured correctly

2. **User Experience**
   - Typing feels responsive (300ms debounce)
   - Loading states are clear
   - Error messages are helpful
   - Form submission is smooth

3. **Accessibility**
   - Keyboard navigation works perfectly
   - Screen reader compatible
   - ARIA labels are correct

4. **Performance**
   - Cache reduces redundant API calls
   - Rate limiting prevents quota exhaustion
   - No memory leaks or performance degradation

5. **Integration**
   - Form submits with coordinates
   - Stores are created successfully
   - Data is saved to database correctly

---

## Troubleshooting

### Issue: Autocomplete not loading suggestions

**Possible Causes:**
1. Backend API not running
2. Mapbox API key not configured
3. Network error

**Solutions:**
1. Check backend is running: `curl http://localhost:5024/health`
2. Check geocoding service: `curl http://localhost:5024/api/geocoding/health`
3. Check Mapbox API key: `echo $MAPBOX_API_KEY` (should not be empty)
4. Check browser console for errors
5. Check Network tab for failed requests

### Issue: Dropdown not appearing

**Possible Causes:**
1. Query too short (< 3 characters)
2. Dropdown is hidden by CSS z-index
3. JavaScript error

**Solutions:**
1. Type at least 3 characters
2. Check browser console for errors
3. Inspect element and check z-index value (should be 50)
4. Check if dropdown element exists in DOM

### Issue: City and Postal Code not updating

**Possible Causes:**
1. API response missing fields
2. State update not working
3. Form data not syncing

**Solutions:**
1. Check API response in Network tab
2. Check browser console for errors
3. Verify `onChange` handler is called (add console.log)
4. Check React state updates (use React DevTools)

### Issue: Coordinates not captured

**Possible Causes:**
1. `onCoordinatesChange` not called
2. State not updating
3. Coordinates not included in API response

**Solutions:**
1. Verify `onCoordinatesChange` prop is passed
2. Check coordinates state with React DevTools
3. Check API response includes `coordinates` field
4. Add console.log to verify coordinates are set

### Issue: Form submission fails

**Possible Causes:**
1. Missing required fields
2. Invalid data format
3. Backend validation error

**Solutions:**
1. Check all required fields are filled
2. Check browser console for errors
3. Check Network tab for response error
4. Verify coordinates format: `{latitude: number, longitude: number}`

---

## Performance Monitoring

### Metrics to Track

1. **API Response Time**
   - Target: < 500ms (95th percentile)
   - Check Network tab: Response time for `/api/geocoding/autocomplete`

2. **Cache Hit Rate**
   - Target: > 40% after initial usage
   - Check: `curl http://localhost:5024/api/geocoding/health`
   - Look for: `"cache_hit_rate": "XX%"`

3. **Rate Limit Utilization**
   - Target: < 50% utilization
   - Check: `curl http://localhost:5024/api/geocoding/health`
   - Look for: `"rate_limit_utilization": "XX%"`

4. **User Completion Time**
   - Target: < 10 seconds for address entry
   - Manual timing: Start when user focuses input, stop when address is filled

---

## Testing Automation (Future)

### Unit Tests (Jest + React Testing Library)
```typescript
describe('AddressAutocomplete', () => {
  it('should render input field', () => { /* ... */ });
  it('should debounce search queries', () => { /* ... */ });
  it('should display suggestions', () => { /* ... */ });
  it('should handle selection', () => { /* ... */ });
  it('should handle keyboard navigation', () => { /* ... */ });
  it('should show error on API failure', () => { /* ... */ });
});
```

### Integration Tests (Cypress/Playwright)
```javascript
describe('Store Creation with Address Autocomplete', () => {
  it('should create store with autocomplete', () => {
    cy.visit('/dashboard/tenants/TEST_TENANT/stores');
    cy.get('[data-testid="new-store-button"]').click();
    cy.get('[data-testid="address-autocomplete"]').type('123 Main Toronto');
    cy.wait(500); // Wait for debounce + API
    cy.get('[data-testid="suggestion-0"]').click();
    cy.get('[data-testid="city-input"]').should('have.value', 'Toronto');
    cy.get('[data-testid="submit-button"]').click();
    cy.contains('Store created successfully');
  });
});
```

---

## Sign-Off Checklist

### Developer Sign-Off
- [ ] Code is committed to version control
- [ ] Code is reviewed by peer
- [ ] Unit tests are written and passing
- [ ] Documentation is complete
- [ ] Known issues are documented

### QA Sign-Off
- [ ] All test cases in this document are passed
- [ ] Edge cases are tested
- [ ] Accessibility is verified
- [ ] Performance is acceptable
- [ ] Integration with backend is verified

### Product Owner Sign-Off
- [ ] Feature meets requirements
- [ ] UX is acceptable
- [ ] Ready for production deployment

---

## Deployment Notes

### Prerequisites
1. ✅ Backend API running on port 5024
2. ✅ Mapbox API key configured
3. ✅ Admin dashboard build process working

### Deployment Steps
1. Build admin dashboard: `npm run build`
2. Deploy to production environment
3. Verify API endpoint is accessible
4. Monitor error logs for first 24 hours
5. Gather user feedback

### Rollback Plan
If issues are found in production:
1. Revert to previous version: `git revert <commit-hash>`
2. Redeploy: `npm run build && deploy`
3. Notify users of temporary rollback
4. Fix issues and redeploy

---

`★ Insight ─────────────────────────────────────`

**Testing Best Practices for Address Autocomplete:**

1. **Debouncing is Critical** - Without the 300ms debounce, every keystroke would fire an API request, quickly exhausting rate limits. Always test that debouncing works correctly by checking the Network tab for request timing.

2. **Edge Cases Matter** - Address autocomplete can break in unexpected ways: special characters (O'Connor), French addresses (Rue Saint-Jean), ambiguous queries (Main St). Test these thoroughly to avoid production issues.

3. **Accessibility is Non-Negotiable** - Screen reader users need to complete forms too. Keyboard navigation and ARIA labels aren't nice-to-haves; they're requirements for compliance (WCAG 2.1 Level AA).

This comprehensive test guide ensures the feature works reliably across all scenarios. Manual testing catches UX issues automated tests miss, making it essential for user-facing features like this.

`─────────────────────────────────────────────────`

---

**Status:** ✅ **READY FOR TESTING**
**API:** ✅ **OPERATIONAL** (http://localhost:5024/api/geocoding/autocomplete)
**Component:** ✅ **IMPLEMENTED** (`AddressAutocomplete.tsx`)
**Integration:** ✅ **COMPLETE** (`StoreManagement.tsx`)

---

*Generated: October 13, 2025*
*Implementation Time: ~2 hours*
*Test Coverage: Comprehensive*
