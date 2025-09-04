using Microsoft.AspNetCore.Mvc;
using System.Data;
using Npgsql;

namespace WeedGo.AI.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class SimpleProductsController : ControllerBase
{
    private readonly string _connectionString;
    private readonly ILogger<SimpleProductsController> _logger;

    public SimpleProductsController(IConfiguration configuration, ILogger<SimpleProductsController> logger)
    {
        _connectionString = configuration.GetConnectionString("DefaultConnection")
            ?? "Host=localhost;Port=5434;Database=ai_engine;Username=weedgo;Password=weedgo123";
        _logger = logger;
    }

    [HttpGet]
    public async Task<IActionResult> GetProducts([FromQuery] int page = 1, [FromQuery] int pageSize = 10, [FromQuery] string? search = null)
    {
        try
        {
            using var connection = new NpgsqlConnection(_connectionString);
            await connection.OpenAsync();

            var query = @"
                SELECT id, name, brand, category, sub_category, thc_min_percent, cbd_min_percent, 
                       short_description, image_url, stock_status 
                FROM cannabis_data.products 
                WHERE ($3::text IS NULL OR name ILIKE '%' || $3 || '%' OR brand ILIKE '%' || $3 || '%')
                ORDER BY name 
                LIMIT $1 OFFSET $2";

            using var command = new NpgsqlCommand(query, connection);
            command.Parameters.AddWithValue(pageSize);
            command.Parameters.AddWithValue((page - 1) * pageSize);
            command.Parameters.AddWithValue(search ?? (object)DBNull.Value);

            var products = new List<object>();
            using var reader = await command.ExecuteReaderAsync();
            
            while (await reader.ReadAsync())
            {
                products.Add(new
                {
                    id = reader.GetGuid(0),
                    name = reader.GetString(1),
                    brand = reader.GetString(2),
                    category = reader.GetString(3),
                    subCategory = reader.IsDBNull(4) ? null : reader.GetString(4),
                    thcMin = reader.IsDBNull(5) ? null : reader.GetDecimal(5),
                    cbdMin = reader.IsDBNull(6) ? null : reader.GetDecimal(6),
                    description = reader.IsDBNull(7) ? null : reader.GetString(7),
                    imageUrl = reader.IsDBNull(8) ? null : reader.GetString(8),
                    stockStatus = reader.IsDBNull(9) ? null : reader.GetString(9)
                });
            }

            return Ok(new { products, page, pageSize, count = products.Count });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error fetching products");
            return StatusCode(500, new { error = "Internal server error" });
        }
    }

    [HttpGet("{id:guid}")]
    public async Task<IActionResult> GetProduct(Guid id)
    {
        try
        {
            using var connection = new NpgsqlConnection(_connectionString);
            await connection.OpenAsync();

            var query = @"
                SELECT id, name, brand, category, sub_category, sub_sub_category,
                       thc_min_percent, thc_max_percent, cbd_min_percent, cbd_max_percent,
                       short_description, long_description, size, terpenes, image_url, 
                       stock_status, supplier_name
                FROM cannabis_data.products 
                WHERE id = $1";

            using var command = new NpgsqlCommand(query, connection);
            command.Parameters.AddWithValue(id);

            using var reader = await command.ExecuteReaderAsync();
            
            if (!await reader.ReadAsync())
            {
                return NotFound();
            }

            var product = new
            {
                id = reader.GetGuid(0),
                name = reader.GetString(1),
                brand = reader.GetString(2),
                category = reader.GetString(3),
                subCategory = reader.IsDBNull(4) ? null : reader.GetString(4),
                subSubCategory = reader.IsDBNull(5) ? null : reader.GetString(5),
                thcMin = reader.IsDBNull(6) ? null : reader.GetDecimal(6),
                thcMax = reader.IsDBNull(7) ? null : reader.GetDecimal(7),
                cbdMin = reader.IsDBNull(8) ? null : reader.GetDecimal(8),
                cbdMax = reader.IsDBNull(9) ? null : reader.GetDecimal(9),
                shortDescription = reader.IsDBNull(10) ? null : reader.GetString(10),
                longDescription = reader.IsDBNull(11) ? null : reader.GetString(11),
                size = reader.IsDBNull(12) ? null : reader.GetString(12),
                terpenes = reader.IsDBNull(13) ? null : reader.GetValue(13),
                imageUrl = reader.IsDBNull(14) ? null : reader.GetString(14),
                stockStatus = reader.IsDBNull(15) ? null : reader.GetString(15),
                supplier = reader.IsDBNull(16) ? null : reader.GetString(16)
            };

            return Ok(product);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error fetching product {ProductId}", id);
            return StatusCode(500, new { error = "Internal server error" });
        }
    }

    [HttpGet("categories")]
    public async Task<IActionResult> GetCategories()
    {
        try
        {
            using var connection = new NpgsqlConnection(_connectionString);
            await connection.OpenAsync();

            var query = @"
                SELECT DISTINCT category, COUNT(*) as product_count
                FROM cannabis_data.products 
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY category";

            using var command = new NpgsqlCommand(query, connection);
            var categories = new List<object>();
            using var reader = await command.ExecuteReaderAsync();
            
            while (await reader.ReadAsync())
            {
                categories.Add(new
                {
                    category = reader.GetString(0),
                    productCount = reader.GetInt32(1)
                });
            }

            return Ok(categories);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error fetching categories");
            return StatusCode(500, new { error = "Internal server error" });
        }
    }
}