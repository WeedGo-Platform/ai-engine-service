using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Caching.Memory;

namespace WeedGo.AIEngine.Api.Services;

public interface IVirtualBudtenderService
{
    Task<BudtenderResponse> ChatAsync(ChatRequest request);
    Task<RecommendationResponse> GetRecommendationsAsync(RecommendationRequest request);
    Task<SessionResponse> CreateSessionAsync(SessionRequest request);
    Task<SessionResponse> GetSessionAsync(string sessionId);
    Task<bool> EndSessionAsync(string sessionId);
}

public class VirtualBudtenderService : IVirtualBudtenderService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<VirtualBudtenderService> _logger;
    private readonly IMemoryCache _cache;
    private readonly string _pythonServiceUrl;

    public VirtualBudtenderService(
        HttpClient httpClient,
        ILogger<VirtualBudtenderService> logger,
        IMemoryCache cache,
        IConfiguration configuration)
    {
        _httpClient = httpClient;
        _logger = logger;
        _cache = cache;
        _pythonServiceUrl = configuration["PythonService:BaseUrl"] ?? "http://localhost:8000";
    }

    public async Task<BudtenderResponse> ChatAsync(ChatRequest request)
    {
        try
        {
            var json = JsonSerializer.Serialize(request);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync($"{_pythonServiceUrl}/api/chat", content);
            response.EnsureSuccessStatusCode();
            
            var responseContent = await response.Content.ReadAsStringAsync();
            var result = JsonSerializer.Deserialize<BudtenderResponse>(responseContent, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });
            
            return result ?? new BudtenderResponse { Message = "No response from AI service" };
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Error communicating with Python AI service");
            return new BudtenderResponse
            {
                Message = "I'm having trouble connecting to my knowledge base. Please try again in a moment.",
                IsError = true
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unexpected error in chat service");
            return new BudtenderResponse
            {
                Message = "An unexpected error occurred. Please try again.",
                IsError = true
            };
        }
    }

    public async Task<RecommendationResponse> GetRecommendationsAsync(RecommendationRequest request)
    {
        var cacheKey = $"recommendations_{request.UserId}_{request.Category}_{request.Effects}";
        
        if (_cache.TryGetValue<RecommendationResponse>(cacheKey, out var cachedResponse))
        {
            _logger.LogInformation("Returning cached recommendations for {CacheKey}", cacheKey);
            return cachedResponse!;
        }

        try
        {
            var json = JsonSerializer.Serialize(request);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync($"{_pythonServiceUrl}/api/recommendations", content);
            response.EnsureSuccessStatusCode();
            
            var responseContent = await response.Content.ReadAsStringAsync();
            var result = JsonSerializer.Deserialize<RecommendationResponse>(responseContent, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });
            
            if (result != null)
            {
                _cache.Set(cacheKey, result, TimeSpan.FromMinutes(15));
            }
            
            return result ?? new RecommendationResponse { Recommendations = new List<ProductRecommendation>() };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting recommendations");
            return new RecommendationResponse
            {
                Recommendations = new List<ProductRecommendation>(),
                ErrorMessage = "Unable to generate recommendations at this time"
            };
        }
    }

    public async Task<SessionResponse> CreateSessionAsync(SessionRequest request)
    {
        try
        {
            var json = JsonSerializer.Serialize(request);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync($"{_pythonServiceUrl}/api/sessions", content);
            response.EnsureSuccessStatusCode();
            
            var responseContent = await response.Content.ReadAsStringAsync();
            var result = JsonSerializer.Deserialize<SessionResponse>(responseContent, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });
            
            return result ?? new SessionResponse { SessionId = Guid.NewGuid().ToString() };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating session");
            return new SessionResponse
            {
                SessionId = Guid.NewGuid().ToString(),
                IsError = true,
                ErrorMessage = "Failed to create session with AI service"
            };
        }
    }

    public async Task<SessionResponse> GetSessionAsync(string sessionId)
    {
        try
        {
            var response = await _httpClient.GetAsync($"{_pythonServiceUrl}/api/sessions/{sessionId}");
            response.EnsureSuccessStatusCode();
            
            var responseContent = await response.Content.ReadAsStringAsync();
            var result = JsonSerializer.Deserialize<SessionResponse>(responseContent, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });
            
            return result ?? new SessionResponse { SessionId = sessionId };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting session {SessionId}", sessionId);
            return new SessionResponse
            {
                SessionId = sessionId,
                IsError = true,
                ErrorMessage = "Session not found"
            };
        }
    }

    public async Task<bool> EndSessionAsync(string sessionId)
    {
        try
        {
            var response = await _httpClient.DeleteAsync($"{_pythonServiceUrl}/api/sessions/{sessionId}");
            return response.IsSuccessStatusCode;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error ending session {SessionId}", sessionId);
            return false;
        }
    }
}

// DTOs
public class ChatRequest
{
    public string SessionId { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
    public string? UserId { get; set; }
    public Dictionary<string, object>? Context { get; set; }
}

public class BudtenderResponse
{
    public string Message { get; set; } = string.Empty;
    public List<ProductRecommendation>? Recommendations { get; set; }
    public Dictionary<string, object>? Metadata { get; set; }
    public bool IsError { get; set; }
    public string? SessionId { get; set; }
}

public class RecommendationRequest
{
    public string? UserId { get; set; }
    public string? Category { get; set; }
    public string? Effects { get; set; }
    public decimal? MaxPrice { get; set; }
    public int Limit { get; set; } = 5;
    public Dictionary<string, object>? Preferences { get; set; }
}

public class RecommendationResponse
{
    public List<ProductRecommendation> Recommendations { get; set; } = new();
    public string? ErrorMessage { get; set; }
}

public class ProductRecommendation
{
    public string ProductId { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public string Description { get; set; } = string.Empty;
    public double Score { get; set; }
    public string Reason { get; set; } = string.Empty;
    public Dictionary<string, object>? Attributes { get; set; }
}

public class SessionRequest
{
    public string? UserId { get; set; }
    public string? CustomerType { get; set; }
    public Dictionary<string, object>? InitialContext { get; set; }
}

public class SessionResponse
{
    public string SessionId { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public Dictionary<string, object>? Context { get; set; }
    public bool IsError { get; set; }
    public string? ErrorMessage { get; set; }
}