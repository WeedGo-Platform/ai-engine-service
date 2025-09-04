using AIEngineTests.Helpers;

namespace AIEngineTests.Tests;

public class ApiTestFixture : IDisposable
{
    public AIEngineApiClient Client { get; }

    public ApiTestFixture()
    {
        // Use environment variable or default to localhost
        var apiUrl = Environment.GetEnvironmentVariable("AI_ENGINE_API_URL") ?? "http://localhost:8080";
        Client = new AIEngineApiClient(apiUrl);

        // Wait for API to be ready
        WaitForApiToBeReady().GetAwaiter().GetResult();
    }

    private async Task WaitForApiToBeReady()
    {
        var maxRetries = 30;
        var retryCount = 0;

        while (retryCount < maxRetries)
        {
            if (await Client.CheckHealthAsync())
            {
                return;
            }

            retryCount++;
            await Task.Delay(1000);
        }

        throw new InvalidOperationException($"API at {Client} did not become ready after {maxRetries} seconds");
    }

    public void Dispose()
    {
        Client?.Dispose();
    }
}