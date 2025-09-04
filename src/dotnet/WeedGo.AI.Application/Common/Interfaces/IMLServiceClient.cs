namespace WeedGo.AI.Application.Common.Interfaces;

/// <summary>
/// ML service client interface for communication with Python ML services
/// </summary>
public interface IMLServiceClient
{
    // Virtual Budtender
    Task<BudtenderResponse> ChatAsync(BudtenderRequest request, CancellationToken cancellationToken = default);
    Task<List<ProductRecommendation>> GetRecommendationsAsync(RecommendationRequest request, CancellationToken cancellationToken = default);
    
    // Customer Recognition
    Task<CustomerRecognitionResponse> RecognizeCustomerAsync(CustomerRecognitionRequest request, CancellationToken cancellationToken = default);
    Task<string> EnrollCustomerAsync(CustomerEnrollmentRequest request, CancellationToken cancellationToken = default);
    
    // Identity Verification
    Task<IdentityVerificationResponse> VerifyIdentityAsync(IdentityVerificationRequest request, CancellationToken cancellationToken = default);
    Task<AgeVerificationResponse> VerifyAgeAsync(AgeVerificationRequest request, CancellationToken cancellationToken = default);
    
    // Pricing Intelligence
    Task<PricingRecommendation> GetPricingRecommendationAsync(PricingRequest request, CancellationToken cancellationToken = default);
    Task<List<CompetitorPrice>> GetCompetitorPricesAsync(string productId, CancellationToken cancellationToken = default);
    
    // Embeddings and Search
    Task<decimal[]> GetProductEmbeddingAsync(string productDescription, CancellationToken cancellationToken = default);
    Task<List<ProductMatch>> FindSimilarProductsAsync(decimal[] embedding, int count, CancellationToken cancellationToken = default);
}

// Request/Response models
public record BudtenderRequest(
    string Message,
    string Language = "en",
    string? CustomerProfileId = null,
    Dictionary<string, object>? Context = null
);

public record BudtenderResponse(
    string Response,
    string Language,
    List<ProductRecommendation>? ProductRecommendations = null,
    string? Intent = null,
    double Confidence = 0.0,
    int ResponseTimeMs = 0
);

public record ProductRecommendation(
    string ProductId,
    string Name,
    string Brand,
    decimal ConfidenceScore,
    string Reason
);

public record RecommendationRequest(
    string? CustomerProfileId = null,
    List<string>? PreferredCategories = null,
    List<string>? PreferredEffects = null,
    decimal? MinThc = null,
    decimal? MaxThc = null,
    decimal? MinCbd = null,
    decimal? MaxCbd = null,
    decimal? MaxPrice = null,
    int Count = 10
);

public record CustomerRecognitionRequest(
    string ImageData, // Base64 encoded
    string TenantId,
    double ConfidenceThreshold = 0.7
);

public record CustomerRecognitionResponse(
    bool Recognized,
    string? CustomerProfileId = null,
    double Confidence = 0.0,
    string? EstimatedAgeRange = null,
    string? EstimatedGender = null
);

public record CustomerEnrollmentRequest(
    string ImageData, // Base64 encoded
    string TenantId,
    bool ConsentGiven = false
);

public record IdentityVerificationRequest(
    string DocumentImageData, // Base64 encoded
    string SelfieImageData, // Base64 encoded
    string DocumentType = "drivers_license",
    string? DocumentRegion = null
);

public record IdentityVerificationResponse(
    bool IdentityVerified,
    bool AgeVerified,
    bool FaceMatchVerified,
    double IdentityConfidence = 0.0,
    double AgeConfidence = 0.0,
    double FaceMatchConfidence = 0.0,
    bool DocumentValid = false,
    bool DocumentExpired = true,
    bool DocumentTampered = false,
    int ProcessingTimeMs = 0,
    string? DocumentHash = null,
    string? SelfieHash = null
);

public record AgeVerificationRequest(
    string DocumentImageData, // Base64 encoded
    string DocumentType = "drivers_license",
    string? DocumentRegion = null
);

public record AgeVerificationResponse(
    bool AgeVerified,
    int? ExtractedAge = null,
    double Confidence = 0.0,
    bool DocumentValid = false,
    bool DocumentExpired = true,
    int ProcessingTimeMs = 0
);

public record PricingRequest(
    string ProductId,
    string Strategy = "competitive", // 'competitive', 'premium', 'value', 'penetration'
    decimal? CurrentPrice = null,
    List<CompetitorPrice>? CompetitorPrices = null
);

public record PricingRecommendation(
    decimal RecommendedPrice,
    decimal? MinPrice = null,
    decimal? MaxPrice = null,
    string Strategy = "",
    double Confidence = 0.0,
    string MarketPosition = "",
    decimal? PredictedDemandChange = null,
    decimal? PredictedRevenueImpact = null
);

public record CompetitorPrice(
    string CompetitorName,
    string ProductName,
    decimal Price,
    string? Size = null,
    bool InStock = true,
    DateTime ScrapedAt = default
);

public record ProductMatch(
    string ProductId,
    string Name,
    string Brand,
    double SimilarityScore
);