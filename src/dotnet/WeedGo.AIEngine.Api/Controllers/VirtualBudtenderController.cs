using Microsoft.AspNetCore.Mvc;
using WeedGo.AIEngine.Api.Services;

namespace WeedGo.AIEngine.Api.Controllers;

[ApiController]
[Route("api/virtual-budtender")]
public class VirtualBudtenderController : ControllerBase
{
    private readonly IVirtualBudtenderService _budtenderService;
    private readonly ILogger<VirtualBudtenderController> _logger;

    public VirtualBudtenderController(
        IVirtualBudtenderService budtenderService,
        ILogger<VirtualBudtenderController> logger)
    {
        _budtenderService = budtenderService;
        _logger = logger;
    }

    /// <summary>
    /// Chat with the virtual budtender
    /// </summary>
    [HttpPost("chat")]
    [ProducesResponseType(typeof(BudtenderResponse), 200)]
    [ProducesResponseType(400)]
    [ProducesResponseType(500)]
    public async Task<IActionResult> Chat([FromBody] ChatRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.Message))
        {
            return BadRequest(new { error = "Message is required" });
        }

        _logger.LogInformation("Chat request received for session {SessionId}", request.SessionId);
        
        var response = await _budtenderService.ChatAsync(request);
        
        if (response.IsError)
        {
            _logger.LogWarning("Chat request failed: {Message}", response.Message);
            return StatusCode(503, response);
        }

        return Ok(response);
    }

    /// <summary>
    /// Get product recommendations based on preferences
    /// </summary>
    [HttpPost("recommend")]
    [ProducesResponseType(typeof(RecommendationResponse), 200)]
    [ProducesResponseType(400)]
    [ProducesResponseType(500)]
    public async Task<IActionResult> GetRecommendations([FromBody] RecommendationRequest request)
    {
        _logger.LogInformation("Recommendation request for user {UserId}, category {Category}", 
            request.UserId, request.Category);
        
        var response = await _budtenderService.GetRecommendationsAsync(request);
        
        if (!string.IsNullOrEmpty(response.ErrorMessage))
        {
            _logger.LogWarning("Recommendation request failed: {Error}", response.ErrorMessage);
            return StatusCode(503, response);
        }

        return Ok(response);
    }

    /// <summary>
    /// Create a new chat session
    /// </summary>
    [HttpPost("session")]
    [ProducesResponseType(typeof(SessionResponse), 201)]
    [ProducesResponseType(400)]
    [ProducesResponseType(500)]
    public async Task<IActionResult> CreateSession([FromBody] SessionRequest request)
    {
        _logger.LogInformation("Creating new session for user {UserId}", request.UserId);
        
        var response = await _budtenderService.CreateSessionAsync(request);
        
        if (response.IsError)
        {
            _logger.LogError("Failed to create session: {Error}", response.ErrorMessage);
            return StatusCode(503, response);
        }

        return CreatedAtAction(nameof(GetSession), new { sessionId = response.SessionId }, response);
    }

    /// <summary>
    /// Get session details
    /// </summary>
    [HttpGet("session/{sessionId}")]
    [ProducesResponseType(typeof(SessionResponse), 200)]
    [ProducesResponseType(404)]
    [ProducesResponseType(500)]
    public async Task<IActionResult> GetSession(string sessionId)
    {
        _logger.LogInformation("Getting session {SessionId}", sessionId);
        
        var response = await _budtenderService.GetSessionAsync(sessionId);
        
        if (response.IsError)
        {
            return NotFound(new { error = response.ErrorMessage });
        }

        return Ok(response);
    }

    /// <summary>
    /// End a chat session
    /// </summary>
    [HttpDelete("session/{sessionId}")]
    [ProducesResponseType(204)]
    [ProducesResponseType(404)]
    [ProducesResponseType(500)]
    public async Task<IActionResult> EndSession(string sessionId)
    {
        _logger.LogInformation("Ending session {SessionId}", sessionId);
        
        var success = await _budtenderService.EndSessionAsync(sessionId);
        
        if (!success)
        {
            return NotFound(new { error = "Session not found" });
        }

        return NoContent();
    }

    /// <summary>
    /// Health check endpoint
    /// </summary>
    [HttpGet("health")]
    [ProducesResponseType(typeof(object), 200)]
    public IActionResult Health()
    {
        return Ok(new
        {
            status = "healthy",
            service = "Virtual Budtender API Wrapper",
            timestamp = DateTime.UtcNow
        });
    }
}