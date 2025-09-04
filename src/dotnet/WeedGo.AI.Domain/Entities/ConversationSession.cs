using System.ComponentModel.DataAnnotations;

namespace WeedGo.AI.Domain.Entities;

/// <summary>
/// Virtual budtender conversation session
/// </summary>
public class ConversationSession
{
    public Guid Id { get; set; } = Guid.NewGuid();
    
    [Required]
    public string SessionId { get; set; } = string.Empty;
    
    public Guid? CustomerProfileId { get; set; }
    
    [Required]
    public Guid TenantId { get; set; }
    
    // Session configuration
    public string LanguageCode { get; set; } = "en"; // 'en', 'fr', 'es', 'pt', 'ar', 'zh'
    public string PersonalityMode { get; set; } = "professional"; // 'professional', 'casual', 'expert'
    
    // Session metadata
    public DateTime StartedAt { get; set; } = DateTime.UtcNow;
    public DateTime? EndedAt { get; set; }
    public int TotalMessages { get; set; } = 0;
    public int? SessionRating { get; set; } // 1-5 stars from customer
    public string? SessionFeedback { get; set; }
    
    // AI metrics
    public int? AverageResponseTimeMs { get; set; }
    public int RecommendationsMade { get; set; } = 0;
    public List<string> ProductsRecommended { get; set; } = new(); // Product IDs
    
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    // Navigation properties
    public virtual CustomerProfile? CustomerProfile { get; set; }
    public virtual ICollection<ConversationMessage> Messages { get; set; } = new List<ConversationMessage>();
}