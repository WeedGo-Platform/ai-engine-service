// Test the API endpoints directly
const API_BASE_URL = 'http://localhost:8080';

async function testAPI() {
  console.log('Testing API endpoints...\n');
  
  // Test conversations endpoint
  try {
    const convResponse = await fetch(`${API_BASE_URL}/api/v1/conversations/history?limit=5`);
    const convData = await convResponse.json();
    console.log('Conversations endpoint:');
    console.log('- Status:', convResponse.status);
    console.log('- Number of conversations:', convData.conversations?.length || 0);
    console.log('- First conversation:', convData.conversations?.[0] ? 'Available' : 'None');
    console.log('');
  } catch (err) {
    console.error('Failed to fetch conversations:', err.message);
  }
  
  // Test training examples endpoint  
  try {
    const trainResponse = await fetch(`${API_BASE_URL}/api/v1/ai/training-examples?limit=5`);
    const trainData = await trainResponse.json();
    console.log('Training examples endpoint:');
    console.log('- Status:', trainResponse.status);
    console.log('- Number of examples:', trainData.examples?.length || 0);
    console.log('- First example:', trainData.examples?.[0] ? 'Available' : 'None');
    console.log('');
  } catch (err) {
    console.error('Failed to fetch training examples:', err.message);
  }
  
  console.log('Test complete!');
}

testAPI();