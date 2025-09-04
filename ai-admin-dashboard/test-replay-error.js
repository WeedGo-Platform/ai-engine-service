// Test script to simulate AI service unavailability during replay

import fetch from 'node-fetch';

async function testReplayWithError() {
  console.log('Testing replay with AI service error simulation...\n');
  
  // 1. Fetch a conversation to replay
  console.log('1. Fetching conversation from database...');
  const conversationsResponse = await fetch('http://localhost:8080/api/v1/conversations/history?limit=1');
  const conversationsData = await conversationsResponse.json();
  
  if (!conversationsData.conversations || conversationsData.conversations.length === 0) {
    console.error('No conversations found in database!');
    return;
  }
  
  const conversation = conversationsData.conversations[0];
  console.log(`   Found conversation: ${conversation.session_id}`);
  
  // Extract customer messages
  const customerMessages = conversation.messages.filter(m => m.sender === 'customer');
  console.log(`   Customer messages to replay: ${customerMessages.length}`);
  
  if (customerMessages.length === 0) {
    console.error('No customer messages found!');
    return;
  }
  
  console.log('\n2. Testing replay with API errors...\n');
  
  // Test 1: Simulate network error
  console.log('Test 1: Network error (wrong port)...');
  try {
    const response = await fetch('http://localhost:9999/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: customerMessages[0].message,
        session_id: `replay_test_${Date.now()}`,
        customer_id: 'test_user'
      })
    });
    console.log('   Unexpected success!');
  } catch (error) {
    console.log('   ✓ Network error caught:', error.code || error.message);
    console.log('   ✓ This should display error message in chat window');
  }
  
  // Test 2: Simulate 500 error (if we had a way to trigger it)
  console.log('\nTest 2: Invalid API endpoint (404)...');
  try {
    const response = await fetch('http://localhost:8080/api/v1/chat_invalid', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: customerMessages[0].message,
        session_id: `replay_test_${Date.now()}`,
        customer_id: 'test_user'
      })
    });
    
    if (!response.ok) {
      console.log(`   ✓ HTTP error: ${response.status} ${response.statusText}`);
      console.log('   ✓ This should display error message in chat window');
    }
  } catch (error) {
    console.log('   ✓ Error caught:', error.message);
  }
  
  // Test 3: Malformed request
  console.log('\nTest 3: Malformed request (missing required fields)...');
  try {
    const response = await fetch('http://localhost:8080/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        // Missing 'message' field
        session_id: `replay_test_${Date.now()}`
      })
    });
    
    const data = await response.json();
    if (!response.ok || data.error) {
      console.log(`   ✓ Validation error: ${data.detail || data.error || response.statusText}`);
      console.log('   ✓ This should display error message in chat window');
    }
  } catch (error) {
    console.log('   ✓ Error caught:', error.message);
  }
  
  console.log('\n3. Expected UI behavior:');
  console.log('   - Loading indicator should be removed');
  console.log('   - Error message should appear in chat as AI response');
  console.log('   - Message should say: "Sorry, I encountered an error..."');
  console.log('   - Replay should continue to next message after pause');
  console.log('   - No toast notification for each error (only network errors)');
  
  console.log('\n✅ Error handling test scenarios complete!');
  console.log('\nTo fully test:');
  console.log('1. Stop the API server (Ctrl+C in the terminal running api_server.py)');
  console.log('2. Click "Start Replay" in the UI');
  console.log('3. Observe error messages appearing in chat window');
  console.log('4. Restart API server to restore normal functionality');
}

// Run the test
testReplayWithError().catch(console.error);