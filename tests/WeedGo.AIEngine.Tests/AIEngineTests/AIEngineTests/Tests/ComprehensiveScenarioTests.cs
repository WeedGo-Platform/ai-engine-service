using Xunit;
using FluentAssertions;
using AIEngineTests.Helpers;
using AIEngineTests.Models;
using System.Linq;

namespace AIEngineTests.Tests;

/// <summary>
/// Comprehensive test suite covering all Customer 0003 and 0004 scenarios
/// Tests cannabis terminology, complex preferences, and context management
/// </summary>
public class ComprehensiveScenarioTests : IClassFixture<ApiTestFixture>
{
    private readonly AIEngineApiClient _client;
    
    public ComprehensiveScenarioTests(ApiTestFixture fixture)
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
    
    #region Customer 0003 Scenarios - Shatter & Complex Preferences
    
    [Fact]
    public async Task Should_Recognize_Greeting_As_Greeting_Not_ProductSearch()
    {
        // Arrange
        var customerId = "test_greeting_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = "hey",
            CustomerId = customerId,
            SessionId = "greeting_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        response.Stage.Should().Be("greeting", "'hey' should be recognized as a greeting");
        response.Message.ToLower().Should().Contain("welcome");
        response.Products.Should().BeEmpty("Greetings should not return products");
    }
    
    [Fact]
    public async Task Should_Find_Shatter_Products_When_Requested()
    {
        // Arrange
        var customerId = "test_shatter_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = "show me some shatter",
            CustomerId = customerId,
            SessionId = "shatter_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        response.Products.Should().NotBeEmpty("Should find shatter products");
        response.Products.Should().OnlyContain(p => 
            p.Category.Equals("Extracts", StringComparison.OrdinalIgnoreCase) ||
            p.Name.ToLower().Contains("shatter"),
            "All products should be shatter or in Extracts category");
    }
    
    [Fact]
    public async Task Should_Handle_Complex_Preferences_NoSmoking_NoEdibles_Odorless()
    {
        // Arrange
        var customerId = "test_complex_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = "I don't smoke and don't like edibles, what odorless sativa products do you have?",
            CustomerId = customerId,
            SessionId = "complex_pref_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        if (response.Products.Any())
        {
            response.Products.Should().NotContain(p => 
                p.Category == "Flower" || p.Category == "Edibles",
                "Should exclude Flower and Edibles categories");
            
            response.Products.Should().OnlyContain(p => 
                p.Category == "Vapes" || p.Category == "Tinctures" || 
                p.Category == "Capsules" || p.Category == "Topicals",
                "Should only include non-smoking, non-edible options");
        }
        else
        {
            // If no products, message should suggest alternatives
            response.Message.Should().ContainAny(
                new[] { "vape", "tincture", "capsule", "topical" });
        }
    }
    
    [Fact]
    public async Task Should_Find_Pink_Kush_When_Requested()
    {
        // Arrange
        var customerId = "test_pink_kush_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = "do you have pink kush",
            CustomerId = customerId,
            SessionId = "pink_kush_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        if (response.Products.Any())
        {
            response.Products.Should().Contain(p => 
                p.Name.ToLower().Contains("pink kush"),
                "Should find Pink Kush products if available");
        }
        else
        {
            // If no Pink Kush available, should acknowledge the request
            response.Message.ToLower().Should().Contain("pink kush");
        }
    }
    
    #endregion
    
    #region Customer 0004 Scenarios - Cannabis Slang & Context
    
    [Theory]
    [InlineData("gas and dense", new[] { "og", "diesel", "fuel", "kush" })]
    [InlineData("want something fruity and dense", new[] { "purple", "berry", "punch", "zkittlez" })]
    [InlineData("loud fire", new[] { "premium", "potent", "high thc" })]
    [InlineData("sticky icky", new[] { "flower", "bud", "resinous" })]
    public async Task Should_Understand_Cannabis_Slang_And_Descriptors(string query, string[] expectedKeywords)
    {
        // Arrange
        var customerId = "test_slang_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = query,
            CustomerId = customerId,
            SessionId = "slang_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        
        if (response.Products.Any())
        {
            // Check if products match expected keywords
            response.Products.Should().Contain(p => 
                expectedKeywords.Any(keyword => 
                    p.Name.ToLower().Contains(keyword)),
                $"Products should match cannabis slang '{query}'");
        }
        else
        {
            // Message should acknowledge the request type
            var messageLower = response.Message.ToLower();
            expectedKeywords.Any(k => messageLower.Contains(k)).Should().BeTrue();
        }
    }
    
    [Theory]
    [InlineData("swettberry kush", "sweetberry")]
    [InlineData("gorrila glue", "gorilla")]
    [InlineData("weding cake", "wedding")]
    public async Task Should_Correct_Common_Misspellings(string misspelled, string corrected)
    {
        // Arrange
        var customerId = "test_spelling_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = $"i want {misspelled}",
            CustomerId = customerId,
            SessionId = "spelling_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        
        // Either finds products with corrected name or shows correction in message
        var foundCorrectedProduct = response.Products?.Any(p => 
            p.Name.ToLower().Contains(corrected.ToLower())) ?? false;
        
        var messageShowsCorrection = response.Message.ToLower().Contains(corrected.ToLower());
        
        (foundCorrectedProduct || messageShowsCorrection).Should().BeTrue(
            $"Should either find products with '{corrected}' or show the correction in the message");
    }
    
    [Fact]
    public async Task Should_Remember_Products_And_Allow_Cart_Actions()
    {
        // Arrange
        var customerId = "test_context_" + Guid.NewGuid().ToString("N");
        var sessionId = "context_test_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        // First, search for products
        var searchRequest = new ChatRequest
        {
            Message = "show me crab cake",
            CustomerId = customerId,
            SessionId = sessionId
        };
        
        var searchResponse = await _client.SendChatMessageAsync(searchRequest);
        searchResponse.Products.Should().NotBeEmpty("Should find products first");
        
        // Then try to reference them
        var cartRequest = new ChatRequest
        {
            Message = "i'll take the preroll",
            CustomerId = customerId,
            SessionId = sessionId
        };
        
        // Act
        var cartResponse = await _client.SendChatMessageAsync(cartRequest);
        
        // Assert
        cartResponse.Should().NotBeNull();
        cartResponse.Message.Should().ContainAny(
            new[] { "cart", "added", "choice" });
        // Should recognize cart intent and add product
    }
    
    #endregion
    
    #region Edge Cases & Advanced Scenarios
    
    [Theory]
    [InlineData("eighth", "3.5")]
    [InlineData("quarter", "7")]
    [InlineData("half ounce", "14")]
    [InlineData("zip", "28")]
    [InlineData("1/4 quarter", "7")]
    public async Task Should_Understand_Quantity_Slang(string slang, string expectedGrams)
    {
        // Arrange
        var customerId = "test_quantity_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = $"i want a {slang} of pink kush",
            CustomerId = customerId,
            SessionId = "quantity_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        
        // Should understand the quantity and search for appropriate products
        // Check if message acknowledges the quantity
        var understandsQuantity = response.Message.Contains(expectedGrams) || 
                                 response.Message.ToLower().Contains(slang.ToLower());
        
        understandsQuantity.Should().BeTrue(
            $"Should understand that '{slang}' means {expectedGrams}g");
    }
    
    [Fact]
    public async Task Should_Handle_Price_Based_Sativa_Query()
    {
        // Arrange
        var customerId = "test_price_sativa_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = "i need a $10 sativa preroll",
            CustomerId = customerId,
            SessionId = "price_sativa_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        
        if (response.Products.Any())
        {
            response.Products.Should().OnlyContain(p =>
                p.Price <= 15 && // Allow some price flexibility
                (p.Name.ToLower().Contains("sativa") ||
                 (p.Description != null && p.Description.ToLower().Contains("sativa"))),
                "Should find sativa products near $10");
        }
        else
        {
            // Message should acknowledge the specific request
            response.Message.ToLower().Should().Contain("sativa");
            response.Message.Should().ContainAny(new[] { "10", "$10", "ten" });
        }
    }
    
    [Fact]
    public async Task Should_Handle_Multiple_Criteria_Query()
    {
        // Arrange
        var customerId = "test_multi_criteria_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = "high THC indica for pain relief under $30",
            CustomerId = customerId,
            SessionId = "multi_criteria_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        
        if (response.Products.Any())
        {
            response.Products.Should().OnlyContain(p =>
                p.Price <= 30 &&
                p.ThcContent >= 18, // High THC
                "Products should match price and THC criteria");
            
            // Should prefer indica strains
            var indicaProducts = response.Products.Where(p => 
                p.Name.ToLower().Contains("indica") ||
                (p.Description != null && p.Description.ToLower().Contains("indica")));
            
            indicaProducts.Should().NotBeEmpty("Should include indica products for pain relief");
        }
    }
    
    [Theory]
    [InlineData("got any fire dabs?", "Extracts")]
    [InlineData("show me carts", "Vapes")]
    [InlineData("i want eddies", "Edibles")]
    public async Task Should_Understand_Product_Type_Slang(string query, string expectedCategory)
    {
        // Arrange
        var customerId = "test_type_slang_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        var request = new ChatRequest
        {
            Message = query,
            CustomerId = customerId,
            SessionId = "type_slang_test"
        };
        
        // Act
        var response = await _client.SendChatMessageAsync(request);
        
        // Assert
        response.Should().NotBeNull();
        
        if (response.Products.Any())
        {
            response.Products.Should().OnlyContain(p =>
                p.Category == expectedCategory,
                $"Should return {expectedCategory} products for '{query}'");
        }
        else
        {
            // Message should mention the category
            response.Message.Should().Contain(expectedCategory);
        }
    }
    
    #endregion
    
    #region Test Helpers
    
    [Fact]
    public async Task All_Test_Scenarios_Should_Return_Valid_Responses()
    {
        // This meta-test ensures all scenarios return valid API responses
        var testQueries = new[]
        {
            "hey",
            "show me some shatter",
            "I don't smoke and don't like edibles",
            "gas and dense",
            "fruity and dense",
            "swettberry kush",
            "$10 sativa preroll",
            "quarter of pink kush",
            "high THC indica under $30",
            "fire dabs",
            "sticky icky"
        };
        
        var customerId = "test_all_scenarios_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);
        
        foreach (var query in testQueries)
        {
            var request = new ChatRequest
            {
                Message = query,
                CustomerId = customerId,
                SessionId = "all_scenarios_test"
            };
            
            // Act
            var response = await _client.SendChatMessageAsync(request);
            
            // Assert - Basic response validation
            response.Should().NotBeNull($"Query '{query}' should return a response");
            response.Message.Should().NotBeNullOrWhiteSpace($"Query '{query}' should have a message");
            response.Stage.Should().NotBeNullOrWhiteSpace($"Query '{query}' should have a stage");
            response.Confidence.Should().BeGreaterThan(0, $"Query '{query}' should have confidence > 0");
        }
    }
    
    #endregion
}