using System.ComponentModel.DataAnnotations;

namespace WeedGo.AI.Domain.Entities;

/// <summary>
/// Individual conversation message
/// </summary>
public class ConversationMessage
{
    public Guid Id { get; set; } = Guid.NewGuid();
    
    [Required]
    public Guid SessionId { get; set; }
    
    // Message details
    public int MessageOrder { get; set; }
    
    [Required]
    public string Sender { get; set; } = string.Empty; // 'customer', 'budtender', 'system'
    
    [Required]
    public string MessageText { get; set; } = string.Empty;
    
    public string? OriginalLanguage { get; set; }
    public string? TranslatedText { get; set; } // If translation was performed
    
    // AI processing
    public string? IntentDetected { get; set; } // 'product_search', 'effect_inquiry', 'price_question', etc.
    public string? EntitiesExtracted { get; set; } // JSON of NLP entities
    public decimal? SentimentScore { get; set; } // -1.0 to 1.0
    public decimal? ConfidenceScore { get; set; }
    
    // Response metadata
    public int? ResponseTimeMs { get; set; }
    public string? ModelUsed { get; set; }
    public string? ModelVersion { get; set; }
    
    // Recommendations in this message
    public List<string> ProductsMentioned { get; set; } = new(); // Product IDs mentioned in response
    
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    // Navigation properties
    public virtual ConversationSession Session { get; set; } = null!;
}