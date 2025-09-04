using System.Net;
using System.Text.Json;
using FluentValidation;

namespace WeedGo.AI.Api.Middleware;

/// <summary>
/// Global exception handling middleware
/// </summary>
public class ExceptionHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlingMiddleware> _logger;

    public ExceptionHandlingMiddleware(RequestDelegate next, ILogger<ExceptionHandlingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An unhandled exception occurred");
            await HandleExceptionAsync(context, ex);
        }
    }

    private static async Task HandleExceptionAsync(HttpContext context, Exception exception)
    {
        var response = context.Response;
        response.ContentType = "application/json";

        var result = exception switch
        {
            ValidationException validationEx => new
            {
                statusCode = (int)HttpStatusCode.BadRequest,
                message = "Validation failed",
                errors = validationEx.Errors.Select(e => new { e.PropertyName, e.ErrorMessage })
            },
            
            KeyNotFoundException => new
            {
                statusCode = (int)HttpStatusCode.NotFound,
                message = "Resource not found"
            },
            
            UnauthorizedAccessException => new
            {
                statusCode = (int)HttpStatusCode.Unauthorized,
                message = "Unauthorized access"
            },
            
            ArgumentException argEx => new
            {
                statusCode = (int)HttpStatusCode.BadRequest,
                message = argEx.Message
            },
            
            InvalidOperationException invOpEx => new
            {
                statusCode = (int)HttpStatusCode.BadRequest,
                message = invOpEx.Message
            },
            
            _ => new
            {
                statusCode = (int)HttpStatusCode.InternalServerError,
                message = "An internal server error occurred"
            }
        };

        response.StatusCode = result.statusCode;

        var jsonResult = JsonSerializer.Serialize(result, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        });

        await response.WriteAsync(jsonResult);
    }
}