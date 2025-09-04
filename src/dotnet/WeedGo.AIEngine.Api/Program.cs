using WeedGo.AIEngine.Api.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title = "WeedGo Virtual Budtender API",
        Version = "v1",
        Description = ".NET wrapper for AI-powered virtual budtender service"
    });
});

// Add memory cache for response caching
builder.Services.AddMemoryCache();

// Configure HttpClient for Python service
builder.Services.AddHttpClient<IVirtualBudtenderService, VirtualBudtenderService>(client =>
{
    client.Timeout = TimeSpan.FromSeconds(30);
    client.DefaultRequestHeaders.Add("Accept", "application/json");
});

// Register services
builder.Services.AddScoped<IVirtualBudtenderService, VirtualBudtenderService>();

// Add CORS for frontend access
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend",
        policy =>
        {
            policy.WithOrigins(
                    "http://localhost:3000",
                    "http://localhost:3001",
                    "http://localhost:3002")
                .AllowAnyHeader()
                .AllowAnyMethod()
                .AllowCredentials();
        });
});

// Add health checks
builder.Services.AddHealthChecks();

// Add logging
builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Logging.AddDebug();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "WeedGo Virtual Budtender API V1");
        c.RoutePrefix = string.Empty; // Serve Swagger UI at root
    });
}

app.UseCors("AllowFrontend");

app.UseRouting();

app.MapControllers();
app.MapHealthChecks("/health");

// Log startup information
var logger = app.Services.GetRequiredService<ILogger<Program>>();
logger.LogInformation("Virtual Budtender API started on port {Port}", 
    builder.Configuration["ASPNETCORE_URLS"] ?? "http://localhost:5021");

app.Run();