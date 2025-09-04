using Microsoft.EntityFrameworkCore;
using WeedGo.AI.Domain.Entities;

namespace WeedGo.AI.Infrastructure.Data;

/// <summary>
/// AI Engine database context
/// </summary>
public class AIEngineDbContext : DbContext
{
    public AIEngineDbContext(DbContextOptions<AIEngineDbContext> options) : base(options)
    {
    }

    // Cannabis Data
    public DbSet<Product> Products { get; set; }
    public DbSet<ProductEffect> ProductEffects { get; set; }
    public DbSet<ProductEmbedding> ProductEmbeddings { get; set; }
    public DbSet<ProductPricing> ProductPricing { get; set; }

    // Customer Analytics
    public DbSet<CustomerProfile> CustomerProfiles { get; set; }
    public DbSet<VisitSession> VisitSessions { get; set; }
    public DbSet<ConversationSession> ConversationSessions { get; set; }
    public DbSet<ConversationMessage> ConversationMessages { get; set; }

    // Identity Verification
    public DbSet<IdentityVerification> IdentityVerifications { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Configure schemas
        modelBuilder.HasDefaultSchema("ai_engine");

        // Configure Product entity
        modelBuilder.Entity<Product>(entity =>
        {
            entity.ToTable("products", "cannabis_data");
            entity.HasKey(e => e.Id);
            
            // Indexes
            entity.HasIndex(e => e.OcsItemNumber).IsUnique();
            entity.HasIndex(e => e.OcsVariantNumber).IsUnique();
            entity.HasIndex(e => e.Brand);
            entity.HasIndex(e => e.Category);
            entity.HasIndex(e => new { e.ThcMinPercent, e.ThcMaxPercent });
            entity.HasIndex(e => new { e.CbdMinPercent, e.CbdMaxPercent });
            entity.HasIndex(e => e.IsActive);

            // Configure properties
            entity.Property(e => e.OcsItemNumber)
                .HasColumnName("ocs_item_number")
                .HasMaxLength(50)
                .IsRequired();

            entity.Property(e => e.OcsVariantNumber)
                .HasColumnName("ocs_variant_number")
                .HasMaxLength(100)
                .IsRequired();

            entity.Property(e => e.Gtin).HasColumnName("gtin");
            entity.Property(e => e.Name).HasColumnName("name").HasMaxLength(500).IsRequired();
            entity.Property(e => e.Brand).HasColumnName("brand").HasMaxLength(200).IsRequired();
            entity.Property(e => e.SupplierName).HasColumnName("supplier_name").HasMaxLength(200).IsRequired();
            entity.Property(e => e.StreetName).HasColumnName("street_name").HasMaxLength(500);
            
            entity.Property(e => e.Category).HasColumnName("category").HasMaxLength(100).IsRequired();
            entity.Property(e => e.SubCategory).HasColumnName("sub_category").HasMaxLength(100);
            entity.Property(e => e.SubSubCategory).HasColumnName("sub_sub_category").HasMaxLength(100);
            
            entity.Property(e => e.ShortDescription).HasColumnName("short_description").HasColumnType("text");
            entity.Property(e => e.LongDescription).HasColumnName("long_description").HasColumnType("text");
            
            entity.Property(e => e.Size).HasColumnName("size").HasMaxLength(50);
            entity.Property(e => e.UnitOfMeasure).HasColumnName("unit_of_measure").HasMaxLength(20);
            entity.Property(e => e.PackSize).HasColumnName("pack_size").HasPrecision(10, 2);
            entity.Property(e => e.NetWeight).HasColumnName("net_weight").HasPrecision(10, 4);
            entity.Property(e => e.Color).HasColumnName("color").HasMaxLength(100);
            
            // THC properties
            entity.Property(e => e.ThcMinPercent).HasColumnName("thc_min_percent").HasPrecision(5, 2);
            entity.Property(e => e.ThcMaxPercent).HasColumnName("thc_max_percent").HasPrecision(5, 2);
            entity.Property(e => e.ThcContentPerUnit).HasColumnName("thc_content_per_unit").HasPrecision(10, 4);
            entity.Property(e => e.ThcContentPerVolume).HasColumnName("thc_content_per_volume").HasPrecision(10, 4);
            entity.Property(e => e.ThcMinMgG).HasColumnName("thc_min_mg_g").HasPrecision(10, 4);
            entity.Property(e => e.ThcMaxMgG).HasColumnName("thc_max_mg_g").HasPrecision(10, 4);
            
            // CBD properties
            entity.Property(e => e.CbdMinPercent).HasColumnName("cbd_min_percent").HasPrecision(5, 2);
            entity.Property(e => e.CbdMaxPercent).HasColumnName("cbd_max_percent").HasPrecision(5, 2);
            entity.Property(e => e.CbdContentPerUnit).HasColumnName("cbd_content_per_unit").HasPrecision(10, 4);
            entity.Property(e => e.CbdContentPerVolume).HasColumnName("cbd_content_per_volume").HasPrecision(10, 4);
            entity.Property(e => e.CbdMinMgG).HasColumnName("cbd_min_mg_g").HasPrecision(10, 4);
            entity.Property(e => e.CbdMaxMgG).HasColumnName("cbd_max_mg_g").HasPrecision(10, 4);
            
            // Cannabis characteristics
            entity.Property(e => e.PlantType).HasColumnName("plant_type").HasMaxLength(50);
            entity.Property(e => e.DriedFlowerEquivalency).HasColumnName("dried_flower_equivalency").HasPrecision(10, 2);
            
            // Configure arrays for PostgreSQL
            entity.Property(e => e.Terpenes)
                .HasColumnName("terpenes")
                .HasColumnType("text[]");
                
            // Growing information
            entity.Property(e => e.GrowingMethod).HasColumnName("growing_method").HasMaxLength(100);
            entity.Property(e => e.GrowMedium).HasColumnName("grow_medium").HasMaxLength(100);
            entity.Property(e => e.GrowMethod).HasColumnName("grow_method").HasMaxLength(100);
            entity.Property(e => e.GrowRegion).HasColumnName("grow_region").HasMaxLength(200);
            entity.Property(e => e.DryingMethod).HasColumnName("drying_method").HasMaxLength(100);
            entity.Property(e => e.TrimmingMethod).HasColumnName("trimming_method").HasMaxLength(100);
            entity.Property(e => e.OntarioGrown).HasColumnName("ontario_grown").HasDefaultValue(false);
            entity.Property(e => e.Craft).HasColumnName("craft").HasDefaultValue(false);
            
            // Processing information
            entity.Property(e => e.ExtractionProcess).HasColumnName("extraction_process").HasMaxLength(200);
            entity.Property(e => e.CarrierOil).HasColumnName("carrier_oil").HasMaxLength(100);
            
            // Hardware specifications
            entity.Property(e => e.HeatingElementType).HasColumnName("heating_element_type").HasMaxLength(100);
            entity.Property(e => e.BatteryType).HasColumnName("battery_type").HasMaxLength(100);
            entity.Property(e => e.RechargeableBattery).HasColumnName("rechargeable_battery");
            entity.Property(e => e.RemovableBattery).HasColumnName("removable_battery");
            entity.Property(e => e.ReplacementPartsAvailable).HasColumnName("replacement_parts_available");
            entity.Property(e => e.TemperatureControl).HasColumnName("temperature_control");
            entity.Property(e => e.TemperatureDisplay).HasColumnName("temperature_display");
            entity.Property(e => e.Compatibility).HasColumnName("compatibility").HasColumnType("text");
            
            // Inventory and logistics
            entity.Property(e => e.StockStatus).HasColumnName("stock_status").HasMaxLength(20);
            entity.Property(e => e.InventoryStatus).HasColumnName("inventory_status").HasMaxLength(50);
            entity.Property(e => e.ItemsPerRetailPack).HasColumnName("items_per_retail_pack");
            entity.Property(e => e.EachesPerInnerPack).HasColumnName("eaches_per_inner_pack");
            entity.Property(e => e.EachesPerMasterCase).HasColumnName("eaches_per_master_case");
            entity.Property(e => e.FulfilmentMethod).HasColumnName("fulfilment_method").HasMaxLength(50);
            entity.Property(e => e.DeliveryTier).HasColumnName("delivery_tier").HasMaxLength(50);
            
            // Physical dimensions
            entity.Property(e => e.DimensionWidthCm).HasColumnName("dimension_width_cm").HasPrecision(8, 4);
            entity.Property(e => e.DimensionHeightCm).HasColumnName("dimension_height_cm").HasPrecision(8, 4);
            entity.Property(e => e.DimensionDepthCm).HasColumnName("dimension_depth_cm").HasPrecision(8, 4);
            entity.Property(e => e.DimensionVolumeMl).HasColumnName("dimension_volume_ml").HasPrecision(10, 4);
            entity.Property(e => e.DimensionWeightKg).HasColumnName("dimension_weight_kg").HasPrecision(8, 4);
            
            // Storage and safety
            entity.Property(e => e.StorageCriteria).HasColumnName("storage_criteria").HasColumnType("text");
            entity.Property(e => e.FoodAllergens).HasColumnName("food_allergens").HasColumnType("text[]");
            entity.Property(e => e.Ingredients).HasColumnName("ingredients").HasColumnType("text[]");
            
            // Media
            entity.Property(e => e.ImageUrl).HasColumnName("image_url").HasColumnType("text");
            entity.Property(e => e.AdditionalImages).HasColumnName("additional_images").HasColumnType("text[]");
            
            // Metadata
            entity.Property(e => e.IsActive).HasColumnName("is_active").HasDefaultValue(true);
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").HasDefaultValueSql("NOW()");
            entity.Property(e => e.UpdatedAt).HasColumnName("updated_at").HasDefaultValueSql("NOW()");
            entity.Property(e => e.LastScrapedAt).HasColumnName("last_scraped_at").HasDefaultValueSql("NOW()");

            // Relationships
            entity.HasMany(e => e.Effects)
                .WithOne(e => e.Product)
                .HasForeignKey(e => e.ProductId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasMany(e => e.Embeddings)
                .WithOne(e => e.Product)
                .HasForeignKey(e => e.ProductId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasMany(e => e.PricingHistory)
                .WithOne(e => e.Product)
                .HasForeignKey(e => e.ProductId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Configure ProductEffect entity
        modelBuilder.Entity<ProductEffect>(entity =>
        {
            entity.ToTable("product_effects", "cannabis_data");
            entity.HasKey(e => e.Id);
            
            entity.Property(e => e.ProductId).HasColumnName("product_id").IsRequired();
            entity.Property(e => e.EffectType).HasColumnName("effect_type").HasMaxLength(50).IsRequired();
            entity.Property(e => e.EffectName).HasColumnName("effect_name").HasMaxLength(200).IsRequired();
            entity.Property(e => e.Intensity).HasColumnName("intensity").HasPrecision(3, 2);
            entity.Property(e => e.Confidence).HasColumnName("confidence").HasPrecision(3, 2);
            entity.Property(e => e.Source).HasColumnName("source").HasMaxLength(50).IsRequired();
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").HasDefaultValueSql("NOW()");
        });

        // Configure ProductEmbedding entity
        modelBuilder.Entity<ProductEmbedding>(entity =>
        {
            entity.ToTable("product_embeddings", "ai_engine");
            entity.HasKey(e => e.Id);
            
            entity.HasIndex(e => new { e.ProductId, e.EmbeddingType, e.ModelName, e.ModelVersion }).IsUnique();
            
            entity.Property(e => e.ProductId).HasColumnName("product_id").IsRequired();
            entity.Property(e => e.EmbeddingType).HasColumnName("embedding_type").HasMaxLength(50).IsRequired();
            entity.Property(e => e.ModelName).HasColumnName("model_name").HasMaxLength(100).IsRequired();
            entity.Property(e => e.ModelVersion).HasColumnName("model_version").HasMaxLength(50).IsRequired();
            entity.Property(e => e.EmbeddingVector).HasColumnName("embedding_vector").HasColumnType("decimal(8,6)[]");
            entity.Property(e => e.VectorDimension).HasColumnName("vector_dimension").IsRequired();
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").HasDefaultValueSql("NOW()");
        });

        // Configure ProductPricing entity
        modelBuilder.Entity<ProductPricing>(entity =>
        {
            entity.ToTable("product_pricing", "cannabis_data");
            entity.HasKey(e => e.Id);
            
            entity.HasIndex(e => e.ProductId);
            entity.HasIndex(e => e.CreatedAt);
            
            entity.Property(e => e.ProductId).HasColumnName("product_id").IsRequired();
            entity.Property(e => e.OcsItemNumber).HasColumnName("ocs_item_number").HasMaxLength(50).IsRequired();
            entity.Property(e => e.Price).HasColumnName("price").HasPrecision(10, 2).IsRequired();
            entity.Property(e => e.Currency).HasColumnName("currency").HasMaxLength(3).HasDefaultValue("CAD");
            entity.Property(e => e.PricePerGram).HasColumnName("price_per_gram").HasPrecision(10, 2);
            entity.Property(e => e.DiscountPercent).HasColumnName("discount_percent").HasPrecision(5, 2);
            entity.Property(e => e.PromotionType).HasColumnName("promotion_type").HasMaxLength(100);
            entity.Property(e => e.CompetitorStore).HasColumnName("competitor_store").HasMaxLength(200);
            entity.Property(e => e.PriceSource).HasColumnName("price_source").HasMaxLength(100).IsRequired();
            entity.Property(e => e.ValidFrom).HasColumnName("valid_from").HasDefaultValueSql("NOW()");
            entity.Property(e => e.ValidTo).HasColumnName("valid_to");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").HasDefaultValueSql("NOW()");
        });

        // Configure CustomerProfile entity
        modelBuilder.Entity<CustomerProfile>(entity =>
        {
            entity.ToTable("customer_profiles", "customer_analytics");
            entity.HasKey(e => e.Id);
            
            entity.HasIndex(e => e.TenantId);
            entity.HasIndex(e => e.FaceTemplateHash).IsUnique();
            
            entity.Property(e => e.TenantId).HasColumnName("tenant_id").IsRequired();
            entity.Property(e => e.FaceTemplateHash).HasColumnName("face_template_hash").HasMaxLength(128);
            entity.Property(e => e.TemplateVersion).HasColumnName("template_version").HasMaxLength(20).IsRequired();
            entity.Property(e => e.TemplateAlgorithm).HasColumnName("template_algorithm").HasMaxLength(50).IsRequired();
            
            entity.Property(e => e.FirstSeenAt).HasColumnName("first_seen_at").HasDefaultValueSql("NOW()");
            entity.Property(e => e.LastSeenAt).HasColumnName("last_seen_at").HasDefaultValueSql("NOW()");
            entity.Property(e => e.VisitCount).HasColumnName("visit_count").HasDefaultValue(1);
            entity.Property(e => e.TotalPurchaseAmount).HasColumnName("total_purchase_amount").HasPrecision(12, 2).HasDefaultValue(0);
            
            entity.Property(e => e.ConsentGiven).HasColumnName("consent_given").HasDefaultValue(false);
            entity.Property(e => e.ConsentDate).HasColumnName("consent_date");
            entity.Property(e => e.ConsentVersion).HasColumnName("consent_version").HasMaxLength(20);
            entity.Property(e => e.DataRetentionExpiresAt).HasColumnName("data_retention_expires_at");
            
            entity.Property(e => e.EstimatedAgeRange).HasColumnName("estimated_age_range").HasMaxLength(20);
            entity.Property(e => e.EstimatedGender).HasColumnName("estimated_gender").HasMaxLength(20);
            
            entity.Property(e => e.PreferredCategories).HasColumnName("preferred_categories").HasColumnType("text[]");
            entity.Property(e => e.PreferredBrands).HasColumnName("preferred_brands").HasColumnType("text[]");
            entity.Property(e => e.ThcPreferenceRange).HasColumnName("thc_preference_range").HasMaxLength(20);
            entity.Property(e => e.CbdPreferenceRange).HasColumnName("cbd_preference_range").HasMaxLength(20);
            entity.Property(e => e.PriceSensitivity).HasColumnName("price_sensitivity").HasMaxLength(20);
            
            entity.Property(e => e.IsActive).HasColumnName("is_active").HasDefaultValue(true);
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").HasDefaultValueSql("NOW()");
            entity.Property(e => e.UpdatedAt).HasColumnName("updated_at").HasDefaultValueSql("NOW()");

            // Relationships
            entity.HasMany(e => e.VisitSessions)
                .WithOne(e => e.CustomerProfile)
                .HasForeignKey(e => e.CustomerProfileId)
                .OnDelete(DeleteBehavior.SetNull);

            entity.HasMany(e => e.ConversationSessions)
                .WithOne(e => e.CustomerProfile)
                .HasForeignKey(e => e.CustomerProfileId)
                .OnDelete(DeleteBehavior.SetNull);
        });

        // Configure other entities...
        ConfigureConversationEntities(modelBuilder);
        ConfigureIdentityEntities(modelBuilder);
    }

    private void ConfigureConversationEntities(ModelBuilder modelBuilder)
    {
        // Configure ConversationSession entity
        modelBuilder.Entity<ConversationSession>(entity =>
        {
            entity.ToTable("conversation_sessions", "ai_engine");
            entity.HasKey(e => e.Id);
            
            entity.HasIndex(e => e.SessionId).IsUnique();
            entity.HasIndex(e => e.CustomerProfileId);
            entity.HasIndex(e => e.TenantId);
            
            entity.Property(e => e.SessionId).HasColumnName("session_id").HasMaxLength(100).IsRequired();
            entity.Property(e => e.CustomerProfileId).HasColumnName("customer_profile_id");
            entity.Property(e => e.TenantId).HasColumnName("tenant_id").IsRequired();
            
            entity.Property(e => e.LanguageCode).HasColumnName("language_code").HasMaxLength(10).HasDefaultValue("en");
            entity.Property(e => e.PersonalityMode).HasColumnName("personality_mode").HasMaxLength(50).HasDefaultValue("professional");
            
            entity.Property(e => e.StartedAt).HasColumnName("started_at").HasDefaultValueSql("NOW()");
            entity.Property(e => e.EndedAt).HasColumnName("ended_at");
            entity.Property(e => e.TotalMessages).HasColumnName("total_messages").HasDefaultValue(0);
            entity.Property(e => e.SessionRating).HasColumnName("session_rating");
            entity.Property(e => e.SessionFeedback).HasColumnName("session_feedback").HasColumnType("text");
            
            entity.Property(e => e.AverageResponseTimeMs).HasColumnName("average_response_time_ms");
            entity.Property(e => e.RecommendationsMade).HasColumnName("recommendations_made").HasDefaultValue(0);
            entity.Property(e => e.ProductsRecommended).HasColumnName("products_recommended").HasColumnType("text[]");
            
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").HasDefaultValueSql("NOW()");

            // Relationships
            entity.HasMany(e => e.Messages)
                .WithOne(e => e.Session)
                .HasForeignKey(e => e.SessionId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Configure ConversationMessage entity
        modelBuilder.Entity<ConversationMessage>(entity =>
        {
            entity.ToTable("conversation_messages", "ai_engine");
            entity.HasKey(e => e.Id);
            
            entity.HasIndex(e => new { e.SessionId, e.MessageOrder }).IsUnique();
            
            entity.Property(e => e.SessionId).HasColumnName("session_id").IsRequired();
            entity.Property(e => e.MessageOrder).HasColumnName("message_order").IsRequired();
            entity.Property(e => e.Sender).HasColumnName("sender").HasMaxLength(20).IsRequired();
            entity.Property(e => e.MessageText).HasColumnName("message_text").HasColumnType("text").IsRequired();
            entity.Property(e => e.OriginalLanguage).HasColumnName("original_language").HasMaxLength(10);
            entity.Property(e => e.TranslatedText).HasColumnName("translated_text").HasColumnType("text");
            
            entity.Property(e => e.IntentDetected).HasColumnName("intent_detected").HasMaxLength(100);
            entity.Property(e => e.EntitiesExtracted).HasColumnName("entities_extracted").HasColumnType("jsonb");
            entity.Property(e => e.SentimentScore).HasColumnName("sentiment_score").HasPrecision(3, 2);
            entity.Property(e => e.ConfidenceScore).HasColumnName("confidence_score").HasPrecision(5, 4);
            
            entity.Property(e => e.ResponseTimeMs).HasColumnName("response_time_ms");
            entity.Property(e => e.ModelUsed).HasColumnName("model_used").HasMaxLength(100);
            entity.Property(e => e.ModelVersion).HasColumnName("model_version").HasMaxLength(50);
            
            entity.Property(e => e.ProductsMentioned).HasColumnName("products_mentioned").HasColumnType("text[]");
            
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").HasDefaultValueSql("NOW()");
        });
    }

    private void ConfigureIdentityEntities(ModelBuilder modelBuilder)
    {
        // Configure IdentityVerification entity
        modelBuilder.Entity<IdentityVerification>(entity =>
        {
            entity.ToTable("identity_verifications", "ai_engine");
            entity.HasKey(e => e.Id);
            
            entity.HasIndex(e => e.SessionId).IsUnique();
            entity.HasIndex(e => e.TenantId);
            
            entity.Property(e => e.SessionId).HasColumnName("session_id").HasMaxLength(100).IsRequired();
            entity.Property(e => e.TenantId).HasColumnName("tenant_id").IsRequired();
            
            entity.Property(e => e.DocumentType).HasColumnName("document_type").HasMaxLength(50).IsRequired();
            entity.Property(e => e.DocumentRegion).HasColumnName("document_region").HasMaxLength(50);
            
            entity.Property(e => e.AgeVerified).HasColumnName("age_verified").HasDefaultValue(false);
            entity.Property(e => e.IdentityVerified).HasColumnName("identity_verified").HasDefaultValue(false);
            entity.Property(e => e.FaceMatchVerified).HasColumnName("face_match_verified").HasDefaultValue(false);
            
            entity.Property(e => e.AgeVerificationConfidence).HasColumnName("age_verification_confidence").HasPrecision(5, 4);
            entity.Property(e => e.IdentityConfidence).HasColumnName("identity_confidence").HasPrecision(5, 4);
            entity.Property(e => e.FaceMatchConfidence).HasColumnName("face_match_confidence").HasPrecision(5, 4);
            
            entity.Property(e => e.DocumentValid).HasColumnName("document_valid").HasDefaultValue(false);
            entity.Property(e => e.DocumentExpired).HasColumnName("document_expired").HasDefaultValue(true);
            entity.Property(e => e.DocumentTampered).HasColumnName("document_tampered").HasDefaultValue(false);
            
            entity.Property(e => e.VerificationMethod).HasColumnName("verification_method").HasMaxLength(50).IsRequired();
            entity.Property(e => e.ProcessingTimeMs).HasColumnName("processing_time_ms");
            entity.Property(e => e.Status).HasColumnName("status").HasMaxLength(20).HasDefaultValue("pending");
            
            entity.Property(e => e.DocumentHash).HasColumnName("document_hash").HasMaxLength(128);
            entity.Property(e => e.SelfieHash).HasColumnName("selfie_hash").HasMaxLength(128);
            
            entity.Property(e => e.VerifiedBy).HasColumnName("verified_by").HasMaxLength(100);
            entity.Property(e => e.VerificationNotes).HasColumnName("verification_notes").HasColumnType("text");
            
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").HasDefaultValueSql("NOW()");
            entity.Property(e => e.CompletedAt).HasColumnName("completed_at");
        });
    }
}