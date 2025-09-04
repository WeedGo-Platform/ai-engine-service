using System.Text;
using Newtonsoft.Json;
using AIEngineTests.Models;

namespace AIEngineTests.Helpers;

public class AIEngineApiClient : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl;

    public AIEngineApiClient(string baseUrl = "http://localhost:8080")
    {
        _baseUrl = baseUrl;
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri(baseUrl)
        };
        _httpClient.DefaultRequestHeaders.Add("Accept", "application/json");
    }

    public async Task<ChatResponse> SendChatMessageAsync(ChatRequest request)
    {
        var json = JsonConvert.SerializeObject(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        var response = await _httpClient.PostAsync("/api/v1/chat", content);
        var responseJson = await response.Content.ReadAsStringAsync();
        
        if (!response.IsSuccessStatusCode)
        {
            throw new HttpRequestException($"Chat API failed with status {response.StatusCode}: {responseJson}");
        }
        
        return JsonConvert.DeserializeObject<ChatResponse>(responseJson) 
            ?? throw new InvalidOperationException("Failed to deserialize response");
    }

    public async Task<AgeVerificationResponse> VerifyAgeAsync(AgeVerificationRequest request)
    {
        var json = JsonConvert.SerializeObject(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        var response = await _httpClient.PostAsync("/api/v1/compliance/verify-age", content);
        var responseJson = await response.Content.ReadAsStringAsync();
        
        if (!response.IsSuccessStatusCode)
        {
            throw new HttpRequestException($"Age verification API failed with status {response.StatusCode}: {responseJson}");
        }
        
        return JsonConvert.DeserializeObject<AgeVerificationResponse>(responseJson) 
            ?? throw new InvalidOperationException("Failed to deserialize response");
    }

    public async Task<bool> CheckHealthAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/health");
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public async Task<string> GetHealthDetailsAsync()
    {
        var response = await _httpClient.GetAsync("/health");
        return await response.Content.ReadAsStringAsync();
    }

    public void Dispose()
    {
        _httpClient?.Dispose();
    }
}