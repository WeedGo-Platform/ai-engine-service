using Xunit;
using FluentAssertions;
using AIEngineTests.Helpers;
using AIEngineTests.Models;

namespace AIEngineTests.Tests;

public class ConversationFlowTests : IClassFixture<ApiTestFixture>
{
    private readonly AIEngineApiClient _client;
    
    public ConversationFlowTests(ApiTestFixture fixture)
    {
        _client = fixture.Client;
    }

    [Fact]
    public async Task Should_Not_Get_Stuck_In_Qualification_Loop()
    {
        // This tests the exact bug we fixed for customer 0001
        // Arrange
        var customerId = "test_loop_" + Guid.NewGuid().ToString("N");
        var sessionId = "session_" + Guid.NewGuid().ToString("N");
        
        // Verify user first
        await VerifyUser(customerId);

        // Send multiple direct product requests
        var messages = new[]
        {
            "3 joint sativa under 10$",
            "I want sativa",
            "show me joints"
        };

        foreach (var message in messages)
        {
            var request = new ChatRequest
            {
                Message = message,
                CustomerId = customerId,
                SessionId = sessionId
            };

            // Act
            var response = await _client.SendChatMessageAsync(request);

            // Assert
            response.Stage.Should().Be("recommendation", 
                $"Should not be stuck in qualification for message: {message}");
            response.Message.Should().NotContain("What methods have you tried", 
                "Should not ask qualification questions for direct requests");
            response.Products.Should().NotBeEmpty(
                "Should return products for direct requests");
        }
    }

    [Fact]
    public async Task Should_Progress_Through_Stages_Naturally()
    {
        // Arrange
        var customerId = "test_stages_" + Guid.NewGuid().ToString("N");
        var sessionId = "session_" + Guid.NewGuid().ToString("N");
        
        await VerifyUser(customerId);

        // Start with greeting
        var greetingRequest = new ChatRequest
        {
            Message = "Hi there",
            CustomerId = customerId,
            SessionId = sessionId
        };

        var greetingResponse = await _client.SendChatMessageAsync(greetingRequest);
        
        // Move to qualification with vague request
        var qualificationRequest = new ChatRequest
        {
            Message = "I need something for sleep",
            CustomerId = customerId,
            SessionId = sessionId
        };

        var qualificationResponse = await _client.SendChatMessageAsync(qualificationRequest);

        // Assert proper progression
        greetingResponse.Stage.Should().BeOneOf("greeting", "qualification");
        qualificationResponse.Stage.Should().BeOneOf("qualification", "recommendation");
        
        // If in qualification, should ask relevant questions
        if (qualificationResponse.Stage == "qualification")
        {
            qualificationResponse.QuickReplies.Should().NotBeEmpty();
        }
    }

    [Fact]
    public async Task Should_Skip_To_Recommendation_For_Direct_Requests()
    {
        // Arrange
        var customerId = "test_skip_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);

        var request = new ChatRequest
        {
            Message = "I want indica flower under 25 dollars",
            CustomerId = customerId,
            SessionId = "session_skip"
        };

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        response.Stage.Should().Be("recommendation", 
            "Direct product requests should skip to recommendation");
        response.Products.Should().NotBeEmpty();
        response.Products.Should().AllSatisfy(p =>
        {
            p.Price.Should().BeLessThanOrEqualTo(25m);
            p.PlantType.ToLower().Should().Contain("indica");
        });
    }

    [Fact]
    public async Task Should_Remember_Customer_Context()
    {
        // Arrange
        var customerId = "test_context_" + Guid.NewGuid().ToString("N");
        var sessionId = "session_context";
        
        await VerifyUser(customerId);

        // First message establishes preference
        var firstRequest = new ChatRequest
        {
            Message = "I prefer sativa for daytime use",
            CustomerId = customerId,
            SessionId = sessionId
        };

        await _client.SendChatMessageAsync(firstRequest);

        // Second message should remember context
        var secondRequest = new ChatRequest
        {
            Message = "Show me some options",
            CustomerId = customerId,
            SessionId = sessionId
        };

        // Act
        var response = await _client.SendChatMessageAsync(secondRequest);

        // Assert
        response.Products.Should().NotBeEmpty();
        // Products should reflect the earlier preference for sativa
        response.Products.Should().Contain(p => 
            p.PlantType.ToLower().Contains("sativa"),
            "Should remember customer's sativa preference");
    }

    private async Task VerifyUser(string customerId)
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