using System.ComponentModel.DataAnnotations;

namespace WeedGo.AI.Domain.Entities;

/// <summary>
/// Customer visit session tracking
/// </summary>
public class VisitSession
{
    public Guid Id { get; set; } = Guid.NewGuid();
    
    public Guid? CustomerProfileId { get; set; }
    
    [Required]
    public Guid TenantId { get; set; }
    
    // Session details
    public DateTime SessionStart { get; set; } = DateTime.UtcNow;
    public DateTime? SessionEnd { get; set; }
    public int? DurationSeconds { get; set; }
    
    // Recognition confidence
    public decimal? RecognitionConfidence { get; set; }
    
    [Required]
    public string RecognitionMethod { get; set; } = string.Empty; // 'face_recognition', 'manual_id', 'loyalty_card'
    
    // Interaction data
    public List<string> ProductsViewed { get; set; } = new(); // Product IDs
    public List<string> ProductsPurchased { get; set; } = new(); // Product IDs
    public decimal? TotalPurchaseAmount { get; set; }
    
    // AI interactions
    public int BudtenderConversations { get; set; } = 0;
    public int QuestionsAsked { get; set; } = 0;
    public int RecommendationsGiven { get; set; } = 0;
    public int RecommendationsAccepted { get; set; } = 0;
    
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    // Navigation properties
    public virtual CustomerProfile? CustomerProfile { get; set; }
}