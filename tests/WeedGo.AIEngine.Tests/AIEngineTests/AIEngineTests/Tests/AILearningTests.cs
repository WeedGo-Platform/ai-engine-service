using Xunit;
using FluentAssertions;
using AIEngineTests.Helpers;
using AIEngineTests.Models;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;

namespace AIEngineTests.Tests;

/// <summary>
/// Tests for AI Learning capabilities
/// These tests validate that the AI improves with training
/// Not testing specific outputs, but learning improvement
/// </summary>
public class AILearningTests : IClassFixture<ApiTestFixture>
{
    private readonly AIEngineApiClient _client;
    
    public AILearningTests(ApiTestFixture fixture)
    {
        _client = fixture.Client;
    }
    
    #region Core Learning Tests
    
    [Fact]
    public async Task AI_Should_Improve_Accuracy_After_Training()
    {
        // This is the most important test - proves the AI learns
        
        // Arrange - Create training examples
        var trainingData = new List<TrainingExample>
        {
            new TrainingExample
            {
                Query = "I need something for sleep",
                ExpectedIntent = "product_search",
                ExpectedEntities = new Dictionary<string, object>
                {
                    ["effects"] = "sleep",
                    ["strain_type"] = "indica"
                },
                ExpectedProducts = new[] { "indica", "sleep", "nighttime" },
                ExpectedResponseQualities = new[] { "mentions_sleep", "suggests_indica", "calming_tone" }
            },
            new TrainingExample
            {
                Query = "show me pink kush 3.5g",
                ExpectedIntent = "product_search",
                ExpectedEntities = new Dictionary<string, object>
                {
                    ["product"] = "pink kush",
                    ["size"] = "3.5g"
                },
                ExpectedProducts = new[] { "pink kush" },
                ExpectedResponseQualities = new[] { "specific_product", "mentions_size" }
            },
            new TrainingExample
            {
                Query = "what's good for creativity?",
                ExpectedIntent = "product_search",
                ExpectedEntities = new Dictionary<string, object>
                {
                    ["effects"] = "creativity",
                    ["strain_type"] = "sativa"
                },
                ExpectedProducts = new[] { "sativa", "creative", "focus" },
                ExpectedResponseQualities = new[] { "mentions_creativity", "suggests_sativa", "energetic_tone" }
            }
        };
        
        // Act - Train the AI
        var trainingRequest = new TrainRequest
        {
            Examples = trainingData,
            SessionId = "training_session_001"
        };
        
        var trainingResponse = await _client.TrainAIAsync(trainingRequest);
        
        // Assert - Verify learning occurred
        trainingResponse.Should().NotBeNull();
        trainingResponse.ExamplesTrained.Should().Be(trainingData.Count);
        trainingResponse.AccuracyAfter.Should().BeGreaterThan(trainingResponse.AccuracyBefore,
            "Accuracy should improve after training");
        
        // Test that the AI now handles similar queries better
        var testQueries = new[]
        {
            "help me sleep better",
            "I want pink kush",
            "need something creative"
        };
        
        foreach (var query in testQueries)
        {
            var response = await _client.SendChatMessageAsync(new ChatRequest
            {
                Message = query,
                CustomerId = "test_customer",
                SessionId = "test_session"
            });
            
            response.Should().NotBeNull();
            response.Confidence.Should().BeGreaterThan(0.5,
                $"AI should be confident about '{query}' after training");
        }
    }
    
    [Fact]
    public async Task AI_Should_Learn_New_Cannabis_Terminology()
    {
        // Test that AI can learn slang and terminology through examples
        
        // Arrange - Teach new slang
        var slangTraining = new List<TrainingExample>
        {
            new TrainingExample
            {
                Query = "got any fire?",
                ExpectedIntent = "product_search",
                ExpectedEntities = new Dictionary<string, object>
                {
                    ["quality"] = "premium",
                    ["potency"] = "high"
                },
                ExpectedResponseQualities = new[] { "mentions_premium", "high_quality_products" }
            },
            new TrainingExample
            {
                Query = "show me some gas",
                ExpectedIntent = "product_search",
                ExpectedEntities = new Dictionary<string, object>
                {
                    ["terpene_profile"] = "diesel",
                    ["category"] = "flower"
                },
                ExpectedResponseQualities = new[] { "mentions_diesel", "strong_aroma" }
            }
        };
        
        // Act - Train
        await _client.TrainAIAsync(new TrainRequest { Examples = slangTraining });
        
        // Test understanding
        var response = await _client.SendChatMessageAsync(new ChatRequest
        {
            Message = "you got fire gas?",
            CustomerId = "test_customer",
            SessionId = "slang_test"
        });
        
        // Assert - Should understand combined slang
        response.Should().NotBeNull();
        response.Stage.Should().NotBe("error");
        
        // The response should indicate understanding of both terms
        var understood = response.Message.ToLower().ContainsAny(
            new[] { "premium", "diesel", "strong", "potent", "quality" });
        
        understood.Should().BeTrue("AI should understand learned slang terminology");
    }
    
    [Fact]
    public async Task AI_Should_Learn_Customer_Preference_Patterns()
    {
        // Test that AI learns patterns from customer interactions
        
        // Arrange - Create pattern examples
        var patternExamples = new List<TrainingExample>();
        
        // Pattern: Customers asking for "fire" usually want high THC
        for (int i = 0; i < 5; i++)
        {
            patternExamples.Add(new TrainingExample
            {
                Query = $"show me fire {i}",
                Context = new Dictionary<string, object> { ["customer_type"] = "experienced" },
                ExpectedEntities = new Dictionary<string, object> { ["min_thc"] = "20" },
                FeedbackScore = 0.9f // High satisfaction
            });
        }
        
        // Pattern: New customers need guidance
        for (int i = 0; i < 5; i++)
        {
            patternExamples.Add(new TrainingExample
            {
                Query = "I'm new to this",
                Context = new Dictionary<string, object> { ["visit_count"] = 1 },
                ExpectedResponseQualities = new[] { "educational", "gentle_guidance", "starter_products" },
                FeedbackScore = 0.95f
            });
        }
        
        // Act - Train with patterns
        var trainingResponse = await _client.TrainAIAsync(new TrainRequest 
        { 
            Examples = patternExamples 
        });
        
        // Assert - Verify pattern learning
        trainingResponse.PattersLearned.Should().BeGreaterThan(0);
        
        // Test pattern recognition
        var fireResponse = await _client.SendChatMessageAsync(new ChatRequest
        {
            Message = "got any fire stuff?",
            CustomerId = "experienced_customer",
            SessionId = "pattern_test_1"
        });
        
        // Should recognize high THC preference pattern
        if (fireResponse.Products.Any())
        {
            fireResponse.Products.Should().Contain(p => p.ThcContent >= 18,
                "Should learn that 'fire' correlates with high THC");
        }
    }
    
    #endregion
    
    #region Continuous Learning Tests
    
    [Fact]
    public async Task AI_Should_Improve_With_Each_Training_Session()
    {
        // Test continuous improvement over multiple training sessions
        
        var accuracyHistory = new List<double>();
        
        // Conduct 5 training sessions
        for (int session = 0; session < 5; session++)
        {
            // Create training data for this session
            var examples = GenerateTrainingExamples(10);
            
            var response = await _client.TrainAIAsync(new TrainRequest
            {
                Examples = examples,
                SessionId = $"continuous_session_{session}"
            });
            
            accuracyHistory.Add(response.AccuracyAfter);
            
            // Each session should maintain or improve accuracy
            if (session > 0)
            {
                response.AccuracyAfter.Should().BeGreaterThanOrEqualTo(
                    accuracyHistory[session - 1],
                    $"Session {session} should not degrade performance");
            }
        }
        
        // Overall improvement from first to last
        accuracyHistory.Last().Should().BeGreaterThan(accuracyHistory.First(),
            "AI should show improvement over multiple training sessions");
    }
    
    [Fact]
    public async Task AI_Should_Learn_From_Feedback()
    {
        // Test that AI incorporates feedback to improve
        
        // Initial query
        var initialResponse = await _client.SendChatMessageAsync(new ChatRequest
        {
            Message = "I want something fruity",
            CustomerId = "feedback_customer",
            SessionId = "feedback_session"
        });
        
        // Provide feedback that response wasn't good
        var feedbackExample = new TrainingExample
        {
            Query = "I want something fruity",
            ExpectedProducts = new[] { "berry", "citrus", "tropical" },
            ExpectedResponseQualities = new[] { "mentions_terpenes", "specific_strains" },
            FeedbackScore = 0.3f // Low score indicates poor initial response
        };
        
        // Train with feedback
        await _client.TrainAIAsync(new TrainRequest
        {
            Examples = new[] { feedbackExample },
            IsFeedback = true
        });
        
        // Same query again
        var improvedResponse = await _client.SendChatMessageAsync(new ChatRequest
        {
            Message = "I want something fruity",
            CustomerId = "feedback_customer_2",
            SessionId = "feedback_session_2"
        });
        
        // Should be better
        improvedResponse.Confidence.Should().BeGreaterThan(initialResponse.Confidence,
            "Response should improve after feedback training");
    }
    
    #endregion
    
    #region Knowledge Retention Tests
    
    [Fact]
    public async Task AI_Should_Retain_Knowledge_Across_Sessions()
    {
        // Test that learned knowledge persists
        
        // Train with specific knowledge
        var knowledgeExamples = new List<TrainingExample>
        {
            new TrainingExample
            {
                Query = "what is CBG?",
                ExpectedIntent = "information_request",
                ExpectedResponseQualities = new[] { 
                    "explains_cbg", 
                    "mentions_benefits", 
                    "educational" 
                }
            }
        };
        
        await _client.TrainAIAsync(new TrainRequest 
        { 
            Examples = knowledgeExamples,
            SessionId = "knowledge_session_1"
        });
        
        // Export knowledge
        var exportResponse = await _client.ExportKnowledgeAsync();
        exportResponse.Should().NotBeNull();
        exportResponse.TotalExamples.Should().BeGreaterThan(0);
        
        // Simulate restart by creating new session
        // In real scenario, this would be after service restart
        
        // Import knowledge
        await _client.ImportKnowledgeAsync(new ImportKnowledgeRequest
        {
            KnowledgeData = exportResponse.KnowledgeData
        });
        
        // Test retained knowledge
        var response = await _client.SendChatMessageAsync(new ChatRequest
        {
            Message = "tell me about CBG",
            CustomerId = "retention_test",
            SessionId = "new_session_after_import"
        });
        
        response.Should().NotBeNull();
        response.Message.ToLower().Should().ContainAny(
            new[] { "cbg", "cannabigerol", "benefit", "effect" },
            "AI should retain knowledge about CBG after import");
    }
    
    #endregion
    
    #region Performance Metrics Tests
    
    [Fact]
    public async Task Should_Track_Learning_Metrics()
    {
        // Test that system tracks learning performance
        
        // Get initial stats
        var initialStats = await _client.GetLearningStatsAsync();
        
        // Train
        var examples = GenerateTrainingExamples(20);
        await _client.TrainAIAsync(new TrainRequest { Examples = examples });
        
        // Get updated stats
        var updatedStats = await _client.GetLearningStatsAsync();
        
        // Verify metrics are tracked
        updatedStats.TotalExamplesTrained.Should().BeGreaterThan(
            initialStats.TotalExamplesTrained);
        updatedStats.UniquePatterns.Should().BeGreaterThan(0);
        updatedStats.CurrentAccuracy.Should().BeGreaterThan(0);
        
        // If multiple sessions, should show improvement rate
        if (updatedStats.SessionsCompleted > 1)
        {
            updatedStats.ImprovementRate.Should().BeGreaterThanOrEqualTo(0,
                "Should track improvement rate");
        }
    }
    
    #endregion
    
    #region Helper Methods
    
    private List<TrainingExample> GenerateTrainingExamples(int count)
    {
        var examples = new List<TrainingExample>();
        var random = new Random();
        
        var queries = new[]
        {
            "show me indica",
            "I need energy",
            "help with pain",
            "something to relax",
            "high THC products",
            "edibles for beginners",
            "vape cartridges",
            "pre-rolls under $20"
        };
        
        var intents = new[] { "product_search", "information_request", "greeting" };
        
        for (int i = 0; i < count; i++)
        {
            examples.Add(new TrainingExample
            {
                Query = queries[random.Next(queries.Length)],
                ExpectedIntent = intents[random.Next(intents.Length)],
                ExpectedEntities = new Dictionary<string, object>
                {
                    ["category"] = "Flower",
                    ["strain_type"] = random.Next(2) == 0 ? "indica" : "sativa"
                },
                FeedbackScore = (float)(0.5 + random.NextDouble() * 0.5)
            });
        }
        
        return examples;
    }
    
    #endregion
}

// Training Models
public class TrainingExample
{
    public string Query { get; set; } = string.Empty;
    public Dictionary<string, object>? Context { get; set; }
    public string ExpectedIntent { get; set; } = string.Empty;
    public Dictionary<string, object> ExpectedEntities { get; set; } = new();
    public string[] ExpectedProducts { get; set; } = Array.Empty<string>();
    public string[] ExpectedResponseQualities { get; set; } = Array.Empty<string>();
    public float FeedbackScore { get; set; }
}

public class TrainRequest
{
    public List<TrainingExample> Examples { get; set; } = new();
    public string SessionId { get; set; } = string.Empty;
    public bool IsFeedback { get; set; }
}

public class TrainResponse
{
    public int ExamplesTrained { get; set; }
    public double AccuracyBefore { get; set; }
    public double AccuracyAfter { get; set; }
    public int PatternsLearned { get; set; }
    public Dictionary<string, double> Improvements { get; set; } = new();
}

public class LearningStats
{
    public int TotalExamplesTrained { get; set; }
    public double CurrentAccuracy { get; set; }
    public int UniquePatterns { get; set; }
    public int SessionsCompleted { get; set; }
    public double ImprovementRate { get; set; }
}

public class ExportKnowledgeResponse
{
    public string KnowledgeData { get; set; } = string.Empty;
    public int TotalExamples { get; set; }
    public DateTime ExportedAt { get; set; }
}

public class ImportKnowledgeRequest
{
    public string KnowledgeData { get; set; } = string.Empty;
}