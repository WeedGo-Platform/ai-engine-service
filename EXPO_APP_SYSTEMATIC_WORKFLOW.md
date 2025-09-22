# Systematic Development Workflow for WeedGo Mobile Application

## Agent Working Instructions

### Core Principles
1. **API-First Development**: Before implementing ANY feature, verify the API endpoint exists and works
2. **Incremental Progress**: Complete one feature entirely before moving to the next
3. **Test as You Build**: Each component must be tested before integration
4. **Document Decisions**: Log all architectural decisions and API discoveries
5. **User-Centric Focus**: Every decision should reduce user friction

## Systematic Implementation Approach

### Day 1-2: Foundation & Discovery
```typescript
TASK 1: Project Initialization
□ Create Expo project with TypeScript template
□ Install all required dependencies
□ Setup folder structure as specified
□ Configure ESLint, Prettier, and TypeScript
□ Setup environment variables
□ Test basic app launch

TASK 2: API Discovery & Documentation
□ Create API service layer structure
□ Test connection to API_URL
□ Document all available endpoints
□ Create TypeScript interfaces for all API responses
□ Setup Axios with interceptors
□ Implement request/response logging for debugging
```

### Day 3-4: Authentication Foundation
```typescript
TASK 3: Implement Authentication Flow
□ Create auth store with Zustand
□ Implement phone number input screen
□ Connect to /api/v1/auth/customer/register
□ Implement OTP verification screen
□ Setup secure token storage
□ Implement token refresh mechanism
□ Add biometric authentication
□ Test complete auth flow end-to-end

DELIVERABLE: User can register, login, and stay authenticated
```

### Day 5-6: Template System
```typescript
TASK 4: Build Template Architecture
□ Create template interface and types
□ Implement theme provider with context
□ Build Pot Palace template components
□ Build Modern template components
□ Build Headless template base
□ Create template switcher for testing
□ Implement theme persistence

DELIVERABLE: App can switch between templates dynamically
```

### Day 7-8: Product Browsing
```typescript
TASK 5: Product Discovery Features
□ Create product service layer
□ Implement product grid with FlashList
□ Add category filters
□ Implement search with debouncing
□ Create product card component (all templates)
□ Add quick view modal
□ Implement pull-to-refresh
□ Add loading states and error handling

DELIVERABLE: Users can browse and search products efficiently
```

### Day 9-10: Chat Integration (First-Class Feature)
```typescript
TASK 6: AI Chat Assistant
□ Setup WebSocket connection manager
□ Create chat UI component
□ Implement message threading
□ Add typing indicators
□ Integrate product recommendations
□ Add voice input button
□ Implement chat persistence
□ Create floating chat bubble
□ Test reconnection logic

DELIVERABLE: Fully functional AI chat with voice
```

### Day 11-12: Shopping Cart
```typescript
TASK 7: Cart Management
□ Create cart store
□ Implement add to cart functionality
□ Build cart screen UI
□ Add quantity adjustments
□ Implement cart persistence
□ Add promotion code input
□ Calculate taxes and totals
□ Add cart badge to navigation

DELIVERABLE: Complete cart functionality
```

### Day 13-14: Checkout Flow
```typescript
TASK 8: Streamlined Checkout
□ Create single-page checkout screen
□ Implement address selection/input
□ Add delivery/pickup toggle
□ Integrate delivery fee calculation
□ Build payment method selector
□ Add order summary
□ Implement order creation
□ Create confirmation screen

DELIVERABLE: 3-tap checkout process
```

### Day 15-16: Payment Integration
```typescript
TASK 9: Clover Go Integration
□ Install Clover SDK
□ Implement card reader pairing
□ Create payment flow UI
□ Handle payment states
□ Add digital wallet support
□ Implement receipt generation
□ Test with sandbox
□ Add payment error handling

DELIVERABLE: Working payment processing
```

### Day 17-18: Order Management
```typescript
TASK 10: Order Tracking
□ Create orders list screen
□ Build order detail view
□ Implement status timeline
□ Add delivery tracking map
□ Setup push notifications
□ Add reorder functionality
□ Implement order history search

DELIVERABLE: Complete order management
```

### Day 19-20: Voice Features
```typescript
TASK 11: Voice Integration
□ Setup Expo.Audio permissions
□ Implement push-to-talk recording
□ Integrate speech-to-text API
□ Add voice search
□ Implement TTS responses
□ Create voice command parser
□ Add accessibility features
□ Test on both platforms

DELIVERABLE: Voice-enabled interactions
```

### Day 21-22: Profile & Settings
```typescript
TASK 12: User Profile
□ Create profile screen
□ Implement address management
□ Add payment method management
□ Build preferences screen
□ Create wishlist functionality
□ Add medical docs upload
□ Implement logout flow

DELIVERABLE: Complete profile management
```

### Day 23-24: Optimization
```typescript
TASK 13: Performance & Polish
□ Implement image optimization
□ Add skeleton screens
□ Optimize bundle size
□ Implement code splitting
□ Add haptic feedback
□ Polish animations
□ Implement offline queue
□ Add crash reporting

DELIVERABLE: Smooth, polished experience
```

## Quality Checkpoints

### After Each Task Completion
```bash
CHECKLIST:
□ Feature works end-to-end
□ Error states handled gracefully
□ Loading states implemented
□ Offline behavior acceptable
□ Accessibility tested
□ Both iOS and Android tested
□ Memory leaks checked
□ Performance acceptable
```

### API Integration Checklist
```typescript
FOR EACH API ENDPOINT:
□ TypeScript types defined
□ Error responses handled
□ Loading states shown
□ Success feedback provided
□ Retry logic implemented
□ Timeout handling added
□ Response cached if appropriate
```

### Component Development Pattern
```typescript
// ALWAYS follow this pattern for new components

// 1. Define Props Interface
interface ComponentProps {
  // Strongly typed props
}

// 2. Create Component with Template Support
const Component: FC<ComponentProps> = (props) => {
  const template = useTemplate();

  // 3. Add loading and error states
  if (loading) return <Skeleton />;
  if (error) return <ErrorView />;

  // 4. Implement template-specific rendering
  return template.components.Component(props);
};

// 5. Export with memo for performance
export default memo(Component);
```

## Testing Protocol

### Component Testing
```typescript
// Test each component in isolation
describe('ProductCard', () => {
  it('renders product information correctly');
  it('handles add to cart action');
  it('shows loading state');
  it('handles error state');
  it('works with all templates');
});
```

### Integration Testing
```typescript
// Test complete user flows
describe('Purchase Flow', () => {
  it('allows product browsing');
  it('adds items to cart');
  it('completes checkout');
  it('processes payment');
  it('shows order confirmation');
});
```

### API Testing
```typescript
// Verify all API integrations
describe('API Services', () => {
  it('authenticates successfully');
  it('refreshes tokens automatically');
  it('handles network errors');
  it('queues offline requests');
  it('validates responses');
});
```

## Continuous Improvement Cycle

### Daily Routine
```
MORNING:
1. Review previous day's work
2. Test on both platforms
3. Fix any overnight issues
4. Plan day's tasks

DEVELOPMENT:
1. Implement one complete feature
2. Test thoroughly
3. Commit with clear message
4. Update documentation

EVENING:
1. Run full test suite
2. Check performance metrics
3. Review code quality
4. Plan next day
```

### Weekly Reviews
```
EVERY FRIDAY:
□ Demo to stakeholders
□ Gather feedback
□ Update roadmap
□ Performance audit
□ Security review
□ Accessibility check
□ Update dependencies
```

## Problem Resolution Framework

### When Stuck on API Integration
```typescript
1. Check API documentation
2. Test endpoint with Postman/curl
3. Verify authentication headers
4. Check request/response format
5. Look for similar working code
6. Add detailed logging
7. Check network inspector
```

### When Performance Issues Arise
```typescript
1. Profile with React DevTools
2. Check render counts
3. Identify heavy computations
4. Implement memoization
5. Lazy load components
6. Optimize images
7. Reduce bundle size
```

### When UI Doesn't Match Design
```typescript
1. Compare with template specs
2. Check theme values
3. Verify component props
4. Test on different devices
5. Adjust responsive breakpoints
6. Get designer feedback
```

## Git Workflow

### Branch Strategy
```bash
main
├── develop
│   ├── feature/auth-flow
│   ├── feature/chat-integration
│   ├── feature/payment-processing
│   └── feature/voice-commands
└── release/v1.0.0
```

### Commit Messages
```bash
# Format: <type>(<scope>): <subject>

feat(auth): implement OTP verification
fix(cart): resolve quantity update issue
perf(products): optimize image loading
docs(api): update endpoint documentation
test(checkout): add payment flow tests
```

## Definition of Done

### Feature Complete Checklist
```
A feature is DONE when:
□ All acceptance criteria met
□ API integration working
□ Error handling complete
□ Loading states implemented
□ Tested on iOS and Android
□ Accessibility verified
□ Performance acceptable
□ Documentation updated
□ Code reviewed
□ Tests passing
```

## Success Metrics Tracking

### Daily Metrics
```typescript
Track and Log:
- Features completed
- Bugs fixed
- Test coverage %
- Build success rate
- Crash-free sessions
```

### Weekly Metrics
```typescript
Review:
- User flow completion rates
- API response times
- App launch time
- Memory usage trends
- User feedback scores
```

## Emergency Procedures

### If API is Down
```typescript
1. Implement offline mode immediately
2. Cache critical data locally
3. Queue user actions
4. Show appropriate messages
5. Auto-retry when connection restored
```

### If Payment Fails
```typescript
1. Log complete error details
2. Show user-friendly message
3. Offer alternative payment
4. Save cart for retry
5. Contact support option
```

### If Chat Disconnects
```typescript
1. Auto-reconnect silently
2. Queue unsent messages
3. Preserve chat history
4. Show connection status
5. Fallback to HTTP if needed
```

## Final Launch Preparation

### Pre-Launch Checklist
```
TWO WEEKS BEFORE:
□ Feature freeze
□ Focus on bug fixes only
□ Extensive testing
□ Performance optimization
□ Security audit

ONE WEEK BEFORE:
□ App store assets ready
□ Marketing materials prepared
□ Support documentation complete
□ Beta feedback incorporated
□ Final builds created

LAUNCH DAY:
□ Monitor crash reports
□ Track user analytics
□ Respond to reviews
□ Hot-fix if critical
□ Celebrate success!
```

## Continuous Learning

### Stay Updated
- Review API changes weekly
- Update dependencies monthly
- Learn new Expo features
- Study user analytics
- Gather team feedback
- Improve based on metrics

### Knowledge Sharing
- Document all decisions
- Create component library
- Share code patterns
- Write test examples
- Update team wiki
- Conduct code reviews

This systematic workflow ensures consistent progress, high quality, and successful delivery of the WeedGo mobile application.