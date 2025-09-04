using Serilog;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .WriteTo.Console()
    .WriteTo.File("logs/ai-engine-.txt", rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Host.UseSerilog();

// Add CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// Add connection string
builder.Configuration.AddInMemoryCollection(new[]
{
    new KeyValuePair<string, string?>("ConnectionStrings:DefaultConnection", 
        "Host=localhost;Port=5434;Database=ai_engine;Username=weedgo;Password=your_password_here")
});

var app = builder.Build();

// Configure the HTTP request pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("AllowAll");
app.UseRouting();
app.MapControllers();

// Add a health check endpoint
app.MapGet("/health", () => new { status = "healthy", timestamp = DateTime.UtcNow });

// Add a root endpoint with API info
app.MapGet("/", () => new 
{ 
    service = "WeedGo AI Engine", 
    version = "1.0.0",
    endpoints = new[]
    {
        "/health",
        "/api/simpleproducts",
        "/api/simpleproducts/{id}",
        "/api/simpleproducts/categories",
        "/swagger"
    }
});

try
{
    Log.Information("Starting WeedGo AI Engine API...");
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}