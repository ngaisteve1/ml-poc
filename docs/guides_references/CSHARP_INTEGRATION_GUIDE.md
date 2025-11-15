# Azure ML Endpoint Integration Guide for C#/.NET

## ✅ Status: ENDPOINT VERIFIED

- **Endpoint URL**: `https://mlflow-workspace-qzgku.southeastasia.inference.ml.azure.com/score`
- **API Key**: Stored in `.env` (retrieved via configuration)
- **Model Type**: sklearn MultiOutputRegressor (RandomForest)
- **Status**: ✅ Working - Returns Status 200 with predictions
- **Last Test**: 2025-11-12 22:32:19 UTC

## 📊 Model Details

### Input Features (9 required)
```
1. total_files              - Total files in tenant/site
2. avg_file_size_mb        - Average file size in MB
3. pct_pdf                 - Percentage of PDF files
4. pct_docx                - Percentage of DOCX files
5. pct_xlsx                - Percentage of XLSX files
6. pct_other               - Percentage of other file types
7. archive_frequency_per_day - Number of archives per day
8. month_sin               - Sin component of month (for seasonality)
9. month_cos               - Cos component of month (for seasonality)
```

### Output Predictions (2 values)
```
[0] archived_gb_next_period  - Forecasted GB to be archived in next period
[1] savings_gb_next_period   - Forecasted storage savings in GB in next period
```

### Example Prediction
```
Input:  120,000 files, 1.2 MB avg, 45% PDF, 30% DOCX, 15% XLSX, 10% other
        320 archives/day, January
Output: 263.81 GB to archive, 128.96 GB storage savings
```

## 🔧 C# Implementation Guide

### Step 1: Create Azure ML Client Service

**File**: `Navoo.SmartArchive.Business/Services/AzureML/IAzureMLForecastService.cs`

```csharp
namespace Navoo.SmartArchive.Business.Services.AzureML;

/// <summary>
/// Service for calling Azure ML endpoint to forecast archive metrics
/// </summary>
public interface IAzureMLForecastService
{
    /// <summary>
    /// Forecast archive metrics for a tenant/site
    /// </summary>
    Task<ArchiveForecastResult?> ForecastAsync(
        Guid tenantId,
        ArchiveMetrics metrics,
        int monthNumber,
        CancellationToken cancellationToken = default);
}

/// <summary>
/// Input metrics for forecasting
/// </summary>
public class ArchiveMetrics
{
    public long TotalFiles { get; set; }
    public double AverageFileSizeMb { get; set; }
    public double PercentagePdf { get; set; }
    public double PercentageDocx { get; set; }
    public double PercentageXlsx { get; set; }
    public double ArchiveFrequencyPerDay { get; set; }
}

/// <summary>
/// Forecast result from Azure ML
/// </summary>
public class ArchiveForecastResult
{
    public double ArchivedGbNextPeriod { get; set; }
    public double SavingsGbNextPeriod { get; set; }
    public DateTime PredictionDate { get; set; }
}
```

### Step 2: Implement the Service

**File**: `Navoo.SmartArchive.Business/Services/AzureML/AzureMLForecastService.cs`

```csharp
using System.Net.Http.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace Navoo.SmartArchive.Business.Services.AzureML;

public class AzureMLForecastService : IAzureMLForecastService
{
    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;
    private readonly ILogger<AzureMLForecastService> _logger;

    public AzureMLForecastService(
        HttpClient httpClient,
        IConfiguration configuration,
        ILogger<AzureMLForecastService> logger)
    {
        _httpClient = httpClient;
        _configuration = configuration;
        _logger = logger;
    }

    public async Task<ArchiveForecastResult?> ForecastAsync(
        Guid tenantId,
        ArchiveMetrics metrics,
        int monthNumber,
        CancellationToken cancellationToken = default)
    {
        try
        {
            // Validate inputs
            if (metrics == null)
            {
                _logger.LogWarning("Invalid metrics provided for tenant {TenantId}", tenantId);
                return null;
            }

            // Calculate trigonometric features for seasonality
            double monthSin = Math.Sin(2 * Math.PI * monthNumber / 12);
            double monthCos = Math.Cos(2 * Math.PI * monthNumber / 12);

            // Calculate pct_other (percentage of other file types)
            double percentOther = 1.0 - (metrics.PercentagePdf + metrics.PercentageDocx + metrics.PercentageXlsx);
            percentOther = Math.Max(0.0, percentOther); // Ensure non-negative

            // Build request payload (must match model training feature order exactly)
            var payload = new
            {
                input_data = new
                {
                    columns = new[]
                    {
                        "total_files",
                        "avg_file_size_mb",
                        "pct_pdf",
                        "pct_docx",
                        "pct_xlsx",
                        "pct_other",
                        "archive_frequency_per_day",
                        "month_sin",
                        "month_cos"
                    },
                    index = new[] { 0 },
                    data = new[]
                    {
                        new object[]
                        {
                            metrics.TotalFiles,
                            metrics.AverageFileSizeMb,
                            metrics.PercentagePdf,
                            metrics.PercentageDocx,
                            metrics.PercentageXlsx,
                            percentOther,
                            metrics.ArchiveFrequencyPerDay,
                            monthSin,
                            monthCos
                        }
                    }
                }
            };

            // Get endpoint URL and API key from configuration
            var endpointUrl = _configuration["AzureML:EndpointUrl"];
            var apiKey = _configuration["AzureML:ApiKey"];

            if (string.IsNullOrEmpty(endpointUrl) || string.IsNullOrEmpty(apiKey))
            {
                _logger.LogError("Azure ML endpoint configuration missing");
                return null;
            }

            // Add authorization header
            var request = new HttpRequestMessage(HttpMethod.Post, endpointUrl)
            {
                Content = JsonContent.Create(payload)
            };
            request.Headers.Add("Authorization", $"Bearer {apiKey}");
            request.Content.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/json");

            _logger.LogInformation("Calling Azure ML endpoint for tenant {TenantId}", tenantId);

            var response = await _httpClient.SendAsync(request, cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync(cancellationToken);
                _logger.LogError(
                    "Azure ML endpoint returned status {StatusCode}: {ErrorContent}",
                    response.StatusCode,
                    errorContent);
                return null;
            }

            // Parse response: [[archived_gb, savings_gb]]
            var responseData = await response.Content.ReadFromJsonAsync<double[][]>(cancellationToken: cancellationToken);
            
            if (responseData?.Length != 1 || responseData[0].Length != 2)
            {
                _logger.LogError("Unexpected Azure ML response format");
                return null;
            }

            var result = new ArchiveForecastResult
            {
                ArchivedGbNextPeriod = responseData[0][0],
                SavingsGbNextPeriod = responseData[0][1],
                PredictionDate = DateTime.UtcNow
            };

            _logger.LogInformation(
                "Forecast for tenant {TenantId}: {ArchivedGb} GB archived, {SavingsGb} GB savings",
                tenantId,
                result.ArchivedGbNextPeriod,
                result.SavingsGbNextPeriod);

            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling Azure ML endpoint for tenant {TenantId}", tenantId);
            return null;
        }
    }
}
```

### Step 3: Register Service

**File**: `Navoo.SmartArchive.Business/Extensions/ServiceCollectionExtensions.cs`

Add to the service registration:

```csharp
// Add Azure ML Forecast Service
services.AddHttpClient<IAzureMLForecastService, AzureMLForecastService>();
```

### Step 4: Configuration

**File**: `appsettings.json` (or `appsettings.{Environment}.json`)

```json
{
  "AzureML": {
    "EndpointUrl": "https://mlflow-workspace-qzgku.southeastasia.inference.ml.azure.com/score",
    "ApiKey": "${AZURE_ML_API_KEY}"
  }
}
```

Or use environment variables or Azure Key Vault for the API key in production.

### Step 5: Create Controller Service

**File**: `Navoo.SmartArchive.Business/ControllerService/ArchiveForecastControllerService.cs`

```csharp
using AutoMapper;
using Microsoft.Extensions.Logging;
using Navoo.SmartArchive.Business.Services.AzureML;

namespace Navoo.SmartArchive.Business.ControllerService;

public interface IArchiveForecastControllerService
{
    Task<ArchiveForecastResponse> ForecastAsync(
        ArchiveForecastRequest request,
        CancellationToken cancellationToken = default);
}

public class ArchiveForecastControllerService : BaseSecureControllerService, IArchiveForecastControllerService
{
    private readonly IAzureMLForecastService _mlForecastService;
    private readonly IMapper _mapper;
    private readonly ILogger<ArchiveForecastControllerService> _logger;

    public ArchiveForecastControllerService(
        IValidatedSecurityContextProvider securityContext,
        IAzureMLForecastService mlForecastService,
        IMapper mapper,
        ILogger<ArchiveForecastControllerService> logger)
        : base(securityContext)
    {
        _mlForecastService = mlForecastService;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<ArchiveForecastResponse> ForecastAsync(
        ArchiveForecastRequest request,
        CancellationToken cancellationToken = default)
    {
        try
        {
            this.ValidateTenantAccess(request.TenantId);

            var metrics = _mapper.Map<ArchiveMetrics>(request);
            var forecast = await _mlForecastService.ForecastAsync(
                request.TenantId,
                metrics,
                DateTime.Now.Month,
                cancellationToken);

            if (forecast == null)
            {
                return new ArchiveForecastResponse
                {
                    ErrorMessage = "Unable to generate forecast. Please try again later."
                };
            }

            return new ArchiveForecastResponse
            {
                ArchivedGbNextPeriod = forecast.ArchivedGbNextPeriod,
                SavingsGbNextPeriod = forecast.SavingsGbNextPeriod,
                PredictionDate = forecast.PredictionDate
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error in ForecastAsync");
            return new ArchiveForecastResponse
            {
                ErrorMessage = "An error occurred while generating the forecast."
            };
        }
    }
}
```

### Step 6: Create Request/Response Models

**File**: `Navoo.SmartArchive.Models/Requests/ArchiveForecastRequest.cs`

```csharp
using Navoo.Application.Framework.ClientSDK.RequestValidation.Interfaces;

namespace Navoo.SmartArchive.Models.Requests;

public class ArchiveForecastRequest : INavooRequest
{
    public Guid TenantId { get; set; }
    public long TotalFiles { get; set; }
    public double AverageFileSizeMb { get; set; }
    public double PercentagePdf { get; set; }
    public double PercentageDocx { get; set; }
    public double PercentageXlsx { get; set; }
    public double ArchiveFrequencyPerDay { get; set; }
}
```

**File**: `Navoo.SmartArchive.Models/Responses/ArchiveForecastResponse.cs`

```csharp
namespace Navoo.SmartArchive.Models.Responses;

public class ArchiveForecastResponse : IResponse
{
    public double ArchivedGbNextPeriod { get; set; }
    public double SavingsGbNextPeriod { get; set; }
    public DateTime PredictionDate { get; set; }
    public string? ErrorMessage { get; set; }
}
```

### Step 7: Create Controller Endpoint

**File**: `Navoo.SmartArchive.WebAPI/Controllers/ArchiveForecastController.cs`

```csharp
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Navoo.SmartArchive.Business.ControllerService;
using Navoo.SmartArchive.Models.Requests;

namespace Navoo.SmartArchive.WebAPI.Controllers;

[ApiVersion("1.0")]
[ApiController]
[Authorize]
[Route("api/v{version:apiVersion}/[controller]")]
public class ArchiveForecastController : ControllerBase
{
    private readonly IArchiveForecastControllerService _controllerService;
    private readonly ILogger<ArchiveForecastController> _logger;

    public ArchiveForecastController(
        IArchiveForecastControllerService controllerService,
        ILogger<ArchiveForecastController> logger)
    {
        _controllerService = controllerService;
        _logger = logger;
    }

    [HttpPost("forecast")]
    [ProducesResponseType(typeof(ArchiveForecastResponse), StatusCodes.Status200OK)]
    public Task<IActionResult> ForecastAsync(
        [FromBody] ArchiveForecastRequest request,
        CancellationToken cancellationToken)
    {
        return this.ExecuteBusinessLogicAsync(
            () => _controllerService.ForecastAsync(request, cancellationToken),
            _logger);
    }
}
```

## 🧪 Testing the Integration

```csharp
// Example usage
POST /api/v1/archiveforecast/forecast
Content-Type: application/json
Authorization: Bearer {token}

{
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "totalFiles": 120000,
  "averageFileSizeMb": 1.2,
  "percentagePdf": 0.45,
  "percentageDocx": 0.30,
  "percentageXlsx": 0.15,
  "archiveFrequencyPerDay": 320
}

Response (200 OK):
{
  "archivedGbNextPeriod": 263.81,
  "savingsGbNextPeriod": 128.96,
  "predictionDate": "2025-11-12T22:32:19Z"
}
```

## ⚠️ Important Notes

1. **Feature Order**: The feature order in the request MUST match exactly:
   - `total_files, avg_file_size_mb, pct_pdf, pct_docx, pct_xlsx, pct_other, archive_frequency_per_day, month_sin, month_cos`

2. **Calculations Required**:
   - `pct_other = 1.0 - (pct_pdf + pct_docx + pct_xlsx)` (clamped to 0 minimum)
   - `month_sin = Sin(2π × month / 12)`
   - `month_cos = Cos(2π × month / 12)`

3. **API Key Security**:
   - Never commit API key to source control
   - Use Azure Key Vault or environment variables
   - Rotate key regularly

4. **Error Handling**:
   - Service returns `null` on any error
   - Controller service returns error message in response
   - All failures are logged for monitoring

5. **Performance**:
   - Endpoint response time: ~70ms
   - Can be safely called per-request or cached
   - Consider caching results for 1 hour to reduce API calls

## 📚 Files to Create

```
Navoo.SmartArchive.Business/
  Services/
    AzureML/
      IAzureMLForecastService.cs
      AzureMLForecastService.cs
  ControllerService/
    ArchiveForecastControllerService.cs
    Logging/
      ArchiveForecastControllerServiceLoggerExtensions.cs

Navoo.SmartArchive.Models/
  Requests/
    ArchiveForecastRequest.cs
  Responses/
    ArchiveForecastResponse.cs

Navoo.SmartArchive.WebAPI/
  Controllers/
    ArchiveForecastController.cs
```

## Next Steps

1. Create the service files in your project
2. Register the service and HttpClient in dependency injection
3. Add configuration to appsettings.json
4. Create the controller endpoint
5. Add unit tests
6. Test endpoint with production data
