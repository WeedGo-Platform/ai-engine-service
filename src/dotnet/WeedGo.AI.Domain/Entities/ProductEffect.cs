using System.ComponentModel.DataAnnotations;

namespace WeedGo.AI.Domain.Entities;

/// <summary>
/// Product effects and characteristics
/// </summary>
public class ProductEffect
{
    public Guid Id { get; set; } = Guid.NewGuid();
    
    [Required]
    public Guid ProductId { get; set; }
    
    [Required]
    public string EffectType { get; set; } = string.Empty; // 'effect', 'medical_use', 'flavor', 'aroma'
    
    [Required]
    public string EffectName { get; set; } = string.Empty;
    
    public decimal? Intensity { get; set; } // 0.0 to 1.0
    public decimal? Confidence { get; set; } // ML model confidence
    
    [Required]
    public string Source { get; set; } = string.Empty; // 'terpenes', 'strain_data', 'user_reviews', 'ml_prediction'
    
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    // Navigation properties
    public virtual Product Product { get; set; } = null!;
}