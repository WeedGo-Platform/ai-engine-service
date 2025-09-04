using System.ComponentModel.DataAnnotations;

namespace WeedGo.AI.Domain.Entities;

/// <summary>
/// Cannabis product entity representing OCS catalogue data
/// </summary>
public class Product
{
    public Guid Id { get; set; } = Guid.NewGuid();
    
    [Required]
    public string OcsItemNumber { get; set; } = string.Empty;
    
    [Required]
    public string OcsVariantNumber { get; set; } = string.Empty;
    
    public long? Gtin { get; set; }
    
    // Basic product information
    [Required]
    public string Name { get; set; } = string.Empty;
    
    [Required]
    public string Brand { get; set; } = string.Empty;
    
    [Required]
    public string SupplierName { get; set; } = string.Empty;
    
    public string? StreetName { get; set; }
    
    // Categories
    [Required]
    public string Category { get; set; } = string.Empty;
    
    public string? SubCategory { get; set; }
    public string? SubSubCategory { get; set; }
    
    // Descriptions
    public string? ShortDescription { get; set; }
    public string? LongDescription { get; set; }
    
    // Product specifications
    public string? Size { get; set; }
    public string? UnitOfMeasure { get; set; }
    public decimal? PackSize { get; set; }
    public decimal? NetWeight { get; set; }
    public string? Color { get; set; }
    
    // Cannabis-specific content
    public decimal? ThcMinPercent { get; set; }
    public decimal? ThcMaxPercent { get; set; }
    public decimal? ThcContentPerUnit { get; set; }
    public decimal? ThcContentPerVolume { get; set; }
    public decimal? ThcMinMgG { get; set; }
    public decimal? ThcMaxMgG { get; set; }
    
    public decimal? CbdMinPercent { get; set; }
    public decimal? CbdMaxPercent { get; set; }
    public decimal? CbdContentPerUnit { get; set; }
    public decimal? CbdContentPerVolume { get; set; }
    public decimal? CbdMinMgG { get; set; }
    public decimal? CbdMaxMgG { get; set; }
    
    // Cannabis characteristics
    public string? PlantType { get; set; }
    public decimal? DriedFlowerEquivalency { get; set; }
    public List<string> Terpenes { get; set; } = new();
    
    // Growing information
    public string? GrowingMethod { get; set; }
    public string? GrowMedium { get; set; }
    public string? GrowMethod { get; set; }
    public string? GrowRegion { get; set; }
    public string? DryingMethod { get; set; }
    public string? TrimmingMethod { get; set; }
    public bool OntarioGrown { get; set; } = false;
    public bool Craft { get; set; } = false;
    
    // Processing information
    public string? ExtractionProcess { get; set; }
    public string? CarrierOil { get; set; }
    
    // Hardware specifications (for vapes, etc.)
    public string? HeatingElementType { get; set; }
    public string? BatteryType { get; set; }
    public bool? RechargeableBattery { get; set; }
    public bool? RemovableBattery { get; set; }
    public bool? ReplacementPartsAvailable { get; set; }
    public bool? TemperatureControl { get; set; }
    public bool? TemperatureDisplay { get; set; }
    public string? Compatibility { get; set; }
    
    // Inventory and logistics
    public string? StockStatus { get; set; }
    public string? InventoryStatus { get; set; }
    public int? ItemsPerRetailPack { get; set; }
    public int? EachesPerInnerPack { get; set; }
    public int? EachesPerMasterCase { get; set; }
    public string? FulfilmentMethod { get; set; }
    public string? DeliveryTier { get; set; }
    
    // Physical dimensions
    public decimal? DimensionWidthCm { get; set; }
    public decimal? DimensionHeightCm { get; set; }
    public decimal? DimensionDepthCm { get; set; }
    public decimal? DimensionVolumeMl { get; set; }
    public decimal? DimensionWeightKg { get; set; }
    
    // Storage and safety
    public string? StorageCriteria { get; set; }
    public List<string> FoodAllergens { get; set; } = new();
    public List<string> Ingredients { get; set; } = new();
    
    // Media
    public string? ImageUrl { get; set; }
    public List<string> AdditionalImages { get; set; } = new();
    
    // Metadata
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    public DateTime LastScrapedAt { get; set; } = DateTime.UtcNow;
    
    // Navigation properties
    public virtual ICollection<ProductEffect> Effects { get; set; } = new List<ProductEffect>();
    public virtual ICollection<ProductEmbedding> Embeddings { get; set; } = new List<ProductEmbedding>();
    public virtual ICollection<ProductPricing> PricingHistory { get; set; } = new List<ProductPricing>();
}