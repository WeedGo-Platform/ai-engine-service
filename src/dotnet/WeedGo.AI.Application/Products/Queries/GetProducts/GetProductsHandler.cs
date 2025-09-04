using MediatR;
using Microsoft.Extensions.Logging;
using WeedGo.AI.Application.Common.Interfaces;
using WeedGo.AI.Application.Common.Models;
using Mapster;

namespace WeedGo.AI.Application.Products.Queries.GetProducts;

/// <summary>
/// Handler for GetProductsQuery
/// </summary>
public class GetProductsHandler : IRequestHandler<GetProductsQuery, PagedResult<ProductDto>>
{
    private readonly IProductRepository _productRepository;
    private readonly ILogger<GetProductsHandler> _logger;

    public GetProductsHandler(
        IProductRepository productRepository,
        ILogger<GetProductsHandler> logger)
    {
        _productRepository = productRepository;
        _logger = logger;
    }

    public async Task<PagedResult<ProductDto>> Handle(GetProductsQuery request, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Getting products with filters: {@Filters}", request);

        try
        {
            PagedResult<Domain.Entities.Product> products;

            // Apply filters based on request
            if (!string.IsNullOrWhiteSpace(request.SearchTerm))
            {
                products = await _productRepository.SearchAsync(
                    request.SearchTerm, 
                    request.PageNumber, 
                    request.PageSize, 
                    cancellationToken);
            }
            else if (!string.IsNullOrWhiteSpace(request.Category))
            {
                products = await _productRepository.GetByCategoryAsync(
                    request.Category, 
                    request.PageNumber, 
                    request.PageSize, 
                    cancellationToken);
            }
            else if (!string.IsNullOrWhiteSpace(request.Brand))
            {
                products = await _productRepository.GetByBrandAsync(
                    request.Brand, 
                    request.PageNumber, 
                    request.PageSize, 
                    cancellationToken);
            }
            else if (request.Effects?.Any() == true)
            {
                products = await _productRepository.GetByEffectsAsync(
                    request.Effects, 
                    request.PageNumber, 
                    request.PageSize, 
                    cancellationToken);
            }
            else if (request.MinThc.HasValue || request.MaxThc.HasValue)
            {
                products = await _productRepository.GetByThcRangeAsync(
                    request.MinThc, 
                    request.MaxThc, 
                    request.PageNumber, 
                    request.PageSize, 
                    cancellationToken);
            }
            else if (request.MinCbd.HasValue || request.MaxCbd.HasValue)
            {
                products = await _productRepository.GetByCbdRangeAsync(
                    request.MinCbd, 
                    request.MaxCbd, 
                    request.PageNumber, 
                    request.PageSize, 
                    cancellationToken);
            }
            else
            {
                products = await _productRepository.GetPagedAsync(
                    request.PageNumber, 
                    request.PageSize, 
                    cancellationToken);
            }

            // Map to DTOs
            var productDtos = products.Items.Adapt<List<ProductDto>>();

            _logger.LogInformation("Retrieved {Count} products out of {Total}", 
                productDtos.Count, products.TotalCount);

            return PagedResult<ProductDto>.Create(
                productDtos, 
                products.TotalCount, 
                products.PageNumber, 
                products.PageSize);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving products with filters: {@Filters}", request);
            throw;
        }
    }
}