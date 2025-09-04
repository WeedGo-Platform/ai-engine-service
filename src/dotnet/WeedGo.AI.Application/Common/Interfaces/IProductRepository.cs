using WeedGo.AI.Application.Common.Models;
using WeedGo.AI.Domain.Entities;

namespace WeedGo.AI.Application.Common.Interfaces;

/// <summary>
/// Product repository interface
/// </summary>
public interface IProductRepository
{
    Task<Product?> GetByIdAsync(Guid id, CancellationToken cancellationToken = default);
    Task<Product?> GetByOcsItemNumberAsync(string ocsItemNumber, CancellationToken cancellationToken = default);
    Task<PagedResult<Product>> GetPagedAsync(int pageNumber, int pageSize, CancellationToken cancellationToken = default);
    Task<PagedResult<Product>> SearchAsync(string searchTerm, int pageNumber, int pageSize, CancellationToken cancellationToken = default);
    Task<PagedResult<Product>> GetByCategoryAsync(string category, int pageNumber, int pageSize, CancellationToken cancellationToken = default);
    Task<PagedResult<Product>> GetByBrandAsync(string brand, int pageNumber, int pageSize, CancellationToken cancellationToken = default);
    Task<PagedResult<Product>> GetByEffectsAsync(List<string> effects, int pageNumber, int pageSize, CancellationToken cancellationToken = default);
    Task<PagedResult<Product>> GetByThcRangeAsync(decimal? minThc, decimal? maxThc, int pageNumber, int pageSize, CancellationToken cancellationToken = default);
    Task<PagedResult<Product>> GetByCbdRangeAsync(decimal? minCbd, decimal? maxCbd, int pageNumber, int pageSize, CancellationToken cancellationToken = default);
    Task<List<Product>> GetRecommendationsAsync(Guid? customerProfileId, int count, CancellationToken cancellationToken = default);
    Task<List<string>> GetCategoriesAsync(CancellationToken cancellationToken = default);
    Task<List<string>> GetBrandsAsync(CancellationToken cancellationToken = default);
    Task<List<string>> GetTerpenesAsync(CancellationToken cancellationToken = default);
    Task<List<Product>> GetSimilarProductsAsync(Guid productId, int count, CancellationToken cancellationToken = default);
    Task AddAsync(Product product, CancellationToken cancellationToken = default);
    Task UpdateAsync(Product product, CancellationToken cancellationToken = default);
    Task DeleteAsync(Guid id, CancellationToken cancellationToken = default);
}