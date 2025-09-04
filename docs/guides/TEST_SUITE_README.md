# WeedGo AI Engine Test Suite

## Overview
Comprehensive .NET 9 test suite for the WeedGo AI Engine API to ensure reliability and catch regressions.

## Test Coverage

### 1. Direct Product Request Tests (`DirectProductRequestTests.cs`)
- ✅ **Should_Return_Products_For_Direct_Sativa_Joint_Request**: Tests the main fix - direct product requests skip qualification
- **Should_Parse_Budget_Under_Pattern**: Validates "under $X" budget parsing
- **Should_Recognize_Joint_As_Flower_Product**: Ensures joints map to flower category
- **Should_Handle_Multiple_Criteria**: Tests complex requests with multiple filters

### 2. Age Verification Tests (`AgeVerificationTests.cs`)
- **Should_Require_Age_Verification_For_New_Users**: Unverified users blocked
- **Should_Allow_Verified_Users_To_See_Products**: Verified users get products
- **Should_Persist_Verification_Across_Sessions**: Database persistence test
- **Should_Allow_Guest_Users_Limited_Access**: Guest user handling

### 3. Conversation Flow Tests (`ConversationFlowTests.cs`)
- **Should_Not_Get_Stuck_In_Qualification_Loop**: Tests the qualification loop bug fix
- **Should_Progress_Through_Stages_Naturally**: Natural stage progression
- **Should_Skip_To_Recommendation_For_Direct_Requests**: Direct-to-recommendation path
- **Should_Remember_Customer_Context**: Context persistence in session

### 4. Parsing Tests (`ParsingTests.cs`)
- **Should_Parse_Single_Budget_Values**: Tests "under $X", "less than $Y" patterns
- **Should_Parse_Budget_Ranges**: Tests "$X to $Y" range patterns
- **Should_Parse_Strain_Types**: Validates sativa/indica/hybrid recognition
- **Should_Parse_Product_Types**: Tests joint/flower/vape/edible parsing
- **Should_Parse_Complex_Requests**: Multi-criteria request handling

## Running Tests

### Quick Test
```bash
# Run a specific test
dotnet test --filter "Should_Return_Products_For_Direct_Sativa_Joint_Request"
```

### Full Suite
```bash
# Run all tests with the provided script
./run-tests.sh
```

### Manual Testing
```bash
# 1. Ensure API is running
python3 api_server.py

# 2. In another terminal, run tests
cd AIEngineTests
dotnet test
```

## Test Architecture

### Models (`Models/ChatModels.cs`)
- C# models with JSON serialization attributes for snake_case compatibility
- Matches Python API request/response formats exactly

### API Client (`Helpers/AIEngineApiClient.cs`)
- Reusable HTTP client for API interactions
- Handles age verification and chat endpoints
- Automatic health check with retry logic

### Test Fixture (`Tests/ApiTestFixture.cs`)
- Shared setup for all test classes
- Waits for API to be ready before tests run
- Configurable via `AI_ENGINE_API_URL` environment variable

## CI/CD Integration

GitHub Actions workflow (`.github/workflows/test-ai-engine.yml`):
- Runs on push to main/develop branches
- Sets up PostgreSQL and Redis services
- Executes full test suite
- Publishes test results as artifacts

## Key Test Scenarios

### The Original Bug (Customer 0001)
```csharp
// This exact scenario is tested
var request = new ChatRequest
{
    Message = "3 joint sativa under 10$",
    CustomerId = "0001",
    SessionId = "test"
};

// Before fix: Stage = "qualification", Message = "What methods have you tried..."
// After fix: Stage = "recommendation", Products returned
```

### Direct Product Recognition
- "I want sativa" → Skip qualification
- "3 joints under $10" → Return matching products
- "Show me indica flower" → Direct to recommendations

### Budget Parsing
- "under 10$" → max_price = 10
- "$20 to $40" → price range 20-40
- "less than 15 dollars" → max_price = 15

## Success Criteria

All tests should pass when:
1. API recognizes direct product requests
2. Skips qualification for specific requests
3. Correctly parses budget constraints
4. Maintains age verification persistence
5. Returns appropriate products based on filters

## Troubleshooting

### Test Failures
1. Check API is running: `curl http://localhost:8080/health`
2. Verify database has products: Check PostgreSQL
3. Ensure Redis cache is running: Port 6381
4. Check models match API response format

### Common Issues
- **JSON Deserialization**: Ensure all models have `[JsonProperty]` attributes
- **API Not Ready**: Increase timeout in `ApiTestFixture`
- **Database Empty**: Run data loading scripts first

## Future Enhancements
- Performance benchmarks
- Load testing
- Error scenario coverage
- Multi-tenant testing
- Integration with monitoring