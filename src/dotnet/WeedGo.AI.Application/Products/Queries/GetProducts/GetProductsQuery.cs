using MediatR;
using WeedGo.AI.Application.Common.Models;
using WeedGo.AI.Domain.Entities;

namespace WeedGo.AI.Application.Products.Queries.GetProducts;

/// <summary>
/// Query to get paginated products with filtering
/// </summary>
public record GetProductsQuery : IRequest<PagedResult<ProductDto>>
{
    public int PageNumber { get; init; } = 1;
    public int PageSize { get; init; } = 20;
    public string? SearchTerm { get; init; }
    public string? Category { get; init; }
    public string? Brand { get; init; }
    public decimal? MinThc { get; init; }
    public decimal? MaxThc { get; init; }
    public decimal? MinCbd { get; init; }
    public decimal? MaxCbd { get; init; }
    public List<string>? Effects { get; init; }
    public bool? OntarioGrown { get; init; }
    public bool? Craft { get; init; }
    public string? SortBy { get; init; } = "name"; // name, thc, cbd, price, brand
    public bool SortDescending { get; init; } = false;
}

/// <summary>
/// Product DTO for API responses
/// </summary>
public record ProductDto
{
    public Guid Id { get; init; }
    public string OcsItemNumber { get; init; } = string.Empty;
    public string Name { get; init; } = string.Empty;
    public string Brand { get; init; } = string.Empty;
    public string Category { get; init; } = string.Empty;
    public string? SubCategory { get; init; }
    public string? ShortDescription { get; init; }
    public string? Size { get; init; }
    public decimal? ThcMinPercent { get; init; }
    public decimal? ThcMaxPercent { get; init; }
    public decimal? CbdMinPercent { get; init; }
    public decimal? CbdMaxPercent { get; init; }
    public List<string> Terpenes { get; init; } = new();
    public bool OntarioGrown { get; init; }
    public bool Craft { get; init; }
    public string? ImageUrl { get; init; }
    public bool IsActive { get; init; }
    public DateTime CreatedAt { get; init; }
    public List<ProductEffectDto> Effects { get; init; } = new();
    public decimal? CurrentPrice { get; init; }
}

/// <summary>
/// Product effect DTO
/// </summary>
public record ProductEffectDto
{
    public string EffectType { get; init; } = string.Empty;
    public string EffectName { get; init; } = string.Empty;
    public decimal? Intensity { get; init; }
    public decimal? Confidence { get; init; }
    public string Source { get; init; } = string.Empty;
}