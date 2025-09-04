"""
WeedGo AI ML Service - Main gRPC Server

This module provides the main entry point for the AI ML service,
orchestrating all AI capabilities including virtual budtender,
customer recognition, pricing optimization, and identity verification.
"""

import asyncio
import logging
import signal
import sys
from concurrent import futures
from typing import Dict, Any

import grpc
from grpc_health.v1 import health_pb2_grpc
from grpc_health.v1.health import HealthServicer
from prometheus_client import start_http_server

from .config import Settings
from .models import ModelManager
from .services import (
    BudtenderService,
    CustomerRecognitionService,
    PricingService,
    IdentityVerificationService
)
from ..shared.proto import ai_service_pb2_grpc
from ..shared.utils.logging import setup_logging
from ..shared.utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)


class MLServicer(ai_service_pb2_grpc.AIServiceServicer):
    """Main ML service implementing all AI capabilities"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model_manager = ModelManager(settings)
        self.metrics = MetricsCollector()
        
        # Initialize specialized services
        self.budtender = BudtenderService(self.model_manager, settings)
        self.recognition = CustomerRecognitionService(self.model_manager, settings)
        self.pricing = PricingService(self.model_manager, settings)
        self.identity = IdentityVerificationService(self.model_manager, settings)
        
        logger.info("ML Service initialized with all capabilities")
    
    async def initialize(self):
        """Initialize all models and services"""
        logger.info("Loading ML models...")
        
        # Load models asynchronously
        await self.model_manager.load_all_models()
        
        # Initialize services
        await self.budtender.initialize()
        await self.recognition.initialize()
        await self.pricing.initialize()
        await self.identity.initialize()
        
        logger.info("All models and services initialized successfully")
    
    # Virtual Budtender Methods
    async def Chat(self, request, context):
        """Handle conversational AI chat requests"""
        try:
            response = await self.budtender.chat(request)
            self.metrics.increment_counter("chat_requests_total", {"status": "success"})
            return response
        except Exception as e:
            logger.error(f"Chat error: {e}")
            self.metrics.increment_counter("chat_requests_total", {"status": "error"})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.ChatResponse()
    
    async def GetRecommendations(self, request, context):
        """Generate product recommendations"""
        try:
            response = await self.budtender.get_recommendations(request)
            self.metrics.increment_counter("recommendation_requests_total", {"status": "success"})
            return response
        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            self.metrics.increment_counter("recommendation_requests_total", {"status": "error"})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.RecommendationResponse()
    
    # Customer Recognition Methods
    async def IdentifyCustomer(self, request, context):
        """Identify customer from image"""
        try:
            response = await self.recognition.identify_customer(request)
            self.metrics.increment_counter("face_recognition_requests_total", {"status": "success"})
            return response
        except Exception as e:
            logger.error(f"Customer identification error: {e}")
            self.metrics.increment_counter("face_recognition_requests_total", {"status": "error"})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.CustomerIdentificationResponse()
    
    async def EnrollCustomer(self, request, context):
        """Enroll new customer face"""
        try:
            response = await self.recognition.enroll_customer(request)
            self.metrics.increment_counter("face_enrollment_requests_total", {"status": "success"})
            return response
        except Exception as e:
            logger.error(f"Customer enrollment error: {e}")
            self.metrics.increment_counter("face_enrollment_requests_total", {"status": "error"})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.CustomerEnrollmentResponse()
    
    # Pricing Optimization Methods
    async def OptimizePricing(self, request, context):
        """Optimize product pricing"""
        try:
            response = await self.pricing.optimize_pricing(request)
            self.metrics.increment_counter("pricing_optimization_requests_total", {"status": "success"})
            return response
        except Exception as e:
            logger.error(f"Pricing optimization error: {e}")
            self.metrics.increment_counter("pricing_optimization_requests_total", {"status": "error"})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.PricingOptimizationResponse()
    
    async def ScrapeCompetitorPrices(self, request, context):
        """Scrape competitor pricing data"""
        try:
            response = await self.pricing.scrape_competitor_prices(request)
            self.metrics.increment_counter("scraping_requests_total", {"status": "success"})
            return response
        except Exception as e:
            logger.error(f"Price scraping error: {e}")
            self.metrics.increment_counter("scraping_requests_total", {"status": "error"})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.ScrapingResponse()
    
    # Identity Verification Methods
    async def VerifyIdentity(self, request, context):
        """Verify customer identity from ID and selfie"""
        try:
            response = await self.identity.verify_identity(request)
            self.metrics.increment_counter("identity_verification_requests_total", {"status": "success"})
            return response
        except Exception as e:
            logger.error(f"Identity verification error: {e}")
            self.metrics.increment_counter("identity_verification_requests_total", {"status": "error"})
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.IdentityVerificationResponse()
    
    # Model Management Methods
    async def GetModelStatus(self, request, context):
        """Get status of all ML models"""
        try:
            response = await self.model_manager.get_status()
            return response
        except Exception as e:
            logger.error(f"Model status error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.ModelStatusResponse()
    
    async def ReloadModel(self, request, context):
        """Reload a specific model"""
        try:
            response = await self.model_manager.reload_model(request.model_name)
            return response
        except Exception as e:
            logger.error(f"Model reload error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.ModelReloadResponse()


async def serve():
    """Start the gRPC server"""
    settings = Settings()
    setup_logging(settings.log_level)
    
    # Create and initialize the service
    ml_service = MLServicer(settings)
    await ml_service.initialize()
    
    # Create gRPC server
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=settings.max_workers),
        options=[
            ('grpc.keepalive_time_ms', 30000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', True),
            ('grpc.http2.max_pings_without_data', 0),
            ('grpc.http2.min_time_between_pings_ms', 10000),
            ('grpc.http2.min_ping_interval_without_data_ms', 300000),
        ]
    )
    
    # Add services
    ai_service_pb2_grpc.add_AIServiceServicer_to_server(ml_service, server)
    health_pb2_grpc.add_HealthServicer_to_server(HealthServicer(), server)
    
    # Listen on all interfaces
    listen_addr = f'[::]:{settings.grpc_port}'
    server.add_insecure_port(listen_addr)
    
    # Start metrics server
    start_http_server(settings.metrics_port)
    logger.info(f"Metrics server started on port {settings.metrics_port}")
    
    # Start gRPC server
    await server.start()
    logger.info(f"AI ML Service started on {listen_addr}")
    
    # Handle graceful shutdown
    async def shutdown():
        logger.info("Shutting down AI ML Service...")
        await server.stop(grace=30)
        logger.info("AI ML Service stopped")
    
    # Wait for termination signal
    loop = asyncio.get_event_loop()
    for sig in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        await shutdown()


if __name__ == '__main__':
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Service failed to start: {e}")
        sys.exit(1)