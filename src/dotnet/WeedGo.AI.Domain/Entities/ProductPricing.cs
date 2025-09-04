using System.ComponentModel.DataAnnotations;

namespace WeedGo.AI.Domain.Entities;

/// <summary>
/// Product pricing history and competitor data
/// </summary>
public class ProductPricing
{
    public Guid Id { get; set; } = Guid.NewGuid();
    
    [Required]
    public Guid ProductId { get; set; }
    
    [Required]
    public string OcsItemNumber { get; set; } = string.Empty;
    
    [Required]
    public decimal Price { get; set; }
    
    public string Currency { get; set; } = "CAD";
    public decimal? PricePerGram { get; set; }
    public decimal? DiscountPercent { get; set; }
    public string? PromotionType { get; set; }
    public string? CompetitorStore { get; set; }
    
    [Required]
    public string PriceSource { get; set; } = string.Empty; // 'ocs', 'competitor_scrape', 'manual'
    
    public DateTime ValidFrom { get; set; } = DateTime.UtcNow;
    public DateTime? ValidTo { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    // Navigation properties
    public virtual Product Product { get; set; } = null!;
}