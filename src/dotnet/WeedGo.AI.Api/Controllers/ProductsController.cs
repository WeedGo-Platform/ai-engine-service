using MediatR;
using Microsoft.AspNetCore.Mvc;
using Swashbuckle.AspNetCore.Annotations;
using WeedGo.AI.Application.Products.Queries.GetProducts;
using WeedGo.AI.Application.Products.Queries.GetProductById;
using WeedGo.AI.Application.Products.Queries.SearchProducts;
using WeedGo.AI.Application.Products.Queries.GetSimilarProducts;
using WeedGo.AI.Application.Common.Models;

namespace WeedGo.AI.Api.Controllers;

/// <summary>
/// Cannabis Products API - Manages product catalog and search functionality
/// </summary>
[ApiController]
[Route("api/v{version:apiVersion}/[controller]")]
[ApiVersion("1.0")]
[SwaggerTag("Cannabis product catalog and search operations")]
public class ProductsController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<ProductsController> _logger;

    public ProductsController(IMediator mediator, ILogger<ProductsController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Get paginated list of cannabis products
    /// </summary>
    /// <param name="query">Query parameters for filtering and pagination</param>
    /// <returns>Paginated list of products</returns>
    [HttpGet]
    [SwaggerOperation(Summary = "Get products", Description = "Retrieve a paginated list of cannabis products with optional filtering")]
    [SwaggerResponse(200, "Success", typeof(PagedResult<ProductDto>))]
    [SwaggerResponse(400, "Bad request")]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<PagedResult<ProductDto>>> GetProducts([FromQuery] GetProductsQuery query)
    {
        _logger.LogInformation("Getting products with filters: Category={Category}, Brand={Brand}, Page={Page}, PageSize={PageSize}",
            query.Category, query.Brand, query.Page, query.PageSize);

        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Get a specific product by ID
    /// </summary>
    /// <param name="id">Product ID</param>
    /// <returns>Product details</returns>
    [HttpGet("{id:guid}")]
    [SwaggerOperation(Summary = "Get product by ID", Description = "Retrieve detailed information about a specific cannabis product")]
    [SwaggerResponse(200, "Success", typeof(ProductDetailDto))]
    [SwaggerResponse(404, "Product not found")]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<ProductDetailDto>> GetProductById(Guid id)
    {
        _logger.LogInformation("Getting product by ID: {ProductId}", id);

        var query = new GetProductByIdQuery { Id = id };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Search products using natural language or keywords
    /// </summary>
    /// <param name="query">Search query parameters</param>
    /// <returns>Search results with relevance scoring</returns>
    [HttpPost("search")]
    [SwaggerOperation(Summary = "Search products", Description = "Search cannabis products using natural language queries, keywords, or filters")]
    [SwaggerResponse(200, "Success", typeof(ProductSearchResultDto))]
    [SwaggerResponse(400, "Bad request")]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<ProductSearchResultDto>> SearchProducts([FromBody] SearchProductsQuery query)
    {
        _logger.LogInformation("Searching products with query: {SearchTerm}", query.SearchTerm);

        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Get similar products using AI-powered recommendations
    /// </summary>
    /// <param name="productId">Base product ID</param>
    /// <param name="limit">Maximum number of similar products to return</param>
    /// <returns>List of similar products with similarity scores</returns>
    [HttpGet("{productId:guid}/similar")]
    [SwaggerOperation(Summary = "Get similar products", Description = "Find similar cannabis products using AI-powered vector similarity")]
    [SwaggerResponse(200, "Success", typeof(IEnumerable<SimilarProductDto>))]
    [SwaggerResponse(404, "Product not found")]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<IEnumerable<SimilarProductDto>>> GetSimilarProducts(
        Guid productId, 
        [FromQuery] int limit = 10)
    {
        _logger.LogInformation("Getting similar products for ID: {ProductId}, Limit: {Limit}", productId, limit);

        var query = new GetSimilarProductsQuery 
        { 
            ProductId = productId, 
            Limit = limit 
        };
        
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Get product categories and subcategories
    /// </summary>
    /// <returns>Hierarchical list of product categories</returns>
    [HttpGet("categories")]
    [SwaggerOperation(Summary = "Get product categories", Description = "Retrieve all available product categories and subcategories")]
    [SwaggerResponse(200, "Success", typeof(IEnumerable<ProductCategoryDto>))]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<IEnumerable<ProductCategoryDto>>> GetCategories()
    {
        _logger.LogInformation("Getting product categories");

        var query = new GetProductCategoriesQuery();
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Get product brands
    /// </summary>
    /// <returns>List of available brands</returns>
    [HttpGet("brands")]
    [SwaggerOperation(Summary = "Get product brands", Description = "Retrieve all available cannabis brands")]
    [SwaggerResponse(200, "Success", typeof(IEnumerable<string>))]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<IEnumerable<string>>> GetBrands()
    {
        _logger.LogInformation("Getting product brands");

        var query = new GetProductBrandsQuery();
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Get product recommendations based on filters and preferences
    /// </summary>
    /// <param name="query">Recommendation parameters</param>
    /// <returns>Personalized product recommendations</returns>
    [HttpPost("recommendations")]
    [SwaggerOperation(Summary = "Get product recommendations", Description = "Get AI-powered product recommendations based on preferences and filters")]
    [SwaggerResponse(200, "Success", typeof(IEnumerable<RecommendedProductDto>))]
    [SwaggerResponse(400, "Bad request")]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<IEnumerable<RecommendedProductDto>>> GetRecommendations([FromBody] GetProductRecommendationsQuery query)
    {
        _logger.LogInformation("Getting product recommendations for preferences: THC={ThcPreference}, CBD={CbdPreference}, Effects={Effects}",
            query.ThcPreference, query.CbdPreference, string.Join(", ", query.DesiredEffects ?? Array.Empty<string>()));

        var result = await _mediator.Send(query);
        return Ok(result);
    }
}