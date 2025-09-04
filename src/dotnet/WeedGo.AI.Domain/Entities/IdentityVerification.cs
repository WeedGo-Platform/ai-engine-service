using System.ComponentModel.DataAnnotations;

namespace WeedGo.AI.Domain.Entities;

/// <summary>
/// Identity verification session
/// </summary>
public class IdentityVerification
{
    public Guid Id { get; set; } = Guid.NewGuid();
    
    [Required]
    public string SessionId { get; set; } = string.Empty;
    
    [Required]
    public Guid TenantId { get; set; }
    
    // Document information (no personal data stored)
    [Required]
    public string DocumentType { get; set; } = string.Empty; // 'drivers_license', 'passport', 'provincial_id'
    
    public string? DocumentRegion { get; set; } // 'ON', 'BC', etc.
    
    // Verification results
    public bool AgeVerified { get; set; } = false;
    public bool IdentityVerified { get; set; } = false;
    public bool FaceMatchVerified { get; set; } = false;
    
    // Confidence scores
    public decimal? AgeVerificationConfidence { get; set; }
    public decimal? IdentityConfidence { get; set; }
    public decimal? FaceMatchConfidence { get; set; }
    
    // Document analysis results
    public bool DocumentValid { get; set; } = false;
    public bool DocumentExpired { get; set; } = true;
    public bool DocumentTampered { get; set; } = false;
    
    // Process metadata
    [Required]
    public string VerificationMethod { get; set; } = string.Empty; // 'ocr_ml', 'manual_review'
    
    public int? ProcessingTimeMs { get; set; }
    
    public string Status { get; set; } = "pending"; // 'pending', 'approved', 'rejected', 'manual_review'
    
    // Privacy (no actual document images stored)
    public string? DocumentHash { get; set; } // Hash of document for duplicate detection
    public string? SelfieHash { get; set; } // Hash of selfie for duplicate detection
    
    // Audit trail
    public string? VerifiedBy { get; set; } // System or operator ID
    public string? VerificationNotes { get; set; }
    
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? CompletedAt { get; set; }
}