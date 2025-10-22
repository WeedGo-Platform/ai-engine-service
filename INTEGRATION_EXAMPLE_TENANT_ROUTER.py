"""
Integration Example: Using TenantLLMRouter in SmartAIEngineV5

This example shows how to integrate the tenant-aware router into the existing
SmartAIEngineV5 class for multi-tenant LLM requests.
"""

# Step 1: Import tenant router components
from services.llm_gateway import (
    TenantLLMRouter,
    get_tenant_router,
    complete_for_tenant,
    TaskType,
    RequestContext
)

# Step 2: Initialize tenant router in __init__
class SmartAIEngineV5:
    def __init__(self, ...):
        # ... existing initialization ...
        
        # Add tenant router initialization
        self.tenant_router = None
        self._initialize_tenant_router()
    
    async def _initialize_tenant_router_async(self):
        """Initialize tenant-aware LLM router (async)"""
        try:
            self.tenant_router = await get_tenant_router()
            logger.info("✅ Tenant-aware LLM router initialized")
        except Exception as e:
            logger.error(f"Failed to initialize tenant router: {e}")
            self.tenant_router = None
    
    def _initialize_tenant_router(self):
        """Initialize tenant router (sync wrapper)"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If event loop is running, schedule initialization
                asyncio.create_task(self._initialize_tenant_router_async())
            else:
                # If no loop, run synchronously
                loop.run_until_complete(self._initialize_tenant_router_async())
        except Exception as e:
            logger.warning(f"Could not initialize tenant router synchronously: {e}")
            self.tenant_router = None

# Step 3: Add method for tenant-aware completion
class SmartAIEngineV5:
    async def complete_with_tenant_config(
        self,
        tenant_id: str,
        messages: List[Dict],
        task_type: TaskType = TaskType.CHAT,
        estimated_tokens: int = 500,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Generate completion using tenant's LLM configuration
        
        Args:
            tenant_id: Tenant UUID
            messages: Chat messages in OpenAI format
            task_type: Type of task (CHAT, REASONING, etc.)
            estimated_tokens: Expected token count
            user_id: Optional user UUID
            **kwargs: Additional context parameters
        
        Returns:
            Dictionary with response and metadata
        
        Example:
            result = await engine.complete_with_tenant_config(
                tenant_id="...",
                messages=[
                    {"role": "user", "content": "Recommend products for sleep"}
                ],
                task_type=TaskType.REASONING,
                estimated_tokens=1000,
                user_id="..."
            )
        """
        if not self.tenant_router:
            await self._initialize_tenant_router_async()
        
        if not self.tenant_router:
            raise RuntimeError("Tenant router not available")
        
        try:
            # Create request context
            context = RequestContext(
                task_type=task_type,
                estimated_tokens=estimated_tokens,
                is_production=True,
                **kwargs
            )
            
            # Complete with tenant config
            result = await self.tenant_router.complete_for_tenant(
                tenant_id=tenant_id,
                messages=messages,
                context=context,
                endpoint="/api/chat",  # Adjust as needed
                user_id=user_id
            )
            
            # Convert to engine response format
            return {
                "response": result.content,
                "provider": result.provider,
                "model": result.model,
                "tokens": {
                    "input": result.tokens_input,
                    "output": result.tokens_output,
                    "total": result.tokens_input + result.tokens_output
                },
                "cost": result.cost,
                "latency": result.latency,
                "cached": result.cached,
                "finish_reason": result.finish_reason
            }
            
        except Exception as e:
            logger.error(f"Tenant completion failed: {e}")
            raise

# Step 4: Add usage stats method
class SmartAIEngineV5:
    async def get_tenant_usage_stats(
        self,
        tenant_id: str,
        hours: int = 24
    ) -> Dict:
        """
        Get LLM usage statistics for a tenant
        
        Args:
            tenant_id: Tenant UUID
            hours: Time window in hours
        
        Returns:
            Usage statistics dictionary
        
        Example:
            stats = await engine.get_tenant_usage_stats(
                tenant_id="...",
                hours=24
            )
            
            # Returns:
            {
                "total_requests": 150,
                "total_tokens": 75000,
                "total_cost_usd": 0.0425,
                "by_provider": {
                    "groq": {"requests": 120, "tokens": 60000, "cost_usd": 0.0},
                    "openrouter": {"requests": 30, "tokens": 15000, "cost_usd": 0.0425}
                },
                "by_model": [...]
            }
        """
        if not self.tenant_router:
            await self._initialize_tenant_router_async()
        
        if not self.tenant_router:
            raise RuntimeError("Tenant router not available")
        
        return await self.tenant_router.get_tenant_usage_stats(
            tenant_id=tenant_id,
            hours=hours
        )

# Step 5: Use in existing methods (example)
class SmartAIEngineV5:
    async def handle_product_recommendation_async(
        self,
        tenant_id: str,
        user_query: str,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """
        Handle product recommendation using tenant's LLM config
        """
        # Build messages for LLM
        messages = [
            {
                "role": "system",
                "content": "You are a cannabis product recommendation assistant."
            },
            {
                "role": "user",
                "content": f"Recommend products for: {user_query}"
            }
        ]
        
        # Use tenant-specific LLM configuration
        result = await self.complete_with_tenant_config(
            tenant_id=tenant_id,
            messages=messages,
            task_type=TaskType.REASONING,  # Product recs need reasoning
            estimated_tokens=1000,
            user_id=user_id,
            requires_reasoning=True
        )
        
        # Process result
        return {
            "recommendations": result["response"],
            "metadata": {
                "provider": result["provider"],
                "model": result["model"],
                "cost": result["cost"]
            }
        }

# Step 6: Convenience function for backward compatibility
class SmartAIEngineV5:
    async def chat_completion(
        self,
        tenant_id: str,
        messages: List[Dict],
        user_id: Optional[str] = None
    ):
        """
        Simple chat completion (uses tenant config if available)
        
        Falls back to old behavior if tenant router not available
        """
        if self.tenant_router:
            # Use tenant-specific configuration
            return await self.complete_with_tenant_config(
                tenant_id=tenant_id,
                messages=messages,
                task_type=TaskType.CHAT,
                estimated_tokens=500,
                user_id=user_id
            )
        else:
            # Fallback to old LLMRouter behavior
            if self.llm_router:
                result = await self.llm_router.complete(
                    messages=messages,
                    context=RequestContext(
                        task_type=TaskType.CHAT,
                        estimated_tokens=500
                    )
                )
                return {
                    "response": result.content,
                    "provider": result.provider,
                    "model": result.model
                }
            else:
                raise RuntimeError("No LLM router available")

# Step 7: Example usage in API endpoint
"""
# In api_server.py or similar

@app.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
):
    engine = SmartAIEngineV5()
    
    result = await engine.complete_with_tenant_config(
        tenant_id=tenant_id,
        messages=request.messages,
        task_type=TaskType.CHAT,
        estimated_tokens=500,
        user_id=user_id
    )
    
    return {
        "response": result["response"],
        "metadata": {
            "provider": result["provider"],
            "model": result["model"],
            "tokens": result["tokens"],
            "cost": result["cost"]
        }
    }

@app.get("/api/usage/stats")
async def usage_stats_endpoint(
    tenant_id: str = Depends(get_tenant_id),
    hours: int = 24
):
    engine = SmartAIEngineV5()
    
    stats = await engine.get_tenant_usage_stats(
        tenant_id=tenant_id,
        hours=hours
    )
    
    return stats
"""

# Step 8: Testing
"""
# Test tenant-aware completion
import asyncio
from services.smart_ai_engine_v5 import SmartAIEngineV5

async def test():
    engine = SmartAIEngineV5()
    
    # Test with tenant A
    result_a = await engine.complete_with_tenant_config(
        tenant_id="tenant-a-uuid",
        messages=[{"role": "user", "content": "Hello"}],
        task_type=TaskType.CHAT,
        estimated_tokens=100
    )
    print(f"Tenant A: {result_a['provider']} - {result_a['response']}")
    
    # Test with tenant B
    result_b = await engine.complete_with_tenant_config(
        tenant_id="tenant-b-uuid",
        messages=[{"role": "user", "content": "Hello"}],
        task_type=TaskType.CHAT,
        estimated_tokens=100
    )
    print(f"Tenant B: {result_b['provider']} - {result_b['response']}")
    
    # Get usage stats
    stats_a = await engine.get_tenant_usage_stats("tenant-a-uuid", hours=24)
    print(f"Tenant A usage: {stats_a}")

asyncio.run(test())
"""

# Key Benefits of This Integration:
# 
# 1. **Per-Tenant Configuration**
#    - Each tenant uses their own API tokens
#    - Custom provider preferences respected
#    - Model selection per tenant
#
# 2. **Automatic Usage Tracking**
#    - Every request logged to database
#    - Cost tracking per tenant
#    - Rate limit monitoring
#
# 3. **Backward Compatibility**
#    - Falls back to old LLMRouter if tenant router unavailable
#    - Existing code continues to work
#    - Gradual migration path
#
# 4. **Performance**
#    - Configuration caching (5min TTL)
#    - Connection pooling
#    - Non-blocking usage tracking
#
# 5. **Observability**
#    - Usage stats API endpoint
#    - Real-time cost monitoring
#    - Provider performance tracking
