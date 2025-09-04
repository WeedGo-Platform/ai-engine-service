using System.Net.Http.Json;
using Microsoft.Extensions.Logging;
using WeedGo.AI.Application.Common.Interfaces;

namespace WeedGo.AI.Infrastructure.Services;

public class MLServiceClient : IMLServiceClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<MLServiceClient> _logger;

    public MLServiceClient(HttpClient httpClient, ILogger<MLServiceClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }

    public async Task<BudtenderResponse> ChatAsync(BudtenderRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var payload = new
            {
                message = request.Message,
                language = request.Language,
                customer_profile_id = request.CustomerProfileId,
                context = request.Context
            };

            var response = await _httpClient.PostAsJsonAsync("/budtender/chat", payload, cancellationToken);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<BudtenderResponse>(cancellationToken);
            return result ?? new BudtenderResponse("Sorry, I'm not available right now.", request.Language);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing budtender message");
            return new BudtenderResponse("Sorry, I encountered an error.", request.Language);
        }
    }

    public async Task<List<ProductRecommendation>> GetRecommendationsAsync(RecommendationRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/recommendations", request, cancellationToken);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<List<ProductRecommendation>>(cancellationToken);
            return result ?? new List<ProductRecommendation>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting recommendations");
            return new List<ProductRecommendation>();
        }
    }

    public async Task<CustomerRecognitionResponse> RecognizeCustomerAsync(CustomerRecognitionRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/customer/recognize", request, cancellationToken);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<CustomerRecognitionResponse>(cancellationToken);
            return result ?? new CustomerRecognitionResponse(false);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error recognizing customer");
            return new CustomerRecognitionResponse(false);
        }
    }

    public async Task<string> EnrollCustomerAsync(CustomerEnrollmentRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/customer/enroll", request, cancellationToken);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadAsStringAsync();
            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error enrolling customer");
            throw;
        }
    }

    public async Task<IdentityVerificationResponse> VerifyIdentityAsync(IdentityVerificationRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/identity/verify", request, cancellationToken);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<IdentityVerificationResponse>(cancellationToken);
            return result ?? new IdentityVerificationResponse(false, false, false);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error verifying identity");
            return new IdentityVerificationResponse(false, false, false);
        }
    }

    public async Task<AgeVerificationResponse> VerifyAgeAsync(AgeVerificationRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/identity/verify-age", request, cancellationToken);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<AgeVerificationResponse>(cancellationToken);
            return result ?? new AgeVerificationResponse(false);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error verifying age");
            return new AgeVerificationResponse(false);
        }
    }

    public async Task<PricingRecommendation> GetPricingRecommendationAsync(PricingRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/pricing/recommendation", request, cancellationToken);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<PricingRecommendation>(cancellationToken);
            return result ?? new PricingRecommendation(0);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting pricing recommendation");
            return new PricingRecommendation(0);
        }
    }

    public async Task<List<CompetitorPrice>> GetCompetitorPricesAsync(string productId, CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient.GetAsync($"/pricing/competitors/{productId}", cancellationToken);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<List<CompetitorPrice>>(cancellationToken);
            return result ?? new List<CompetitorPrice>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting competitor prices");
            return new List<CompetitorPrice>();
        }
    }

    public async Task<decimal[]> GetProductEmbeddingAsync(string productDescription, CancellationToken cancellationToken = default)
    {
        try
        {
            var request = new { text = productDescription };
            var response = await _httpClient.PostAsJsonAsync("/embeddings/product", request, cancellationToken);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<decimal[]>(cancellationToken);
            return result ?? Array.Empty<decimal>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting product embedding");
            return Array.Empty<decimal>();
        }
    }

    public async Task<List<ProductMatch>> FindSimilarProductsAsync(decimal[] embedding, int count, CancellationToken cancellationToken = default)
    {
        try
        {
            var request = new { embedding = embedding, count = count };
            var response = await _httpClient.PostAsJsonAsync("/embeddings/similar", request, cancellationToken);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<List<ProductMatch>>(cancellationToken);
            return result ?? new List<ProductMatch>();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error finding similar products");
            return new List<ProductMatch>();
        }
    }
}