using Xunit;
using FluentAssertions;
using AIEngineTests.Helpers;
using AIEngineTests.Models;

namespace AIEngineTests.Tests;

public class AgeVerificationTests : IClassFixture<ApiTestFixture>
{
    private readonly AIEngineApiClient _client;
    
    public AgeVerificationTests(ApiTestFixture fixture)
    {
        _client = fixture.Client;
    }

    [Fact]
    public async Task Should_Require_Age_Verification_For_New_Users()
    {
        // Arrange
        var request = new ChatRequest
        {
            Message = "Show me some products",
            CustomerId = "unverified_user_" + Guid.NewGuid().ToString("N"),
            SessionId = "test_session"
        };

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        response.Should().NotBeNull();
        response.Stage.Should().Be("verification_required");
        response.Message.Should().Contain("verify your age");
        response.Products.Should().BeEmpty("Unverified users should not see products");
        response.QuickReplies.Should().Contain("Verify Age");
    }

    [Fact]
    public async Task Should_Allow_Verified_Users_To_See_Products()
    {
        // Arrange
        var customerId = "verified_user_" + Guid.NewGuid().ToString("N");
        
        // First verify the user
        var verificationRequest = new AgeVerificationRequest
        {
            CustomerId = customerId,
            BirthDate = "1985-06-15",
            VerificationMethod = "government_id",
            GovernmentIdHash = "hash_" + Guid.NewGuid().ToString("N")
        };
        
        var verificationResponse = await _client.VerifyAgeAsync(verificationRequest);
        verificationResponse.Success.Should().BeTrue();
        verificationResponse.Token.Should().NotBeNullOrEmpty();

        // Now try to get products
        var chatRequest = new ChatRequest
        {
            Message = "Show me sativa products",
            CustomerId = customerId,
            SessionId = "test_session"
        };

        // Act
        var chatResponse = await _client.SendChatMessageAsync(chatRequest);

        // Assert
        chatResponse.Stage.Should().NotBe("verification_required");
        chatResponse.Products.Should().NotBeEmpty("Verified users should see products");
    }

    [Fact]
    public async Task Should_Persist_Verification_Across_Sessions()
    {
        // Arrange
        var customerId = "persistent_user_" + Guid.NewGuid().ToString("N");
        
        // Verify the user
        var verificationRequest = new AgeVerificationRequest
        {
            CustomerId = customerId,
            BirthDate = "1992-03-20",
            VerificationMethod = "manual"
        };
        
        await _client.VerifyAgeAsync(verificationRequest);

        // First chat request
        var firstRequest = new ChatRequest
        {
            Message = "Show me products",
            CustomerId = customerId,
            SessionId = "session_1"
        };

        var firstResponse = await _client.SendChatMessageAsync(firstRequest);
        firstResponse.Stage.Should().NotBe("verification_required");

        // Second chat request with different session
        var secondRequest = new ChatRequest
        {
            Message = "Show me more products",
            CustomerId = customerId,
            SessionId = "session_2"
        };

        // Act
        var secondResponse = await _client.SendChatMessageAsync(secondRequest);

        // Assert
        secondResponse.Stage.Should().NotBe("verification_required", 
            "Verification should persist across different sessions");
        secondResponse.Products.Should().NotBeEmpty();
    }

    [Fact]
    public async Task Should_Allow_Guest_Users_Limited_Access()
    {
        // Arrange
        var sessionId = Guid.NewGuid().ToString("N");
        var guestId = $"guest_{sessionId.Substring(0, 8)}";
        
        var request = new ChatRequest
        {
            Message = "Tell me about cannabis",
            CustomerId = guestId,
            SessionId = sessionId
        };

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        response.Should().NotBeNull();
        response.Stage.Should().NotBe("verification_required", 
            "Guest users should have limited access without verification requirement");
        // Guest users might have limited functionality but shouldn't be blocked entirely
    }
}