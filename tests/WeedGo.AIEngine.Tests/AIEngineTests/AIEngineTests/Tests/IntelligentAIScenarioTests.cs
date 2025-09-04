using Xunit;
using FluentAssertions;
using AIEngineTests.Helpers;
using AIEngineTests.Models;
using System.Linq;
using System.Text.Json;

namespace AIEngineTests.Tests;

/// <summary>
/// Intelligent AI-driven test suite that validates behavior patterns
/// rather than exact string matches. Tests natural language understanding,
/// context awareness, learning, and sales closure capabilities.
/// </summary>
public class IntelligentAIScenarioTests : IClassFixture<ApiTestFixture>
{
    private readonly AIEngineApiClient _client;
    
    public IntelligentAIScenarioTests(ApiTestFixture fixture)
    {
        _client = fixture.Client;
    }
    
    private async Task VerifyUser(string customerId)
    {
        var verifyRequest = new AgeVerificationRequest
        {
            CustomerId = customerId,
            BirthDate = "1990-01-01",
            VerificationMethod = "government_id"
        };
        await _client.VerifyAgeAsync(verifyRequest);
    }
    
    #region 1. Conversation Memory & Context Tests
    
    [Fact]
    public async Task Should_Remember_Previous_Conversation_Context()
    {
        // Arrange
        var customerId = "test_memory_" + Guid.NewGuid().ToString("N");
        var sessionId = "memory_test_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        // Act - First interaction: Customer mentions preference
        var request1 = new ChatRequest
        {
            Message = "I prefer indica strains for nighttime use",
            CustomerId = customerId,
            SessionId = sessionId
        };
        
        var response1 = await _client.SendChatMessageAsync(request1);
        
        // Second interaction: Ask for recommendation without repeating preference
        var request2 = new ChatRequest
        {
            Message = "what do you recommend?",
            CustomerId = customerId,
            SessionId = sessionId
        };
        
        var response2 = await _client.SendChatMessageAsync(request2);
        
        // Assert - AI should remember indica preference
        response2.Should().NotBeNull();
        
        // Check if recommendations are indica or mention nighttime/relaxation
        if (response2.Products.Any())
        {
            var indicaProducts = response2.Products.Where(p => 
                p.Name.ToLower().Contains("indica") ||
                p.Description?.ToLower().Contains("indica") == true ||
                p.Description?.ToLower().Contains("relax") == true ||
                p.Description?.ToLower().Contains("night") == true);
            
            indicaProducts.Should().NotBeEmpty("AI should remember indica preference from previous message");
        }
        
        // Or check if message acknowledges the preference
        var messageIndicatesMemory = MessageContainsAny(response2.Message,
            new[] { "indica", "nighttime", "relax", "sleep", "evening" });
        
        messageIndicatesMemory.Should().BeTrue("AI should show it remembers the customer's preference");
    }
    
    [Fact]
    public async Task Should_Build_Customer_Profile_Over_Multiple_Sessions()
    {
        // Arrange
        var customerId = "test_profile_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        // Act - Multiple sessions building profile
        // Session 1: Price preference
        var session1 = "session1_" + Guid.NewGuid().ToString("N");
        var request1 = new ChatRequest
        {
            Message = "I usually spend around $30-40",
            CustomerId = customerId,
            SessionId = session1
        };
        await _client.SendChatMessageAsync(request1);
        
        // Session 2: Product type preference
        var session2 = "session2_" + Guid.NewGuid().ToString("N");
        var request2 = new ChatRequest
        {
            Message = "I prefer pre-rolls over flower",
            CustomerId = customerId,
            SessionId = session2
        };
        await _client.SendChatMessageAsync(request2);
        
        // Session 3: Ask for recommendation
        var session3 = "session3_" + Guid.NewGuid().ToString("N");
        var request3 = new ChatRequest
        {
            Message = "what's good today?",
            CustomerId = customerId,
            SessionId = session3
        };
        
        var response3 = await _client.SendChatMessageAsync(request3);
        
        // Assert - Should consider accumulated preferences
        response3.Should().NotBeNull();
        
        if (response3.Products.Any())
        {
            // Check if products align with learned preferences
            var matchingPreferences = response3.Products.Where(p =>
                (p.Price >= 30 && p.Price <= 50) || // Price range with some flexibility
                p.Category == "Pre-Rolls" ||
                p.Name.ToLower().Contains("pre-roll"));
            
            matchingPreferences.Should().NotBeEmpty(
                "AI should consider customer's accumulated preferences across sessions");
        }
    }
    
    #endregion
    
    #region 2. Natural Language Interaction Tests
    
    [Theory]
    [InlineData("I'm feeling anxious and need something to calm down")]
    [InlineData("got anything for creativity and focus?")]
    [InlineData("I want to party tonight, what's good?")]
    [InlineData("need pain relief but don't want to get too high")]
    public async Task Should_Understand_Natural_Language_Needs(string naturalQuery)
    {
        // Arrange
        var customerId = "test_natural_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = naturalQuery,
            CustomerId = customerId,
            SessionId = "natural_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert - Should provide relevant recommendations
        response.Should().NotBeNull();
        response.Stage.Should().NotBe("error", "Should understand natural language");
        
        // Response should acknowledge the need
        if (naturalQuery.Contains("anxious"))
        {
            var hasRelevantResponse = MessageContainsAny(response.Message,
                new[] { "calm", "relax", "anxiety", "stress", "indica" });
            hasRelevantResponse.Should().BeTrue("Should acknowledge anxiety relief need");
        }
        else if (naturalQuery.Contains("creativity"))
        {
            var hasRelevantResponse = MessageContainsAny(response.Message,
                new[] { "creative", "focus", "sativa", "energiz", "uplift" });
            hasRelevantResponse.Should().BeTrue("Should acknowledge creativity need");
        }
        else if (naturalQuery.Contains("party"))
        {
            var hasRelevantResponse = MessageContainsAny(response.Message,
                new[] { "social", "energy", "fun", "sativa", "hybrid" });
            hasRelevantResponse.Should().BeTrue("Should acknowledge party/social need");
        }
        else if (naturalQuery.Contains("pain"))
        {
            var hasRelevantResponse = MessageContainsAny(response.Message,
                new[] { "pain", "relief", "cbd", "relax", "indica" });
            hasRelevantResponse.Should().BeTrue("Should acknowledge pain relief need");
        }
    }
    
    [Fact]
    public async Task Should_Handle_Conversational_Flow_Naturally()
    {
        // Arrange
        var customerId = "test_flow_" + Guid.NewGuid().ToString("N");
        var sessionId = "flow_test_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        // Act - Natural conversation flow
        var conversation = new[]
        {
            "hey there",
            "I'm new to this",
            "what's the difference between sativa and indica?",
            "okay, I think I want something energizing",
            "how much should I take as a beginner?",
            "sounds good, I'll try that"
        };
        
        ChatResponse? lastResponse = null;
        foreach (var message in conversation)
        {
            var request = new ChatRequest
            {
                Message = message,
                CustomerId = customerId,
                SessionId = sessionId
            };
            
            lastResponse = await _client.SendChatMessageAsync(request);
            
            // Each response should be contextually appropriate
            lastResponse!.Should().NotBeNull();
            lastResponse.Message.Should().NotBeNullOrWhiteSpace();
            lastResponse.Confidence.Should().BeGreaterThan(0);
        }
        
        // Final response should show progression through conversation
        lastResponse!.Stage.Should().NotBe("greeting", 
            "Conversation should have progressed beyond greeting");
    }
    
    #endregion
    
    #region 3. Intent & Entity Extraction Tests
    
    [Theory]
    [InlineData("I want pink kush 3.5g", "pink kush", 3.5, "", "")]
    [InlineData("show me $20 sativa pre-rolls", "", null, "Pre-Rolls", "sativa")]
    [InlineData("eighth of something fruity", "", 3.5, "", "")]
    [InlineData("high THC indica under $50", "", null, "", "indica")]
    public async Task Should_Extract_Product_Entities_From_Query(
        string query, string expectedProduct, double? expectedSize, 
        string expectedCategory, string expectedStrain)
    {
        // Arrange
        var customerId = "test_extract_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = query,
            CustomerId = customerId,
            SessionId = "extract_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert - Check if correct entities were extracted
        response.Should().NotBeNull();
        
        if (!string.IsNullOrEmpty(expectedProduct) && response.Products.Any())
        {
            response.Products.Should().Contain(p => 
                p.Name.ToLower().Contains(expectedProduct.ToLower()),
                $"Should find products matching '{expectedProduct}'");
        }
        
        if (expectedSize.HasValue)
        {
            // Check if size was understood (in message or product selection)
            var sizeUnderstood = response.Message.Contains(expectedSize.ToString()) ||
                                response.Products.Any(p => p.Name.Contains($"{expectedSize}g"));
            sizeUnderstood.Should().BeTrue($"Should understand size {expectedSize}g");
        }
        
        if (!string.IsNullOrEmpty(expectedCategory) && response.Products.Any())
        {
            response.Products.Should().Contain(p => 
                p.Category == expectedCategory,
                $"Should filter by category {expectedCategory}");
        }
        
        if (!string.IsNullOrEmpty(expectedStrain))
        {
            var strainUnderstood = response.Message.ToLower().Contains(expectedStrain) ||
                                  response.Products.Any(p => 
                                      p.Name.ToLower().Contains(expectedStrain) ||
                                      p.Description?.ToLower().Contains(expectedStrain.ToLower()) == true);
            strainUnderstood.Should().BeTrue($"Should understand strain type {expectedStrain}");
        }
    }
    
    [Fact]
    public async Task Should_Infer_Intent_From_Indirect_Statements()
    {
        // Arrange
        var testCases = new[]
        {
            ("I can't sleep at night", "sleep_aid"),
            ("I need to clean my whole house", "energy"),
            ("going to a concert tonight", "social"),
            ("my back is killing me", "pain_relief"),
            ("want to watch movies and chill", "relaxation")
        };
        
        foreach (var (statement, expectedIntent) in testCases)
        {
            var customerId = "test_infer_" + Guid.NewGuid().ToString("N");
            await VerifyUser(customerId);
            
            var request = new ChatRequest
            {
                Message = statement,
                CustomerId = customerId,
                SessionId = "infer_test"
            };
            
            // Act
            var response = await _client.SendChatMessageAsync(request);
            
            // Assert - Check if intent was properly inferred
            response.Should().NotBeNull();
            
            switch (expectedIntent)
            {
                case "sleep_aid":
                    var sleepTerms = new[] { "sleep", "indica", "relax", "night", "rest" };
                    MessageContainsAny(response.Message, sleepTerms).Should().BeTrue("Should mention sleep-related terms");
                    break;
                    
                case "energy":
                    var energyTerms = new[] { "energy", "sativa", "active", "focus", "motivat" };
                    MessageContainsAny(response.Message, energyTerms).Should().BeTrue("Should mention energy-related terms");
                    break;
                    
                case "social":
                    var socialTerms = new[] { "social", "hybrid", "enjoy", "fun", "euphori" };
                    MessageContainsAny(response.Message, socialTerms).Should().BeTrue("Should mention social-related terms");
                    break;
                    
                case "pain_relief":
                    var painTerms = new[] { "pain", "relief", "cbd", "help", "sooth" };
                    MessageContainsAny(response.Message, painTerms).Should().BeTrue("Should mention pain relief terms");
                    break;
                    
                case "relaxation":
                    var relaxTerms = new[] { "relax", "chill", "calm", "mellow", "unwind" };
                    MessageContainsAny(response.Message, relaxTerms).Should().BeTrue("Should mention relaxation terms");
                    break;
            }
        }
    }
    
    #endregion
    
    #region 4. Sales Closure & Recommendation Tests
    
    [Fact]
    public async Task Should_Guide_Customer_To_Product_Selection()
    {
        // Arrange
        var customerId = "test_closure_" + Guid.NewGuid().ToString("N");
        var sessionId = "closure_test_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        // Simulate indecisive customer
        var conversation = new[]
        {
            "I want something good",
            "not sure what though",
            "what do most people get?",
            "hmm, maybe something else?",
            "okay what about the first one?"
        };
        
        int productsSuggested = 0;
        ChatResponse? lastResponse = null;
        
        foreach (var message in conversation)
        {
            var request = new ChatRequest
            {
                Message = message,
                CustomerId = customerId,
                SessionId = sessionId
            };
            
            lastResponse = await _client.SendChatMessageAsync(request);
            
            if (lastResponse.Products.Any())
            {
                productsSuggested++;
            }
        }
        
        // Assert - Should actively try to close the sale
        productsSuggested.Should().BeGreaterThan(0, 
            "Should suggest products to help customer decide");
        
        // Should show persistence in helping customer decide
        lastResponse!.Should().NotBeNull();
        var closingIndicators = new[] { "great choice", "excellent", "add", "cart", "try", "recommend" };
        MessageContainsAny(lastResponse!.Message, closingIndicators).Should().BeTrue(
            "Should use closing language to encourage purchase");
    }
    
    [Fact]
    public async Task Should_Provide_Smart_Recommendations_With_Alternatives()
    {
        // Arrange
        var customerId = "test_recommend_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        // Customer asks for specific product with size
        var request = new ChatRequest
        {
            Message = "do you have blue dream 3.5g?",
            CustomerId = customerId,
            SessionId = "recommend_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        
        if (response.Products.Any())
        {
            // Should include exact match if available
            var exactMatch = response.Products.FirstOrDefault(p => 
                p.Name.ToLower().Contains("blue dream"));
            
            // Should also include alternatives
            if (response.Products.Count > 1)
            {
                // Alternatives should be similar (same category, similar effects, or price)
                var alternatives = response.Products.Where(p => p != exactMatch);
                
                alternatives.Should().NotBeEmpty("Should provide alternatives");
                
                // Verify alternatives are reasonable (similar category or type)
                if (exactMatch != null)
                {
                    alternatives.Should().Contain(p => 
                        p.Category == exactMatch.Category ||
                        Math.Abs(p.Price - exactMatch.Price) < 20,
                        "Alternatives should be similar in category or price");
                }
            }
        }
        
        // Message should explain recommendations
        response.Message.Should().NotBeNullOrWhiteSpace();
        var hasRecommendationLanguage = MessageContainsAny(response.Message,
            new[] { "also", "similar", "like", "recommend", "try", "alternative" });
        
        if (response.Products.Count > 1)
        {
            hasRecommendationLanguage.Should().BeTrue(
                "Should explain why alternatives are being shown");
        }
    }
    
    #endregion
    
    #region 5. Learning & Training Validation Tests
    
    [Fact]
    public async Task Should_Improve_Accuracy_With_Feedback()
    {
        // This test validates that the system can accept and learn from feedback
        // In a real implementation, this would train the model
        
        var customerId = "test_learning_" + Guid.NewGuid().ToString("N");
        var sessionId = "learning_test";
        await VerifyUser(customerId);
        
        // First attempt - might not be perfect
        var request1 = new ChatRequest
        {
            Message = "I want something with terpenes for flavor",
            CustomerId = customerId,
            SessionId = sessionId
        };
        
        var response1 = await _client.SendChatMessageAsync(request1);
        
        // Simulate feedback (in real system, this would be a training endpoint)
        // Customer indicates they wanted something specific
        var request2 = new ChatRequest
        {
            Message = "no, I meant something with citrus terpenes specifically",
            CustomerId = customerId,
            SessionId = sessionId
        };
        
        var response2 = await _client.SendChatMessageAsync(request2);
        
        // Assert - Should show learning/correction
        response2.Should().NotBeNull();
        MessageContainsAny(response2.Message,
            new[] { "citrus", "lemon", "limonene", "orange", "tangie" }).Should().BeTrue(
            "Should understand the correction and provide citrus-focused recommendations");
        
        // Future similar request should be better
        var request3 = new ChatRequest
        {
            Message = "show me more terpene-rich options",
            CustomerId = customerId,
            SessionId = sessionId
        };
        
        var response3 = await _client.SendChatMessageAsync(request3);
        
        // Should remember the citrus preference from earlier
        if (response3.Products.Any())
        {
            var terpeneProducts = response3.Products.Where(p =>
                MessageContainsAny(p.Description, new[] { "terp", "flavor", "aroma" }));
            
            terpeneProducts.Should().NotBeEmpty("Should focus on terpene-rich products");
        }
    }
    
    [Fact]
    public async Task Should_Learn_From_Purchase_Patterns()
    {
        // Simulate multiple customers with similar patterns
        var customerIds = new List<string>();
        
        // Create pattern: customers asking for "fire" tend to want high THC
        for (int i = 0; i < 3; i++)
        {
            var customerId = $"test_pattern_{i}_{Guid.NewGuid():N}";
            customerIds.Add(customerId);
            await VerifyUser(customerId);
            
            // Each customer asks for "fire" and then specifies high THC
            var request1 = new ChatRequest
            {
                Message = "show me some fire",
                CustomerId = customerId,
                SessionId = $"pattern_session_{i}"
            };
            
            await _client.SendChatMessageAsync(request1);
            
            var request2 = new ChatRequest
            {
                Message = "I want the highest THC you have",
                CustomerId = customerId,
                SessionId = $"pattern_session_{i}"
            };
            
            await _client.SendChatMessageAsync(request2);
        }
        
        // Now test if system learned the pattern
        var testCustomerId = "test_pattern_verify_" + Guid.NewGuid().ToString("N");
        await VerifyUser(testCustomerId);
        
        var testRequest = new ChatRequest
        {
            Message = "got any fire?",
            CustomerId = testCustomerId,
            SessionId = "pattern_verify"
        };
        
        var response = await _client.SendChatMessageAsync(testRequest);
        
        // Assert - Should associate "fire" with high THC based on pattern
        response.Should().NotBeNull();
        
        if (response.Products.Any())
        {
            var highThcProducts = response.Products.Where(p => p.ThcContent >= 20);
            highThcProducts.Should().NotBeEmpty(
                "Should learn that 'fire' often means high THC products");
        }
    }
    
    #endregion
    
    #region 6. Direct Product Request Tests (Existing Functionality)
    
    [Fact]
    public async Task Should_Return_Exact_Product_When_Directly_Requested()
    {
        // Arrange
        var customerId = "test_direct_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = "do you have pink kush 3.5g?",
            CustomerId = customerId,
            SessionId = "direct_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        
        if (response.Products.Any())
        {
            // Should prioritize exact matches
            var exactMatches = response.Products.Where(p =>
                p.Name.ToLower().Contains("pink kush") &&
                (p.Name.Contains("3.5") || p.Name.Contains("eighth")));
            
            if (exactMatches.Any())
            {
                // Exact match should be first
                response.Products.First().Name.ToLower().Should().Contain("pink kush");
            }
            
            // Should also include alternatives/recommendations
            response.Products.Count.Should().BeGreaterThanOrEqualTo(1,
                "Should provide the requested product and possibly alternatives");
        }
    }
    
    [Fact]
    public async Task Should_Return_All_Brands_For_Same_Product()
    {
        // Arrange
        var customerId = "test_brands_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        // Request a common strain that likely has multiple brands
        var request = new ChatRequest
        {
            Message = "show me all OG Kush options",
            CustomerId = customerId,
            SessionId = "brands_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        
        if (response.Products.Any())
        {
            var ogKushProducts = response.Products.Where(p =>
                p.Name.ToLower().Contains("og") && p.Name.ToLower().Contains("kush"));
            
            // If multiple brands exist, should show them
            var uniqueBrands = ogKushProducts
                .Select(p => p.Brand)
                .Where(b => !string.IsNullOrEmpty(b))
                .Distinct()
                .Count();
            
            if (uniqueBrands > 1)
            {
                MessageContainsAny(response.Message,
                    new[] { "brand", "option", "different", "various", "multiple" }).Should().BeTrue(
                    "Should mention multiple brands are available");
            }
        }
    }
    
    #endregion
    
    #region Helper Methods
    
    private bool MessageContainsAny(string message, string[] terms)
    {
        if (string.IsNullOrWhiteSpace(message))
            return false;
            
        var lowerMessage = message.ToLower();
        return terms.Any(term => lowerMessage.Contains(term.ToLower()));
    }
    
    private bool ProductsContainTerms(List<Product> products, string[] terms)
    {
        if (products == null || !products.Any())
            return false;
            
        return products.Any(p => 
            terms.Any(term => 
                p.Name?.ToLower().Contains(term.ToLower()) == true ||
                p.Description?.ToLower().Contains(term.ToLower()) == true));
    }
    
    #endregion
}