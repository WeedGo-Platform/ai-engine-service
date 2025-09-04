using Xunit;
using FluentAssertions;
using AIEngineTests.Helpers;
using AIEngineTests.Models;

namespace AIEngineTests.Tests;

public class ParsingTests : IClassFixture<ApiTestFixture>
{
    private readonly AIEngineApiClient _client;
    
    public ParsingTests(ApiTestFixture fixture)
    {
        _client = fixture.Client;
    }

    [Theory]
    [InlineData("under 10$", 10)]
    [InlineData("less than 20 dollars", 20)]
    [InlineData("under $15", 15)]
    [InlineData("products under 30", 30)]
    [InlineData("cheaper than $25", 25)]
    public async Task Should_Parse_Single_Budget_Values(string budgetPhrase, decimal expectedMax)
    {
        // Arrange
        var customerId = "test_budget_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);

        var request = new ChatRequest
        {
            Message = $"Show me products {budgetPhrase}",
            CustomerId = customerId,
            SessionId = "budget_test"
        };

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        response.Products.Should().NotBeEmpty();
        response.Products.Should().AllSatisfy(product =>
        {
            product.Price.Should().BeLessThanOrEqualTo(expectedMax,
                $"All products should be under ${expectedMax} for phrase: {budgetPhrase}");
        });
    }

    [Theory]
    [InlineData("$10 to $20", 10, 20)]
    [InlineData("between 15 and 30", 15, 30)]
    [InlineData("20-40 dollars", 20, 40)]
    [InlineData("$25 - $50", 25, 50)]
    public async Task Should_Parse_Budget_Ranges(string budgetPhrase, decimal expectedMin, decimal expectedMax)
    {
        // Arrange
        var customerId = "test_range_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);

        var request = new ChatRequest
        {
            Message = $"I want products {budgetPhrase}",
            CustomerId = customerId,
            SessionId = "range_test"
        };

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        if (response.Products.Any())
        {
            response.Products.Should().AllSatisfy(product =>
            {
                product.Price.Should().BeInRange(expectedMin, expectedMax,
                    $"Products should be in range {expectedMin}-{expectedMax}");
            });
        }
    }

    [Theory]
    [InlineData("sativa", "sativa")]
    [InlineData("indica", "indica")]
    [InlineData("hybrid", "hybrid")]
    [InlineData("sativa dominant", "sativa")]
    [InlineData("indica heavy", "indica")]
    public async Task Should_Parse_Strain_Types(string strainPhrase, string expectedStrain)
    {
        // Arrange
        var customerId = "test_strain_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);

        var request = new ChatRequest
        {
            Message = $"I want {strainPhrase} products",
            CustomerId = customerId,
            SessionId = "strain_test"
        };

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        response.Stage.Should().Be("recommendation");
        if (response.Products.Any())
        {
            response.Products.Should().Contain(product =>
                product.PlantType.ToLower().Contains(expectedStrain),
                $"Should have {expectedStrain} products for phrase: {strainPhrase}");
        }
    }

    [Theory]
    [InlineData("joint", new[] { "joint", "pre-roll" })]
    [InlineData("joints", new[] { "joint", "pre-roll" })]
    [InlineData("pre-roll", new[] { "pre-roll", "joint" })]
    [InlineData("flower", new[] { "flower", "bud" })]
    [InlineData("vape", new[] { "vape", "cartridge" })]
    [InlineData("edible", new[] { "edible", "gummy", "chocolate" })]
    public async Task Should_Parse_Product_Types(string productType, string[] expectedKeywords)
    {
        // Arrange
        var customerId = "test_type_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);

        var request = new ChatRequest
        {
            Message = $"Show me some {productType}",
            CustomerId = customerId,
            SessionId = "type_test"
        };

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        response.Stage.Should().Be("recommendation");
        if (response.Products.Any())
        {
            response.Products.Should().Contain(product =>
                expectedKeywords.Any(keyword => 
                    product.Name.ToLower().Contains(keyword)),
                $"Should have products matching type: {productType}");
        }
    }

    [Fact]
    public async Task Should_Parse_Complex_Requests()
    {
        // Arrange
        var customerId = "test_complex_" + Guid.NewGuid().ToString("N");
        await VerifyUser(customerId);

        var request = new ChatRequest
        {
            Message = "I need 3 sativa pre-rolls under $12 for daytime energy",
            CustomerId = customerId,
            SessionId = "complex_test"
        };

        // Act
        var response = await _client.SendChatMessageAsync(request);

        // Assert
        response.Stage.Should().Be("recommendation");
        response.Products.Should().NotBeEmpty();
        response.Products.Should().AllSatisfy(product =>
        {
            product.Price.Should().BeLessThanOrEqualTo(12m);
            product.PlantType.ToLower().Should().Contain("sativa");
            var name = product.Name.ToLower();
            (name.Contains("pre-roll") || name.Contains("joint")).Should().BeTrue(
                "Products should be pre-rolls or joints");
        });
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