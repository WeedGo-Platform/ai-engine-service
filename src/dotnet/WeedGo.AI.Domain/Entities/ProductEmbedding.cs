using System.ComponentModel.DataAnnotations;

namespace WeedGo.AI.Domain.Entities;

/// <summary>
/// Product embeddings for semantic search
/// </summary>
public class ProductEmbedding
{
    public Guid Id { get; set; } = Guid.NewGuid();
    
    [Required]
    public Guid ProductId { get; set; }
    
    [Required]
    public string EmbeddingType { get; set; } = string.Empty; // 'description', 'effects', 'terpenes', 'combined'
    
    [Required]
    public string ModelName { get; set; } = string.Empty;
    
    [Required]
    public string ModelVersion { get; set; } = string.Empty;
    
    public decimal[] EmbeddingVector { get; set; } = Array.Empty<decimal>();
    public int VectorDimension { get; set; }
    
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    // Navigation properties
    public virtual Product Product { get; set; } = null!;
}