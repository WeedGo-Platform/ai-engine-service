using Xunit;
using FluentAssertions;
using AIEngineTests.Helpers;
using AIEngineTests.Models;

namespace AIEngineTests.Tests;

public class DirectProductRequestTests : IClassFixture<ApiTestFixture>
{
    private readonly AIEngineApiClient _client;
    
    public DirectProductRequestTests(ApiTestFixture fixture)
    {
        _client = fixture.Client;
    }

    [Fact]
    public async Task Should_Return_Products_For_Direct_Sativa_Joint_Request()
    {
        // Arrange
        var request = new ChatRequest
        {
            Message = "3 joint sativa under 10$",
            CustomerId = "test_user_" + Guid.NewGuid().ToString("N"),
            SessionId = "test_session_" + Guid.NewGuid().ToString("N")
        };

        // First verify the user
        await VerifyTestUser(request.CustomerId);

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        response.Should().NotBeNull();
        response.Stage.Should().Be("recommendation", "Direct product request should skip to recommendation stage");
        response.Products.Should().NotBeEmpty("Should return products matching the request");
        
        // All products should be sativa and under $10
        response.Products.Should().AllSatisfy(product =>
        {
            product.Price.Should().BeLessThanOrEqualTo(10m, "All products should be under $10");
            product.PlantType.ToLower().Should().Contain("sativa", "All products should be sativa");
        });
    }

    [Fact]
    public async Task Should_Parse_Budget_Under_Pattern()
    {
        // Arrange
        var request = new ChatRequest
        {
            Message = "I want products under 20 dollars",
            CustomerId = "test_user_" + Guid.NewGuid().ToString("N"),
            SessionId = "test_session_" + Guid.NewGuid().ToString("N")
        };

        await VerifyTestUser(request.CustomerId);

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        response.Products.Should().NotBeEmpty();
        response.Products.Should().AllSatisfy(product =>
        {
            product.Price.Should().BeLessThanOrEqualTo(20m, "All products should be under $20");
        });
    }

    [Fact]
    public async Task Should_Recognize_Joint_As_Flower_Product()
    {
        // Arrange
        var request = new ChatRequest
        {
            Message = "Show me some joints",
            CustomerId = "test_user_" + Guid.NewGuid().ToString("N"),
            SessionId = "test_session_" + Guid.NewGuid().ToString("N")
        };

        await VerifyTestUser(request.CustomerId);

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        response.Stage.Should().Be("recommendation");
        response.Products.Should().NotBeEmpty();
        response.Products.Should().AllSatisfy(product =>
        {
            product.Name.ToLower().Should().Match(name => 
                name.Contains("joint") || name.Contains("pre-roll") || name.Contains("flower"),
                "Products should be flower-based");
        });
    }

    [Fact]
    public async Task Should_Handle_Multiple_Criteria()
    {
        // Arrange
        var request = new ChatRequest
        {
            Message = "I need 2 indica joints under 15 dollars for sleep",
            CustomerId = "test_user_" + Guid.NewGuid().ToString("N"),
            SessionId = "test_session_" + Guid.NewGuid().ToString("N")
        };

        await VerifyTestUser(request.CustomerId);

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        response.Stage.Should().Be("recommendation");
        response.Products.Should().NotBeEmpty();
        response.Products.Should().AllSatisfy(product =>
        {
            product.Price.Should().BeLessThanOrEqualTo(15m);
            product.PlantType.ToLower().Should().Contain("indica");
        });
    }

    private async Task VerifyTestUser(string customerId)
    {
        var verificationRequest = new AgeVerificationRequest
        {
            CustomerId = customerId,
            BirthDate = "1990-01-01",
            VerificationMethod = "manual"
        };
        
        await _client.VerifyAgeAsync(verificationRequest);
    }
}