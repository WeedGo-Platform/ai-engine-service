// Test script to verify replay functionality with correct API endpoints

async function testReplayFixed() {
  console.log('Testing replay functionality with correct API endpoints...\n');
  
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
  
  // 2. Extract customer messages (using correct field names)
  const customerMessages = conversation.messages.filter(m => m.sender === 'customer');
  console.log(`\n2. Customer messages to replay: ${customerMessages.length}`);
  customerMessages.forEach((msg, idx) => {
    console.log(`   Message ${idx + 1}: "${msg.message?.substring(0, 50)}..."`);
  });
  
  // 3. Simulate replay - send each message to AI
  console.log('\n3. Starting replay simulation...');
  const replayResults = [];
  
  for (let i = 0; i < customerMessages.length; i++) {
    const msg = customerMessages[i];
    console.log(`\n   Replaying message ${i + 1}/${customerMessages.length}...`);
    
    try {
      const response = await fetch('http://localhost:8080/api/v1/chat', {
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
      
      // Find original response (next message after customer message)
      const msgIndex = conversation.messages.indexOf(msg);
      const originalResponse = conversation.messages[msgIndex + 1];
      
      console.log('   ✓ Got new response');
      console.log(`   Original: "${originalResponse?.message?.substring(0, 50)}..."`);
      console.log(`   New:      "${data.message?.substring(0, 50)}..."`);
      console.log(`   Confidence: ${(data.confidence * 100).toFixed(1)}%`);
      console.log(`   Response time: ${data.response_time_ms}ms`);
      
      // Calculate similarity
      const originalText = originalResponse?.message || '';
      const newText = data.message || '';
      const similarity = calculateSimilarity(originalText, newText);
      
      console.log(`   Similarity: ${similarity.toFixed(1)}%`);
      
      if (similarity === 100) {
        console.log('   → Responses are identical');
      } else if (similarity > 80) {
        console.log('   → Responses are very similar (minor changes)');
      } else if (similarity > 50) {
        console.log('   → Responses differ moderately (AI has evolved)');
      } else {
        console.log('   → Responses are significantly different (major learning)');
      }
      
      replayResults.push({
        userMessage: msg.message,
        originalResponse: originalResponse?.message,
        newResponse: data.message,
        confidence: data.confidence,
        responseTime: data.response_time_ms,
        similarity
      });
      
    } catch (error) {
      console.error(`   ✗ Error replaying message: ${error.message}`);
    }
    
    // Wait a bit between messages
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  // 4. Summary
  console.log('\n4. Replay Summary:');
  console.log('   Total messages replayed:', replayResults.length);
  
  if (replayResults.length > 0) {
    const avgSimilarity = replayResults.reduce((acc, r) => acc + r.similarity, 0) / replayResults.length;
    const avgConfidence = replayResults.reduce((acc, r) => acc + r.confidence, 0) / replayResults.length;
    const avgResponseTime = replayResults.reduce((acc, r) => acc + r.responseTime, 0) / replayResults.length;
    
    console.log(`   Average similarity: ${avgSimilarity.toFixed(1)}%`);
    console.log(`   Average confidence: ${(avgConfidence * 100).toFixed(1)}%`);
    console.log(`   Average response time: ${avgResponseTime.toFixed(0)}ms`);
    
    if (avgSimilarity < 100) {
      console.log('\n   🎯 AI Model has evolved since original conversation!');
    }
  }
  
  console.log('\n✅ Replay test complete!');
  return replayResults;
}

// Simple similarity calculation (Jaccard similarity)
function calculateSimilarity(text1, text2) {
  if (!text1 || !text2) return 0;
  
  const words1 = new Set(text1.toLowerCase().split(/\s+/));
  const words2 = new Set(text2.toLowerCase().split(/\s+/));
  
  const intersection = new Set([...words1].filter(x => words2.has(x)));
  const union = new Set([...words1, ...words2]);
  
  return (intersection.size / union.size) * 100;
}

// Run the test
testReplayFixed().catch(console.error);