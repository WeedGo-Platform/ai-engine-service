using System.ComponentModel.DataAnnotations;

namespace WeedGo.AI.Domain.Entities;

/// <summary>
/// Customer recognition profile (privacy-preserving)
/// </summary>
public class CustomerProfile
{
    public Guid Id { get; set; } = Guid.NewGuid();
    
    [Required]
    public Guid TenantId { get; set; } // Store/tenant identifier
    
    // Biometric data (cancelable/revocable templates)
    public string? FaceTemplateHash { get; set; } // Hashed cancelable biometric template
    
    [Required]
    public string TemplateVersion { get; set; } = "1.0";
    
    [Required]
    public string TemplateAlgorithm { get; set; } = "InsightFace_ArcFace";
    
    // Recognition metadata
    public DateTime FirstSeenAt { get; set; } = DateTime.UtcNow;
    public DateTime LastSeenAt { get; set; } = DateTime.UtcNow;
    public int VisitCount { get; set; } = 1;
    public decimal TotalPurchaseAmount { get; set; } = 0;
    
    // Privacy and consent
    public bool ConsentGiven { get; set; } = false;
    public DateTime? ConsentDate { get; set; }
    public string? ConsentVersion { get; set; }
    public DateTime? DataRetentionExpiresAt { get; set; }
    
    // Demographics (anonymized)
    public string? EstimatedAgeRange { get; set; } // '18-25', '26-35', etc.
    public string? EstimatedGender { get; set; } // Optional, anonymized
    
    // Preferences (learned from behavior)
    public List<string> PreferredCategories { get; set; } = new();
    public List<string> PreferredBrands { get; set; } = new();
    public string? ThcPreferenceRange { get; set; } // 'low', 'medium', 'high'
    public string? CbdPreferenceRange { get; set; }
    public string? PriceSensitivity { get; set; } // 'budget', 'mid-range', 'premium'
    
    // Status
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    
    // Navigation properties
    public virtual ICollection<VisitSession> VisitSessions { get; set; } = new List<VisitSession>();
    public virtual ICollection<ConversationSession> ConversationSessions { get; set; } = new List<ConversationSession>();
}