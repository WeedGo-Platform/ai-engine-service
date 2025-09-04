using MediatR;
using Microsoft.AspNetCore.Mvc;
using Swashbuckle.AspNetCore.Annotations;
using WeedGo.AI.Application.Budtender.Commands.StartConversation;
using WeedGo.AI.Application.Budtender.Commands.SendMessage;
using WeedGo.AI.Application.Budtender.Commands.EndConversation;
using WeedGo.AI.Application.Budtender.Queries.GetConversation;
using WeedGo.AI.Application.Budtender.Queries.GetConversationHistory;

namespace WeedGo.AI.Api.Controllers;

/// <summary>
/// Virtual Budtender API - AI-powered cannabis consultation and recommendations
/// </summary>
[ApiController]
[Route("api/v{version:apiVersion}/[controller]")]
[ApiVersion("1.0")]
[SwaggerTag("Virtual budtender AI conversation and consultation services")]
public class BudtenderController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<BudtenderController> _logger;

    public BudtenderController(IMediator mediator, ILogger<BudtenderController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Start a new conversation with the virtual budtender
    /// </summary>
    /// <param name="command">Conversation initialization parameters</param>
    /// <returns>New conversation session details</returns>
    [HttpPost("conversations")]
    [SwaggerOperation(Summary = "Start conversation", Description = "Initialize a new conversation session with the virtual budtender")]
    [SwaggerResponse(201, "Conversation started", typeof(ConversationSessionDto))]
    [SwaggerResponse(400, "Bad request")]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<ConversationSessionDto>> StartConversation([FromBody] StartConversationCommand command)
    {
        _logger.LogInformation("Starting new budtender conversation. Language: {Language}, CustomerProfile: {CustomerProfile}",
            command.LanguageCode, command.CustomerProfileId);

        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetConversation), new { sessionId = result.SessionId }, result);
    }

    /// <summary>
    /// Send a message to the virtual budtender
    /// </summary>
    /// <param name="sessionId">Conversation session ID</param>
    /// <param name="command">Message content and metadata</param>
    /// <returns>Budtender response with recommendations</returns>
    [HttpPost("conversations/{sessionId}/messages")]
    [SwaggerOperation(Summary = "Send message", Description = "Send a message to the virtual budtender and receive AI-powered response")]
    [SwaggerResponse(200, "Message sent successfully", typeof(BudtenderResponseDto))]
    [SwaggerResponse(404, "Conversation not found")]
    [SwaggerResponse(400, "Bad request")]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<BudtenderResponseDto>> SendMessage(
        string sessionId, 
        [FromBody] SendMessageCommand command)
    {
        _logger.LogInformation("Sending message to budtender. Session: {SessionId}, Message: {Message}",
            sessionId, command.Message);

        command.SessionId = sessionId;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Get conversation details and recent messages
    /// </summary>
    /// <param name="sessionId">Conversation session ID</param>
    /// <returns>Conversation details with message history</returns>
    [HttpGet("conversations/{sessionId}")]
    [SwaggerOperation(Summary = "Get conversation", Description = "Retrieve conversation details and recent message history")]
    [SwaggerResponse(200, "Success", typeof(ConversationDetailDto))]
    [SwaggerResponse(404, "Conversation not found")]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<ConversationDetailDto>> GetConversation(string sessionId)
    {
        _logger.LogInformation("Getting conversation details. Session: {SessionId}", sessionId);

        var query = new GetConversationQuery { SessionId = sessionId };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Get conversation message history
    /// </summary>
    /// <param name="sessionId">Conversation session ID</param>
    /// <param name="page">Page number for pagination</param>
    /// <param name="pageSize">Number of messages per page</param>
    /// <returns>Paginated message history</returns>
    [HttpGet("conversations/{sessionId}/messages")]
    [SwaggerOperation(Summary = "Get message history", Description = "Retrieve paginated conversation message history")]
    [SwaggerResponse(200, "Success", typeof(PagedResult<ConversationMessageDto>))]
    [SwaggerResponse(404, "Conversation not found")]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<PagedResult<ConversationMessageDto>>> GetMessageHistory(
        string sessionId,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20)
    {
        _logger.LogInformation("Getting message history. Session: {SessionId}, Page: {Page}, PageSize: {PageSize}",
            sessionId, page, pageSize);

        var query = new GetConversationHistoryQuery 
        { 
            SessionId = sessionId, 
            Page = page, 
            PageSize = pageSize 
        };
        
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// End a conversation session
    /// </summary>
    /// <param name="sessionId">Conversation session ID</param>
    /// <param name="command">Session closure details</param>
    /// <returns>Conversation summary and statistics</returns>
    [HttpPost("conversations/{sessionId}/end")]
    [SwaggerOperation(Summary = "End conversation", Description = "End a conversation session and provide feedback")]
    [SwaggerResponse(200, "Conversation ended", typeof(ConversationSummaryDto))]
    [SwaggerResponse(404, "Conversation not found")]
    [SwaggerResponse(400, "Bad request")]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<ConversationSummaryDto>> EndConversation(
        string sessionId,
        [FromBody] EndConversationCommand command)
    {
        _logger.LogInformation("Ending conversation. Session: {SessionId}, Rating: {Rating}",
            sessionId, command.Rating);

        command.SessionId = sessionId;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Get supported languages for budtender conversations
    /// </summary>
    /// <returns>List of supported language codes and names</returns>
    [HttpGet("languages")]
    [SwaggerOperation(Summary = "Get supported languages", Description = "Retrieve list of supported languages for budtender conversations")]
    [SwaggerResponse(200, "Success", typeof(IEnumerable<LanguageDto>))]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<IEnumerable<LanguageDto>>> GetSupportedLanguages()
    {
        _logger.LogInformation("Getting supported languages");

        var query = new GetSupportedLanguagesQuery();
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Get conversation analytics and insights
    /// </summary>
    /// <param name="tenantId">Tenant ID for analytics scope</param>
    /// <param name="fromDate">Start date for analytics period</param>
    /// <param name="toDate">End date for analytics period</param>
    /// <returns>Conversation analytics and insights</returns>
    [HttpGet("analytics")]
    [SwaggerOperation(Summary = "Get conversation analytics", Description = "Retrieve conversation analytics and insights for a tenant")]
    [SwaggerResponse(200, "Success", typeof(ConversationAnalyticsDto))]
    [SwaggerResponse(400, "Bad request")]
    [SwaggerResponse(500, "Internal server error")]
    public async Task<ActionResult<ConversationAnalyticsDto>> GetAnalytics(
        [FromQuery] Guid tenantId,
        [FromQuery] DateTime? fromDate = null,
        [FromQuery] DateTime? toDate = null)
    {
        _logger.LogInformation("Getting conversation analytics. Tenant: {TenantId}, From: {FromDate}, To: {ToDate}",
            tenantId, fromDate, toDate);

        var query = new GetConversationAnalyticsQuery 
        { 
            TenantId = tenantId,
            FromDate = fromDate ?? DateTime.UtcNow.AddDays(-30),
            ToDate = toDate ?? DateTime.UtcNow
        };
        
        var result = await _mediator.Send(query);
        return Ok(result);
    }
}