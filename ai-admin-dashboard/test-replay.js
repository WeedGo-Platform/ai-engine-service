// Test script to verify replay functionality with database data

async function testReplay() {
  console.log('Testing replay functionality...\n');
  
  // 1. Fetch conversations from database
  console.log('1. Fetching conversations from database...');
  const conversationsResponse = await fetch('http://localhost:8080/api/v1/conversations/history?limit=5');
  const conversationsData = await conversationsResponse.json();
  
  if (conversationsData.conversations.length === 0) {
    console.error('No conversations found in database!');
    return;
  }
  
  const conversation = conversationsData.conversations[0];
  console.log(`   Found conversation: ${conversation.session_id}`);
  console.log(`   Total messages: ${conversation.messages.length}`);
  
  // 2. Extract customer messages
  const customerMessages = conversation.messages.filter(m => m.sender === 'customer');
  console.log(`\n2. Customer messages to replay: ${customerMessages.length}`);
  customerMessages.forEach((msg, idx) => {
    console.log(`   Message ${idx + 1}: "${msg.message?.substring(0, 50)}..."`);
  });
  
  // 3. Simulate replay - send each message to AI
  console.log('\n3. Starting replay simulation...');
  for (let i = 0; i < customerMessages.length; i++) {
    const msg = customerMessages[i];
    console.log(`\n   Replaying message ${i + 1}/${customerMessages.length}...`);
    
    try {
      const response = await fetch('http://localhost:8080/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: msg.message,
          session_id: `replay_${conversation.session_id}_${Date.now()}`,
          customer_id: `replay_test`,
          context: {
            mode: 'replay',
            original_session_id: conversation.session_id
          }
        })
      });
      
      const data = await response.json();
      
      // Find original response
      const msgIndex = conversation.messages.indexOf(msg);
      const originalResponse = conversation.messages[msgIndex + 1];
      
      console.log('   ✓ Got new response');
      console.log(`   Original: "${originalResponse?.message?.substring(0, 50)}..."`);
      console.log(`   New:      "${data.response?.substring(0, 50)}..."`);
      console.log(`   Confidence: ${(data.confidence * 100).toFixed(1)}%`);
      console.log(`   Response time: ${data.processing_time_ms}ms`);
      
      // Simple diff check
      if (originalResponse?.message === data.response) {
        console.log('   → Responses are identical');
      } else {
        console.log('   → Responses differ (AI has evolved!)');
      }
      
    } catch (error) {
      console.error(`   ✗ Error replaying message: ${error.message}`);
    }
    
    // Wait a bit between messages
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  console.log('\n✅ Replay test complete!');
}

// Run the test
testReplay().catch(console.error);