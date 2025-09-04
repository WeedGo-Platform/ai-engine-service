#!/usr/bin/env python3
"""
Test Multi-Model Orchestration
Demonstrates different models' strengths through various tasks
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from services.multi_model_orchestrator import get_orchestrator, TaskType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test prompts for different task types
TEST_PROMPTS = {
    TaskType.MATHEMATICAL: "Solve this equation: x^2 + 5x + 6 = 0. Show your work step by step.",
    
    TaskType.CODING: "Write a Python function to find the nth Fibonacci number using dynamic programming.",
    
    TaskType.MULTILINGUAL: "Translate 'Welcome to our cannabis dispensary' to Spanish, French, and Chinese.",
    
    TaskType.REASONING: "Explain why THC and CBD have different effects on the human body despite coming from the same plant.",
    
    TaskType.ANALYSIS: "Analyze the market trends for cannabis legalization in the US over the past 5 years.",
    
    TaskType.CANNABIS_SPECIFIC: "What's the difference between indica and sativa strains? Which is better for pain relief?",
    
    TaskType.GENERAL: "What are the business hours for most dispensaries?"
}

async def test_individual_models():
    """Test each model individually with appropriate tasks"""
    orchestrator = get_orchestrator()
    
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL MODEL CAPABILITIES")
    print("="*60)
    
    # Test each task type
    for task_type, prompt in TEST_PROMPTS.items():
        print(f"\n### Testing {task_type.value.upper()} task ###")
        print(f"Prompt: {prompt[:100]}...")
        
        try:
            # Process with optimal model
            result = await orchestrator.process_with_optimal_model(prompt, max_tokens=200)
            
            if result.get("response"):
                response_text = result["response"].get("choices", [{}])[0].get("text", "No response")
                print(f"Model Used: {result['model_used']}")
                print(f"Processing Time: {result['processing_time']:.2f}s")
                print(f"Response: {response_text[:200]}...")
            else:
                print(f"Error: No response generated")
                
        except Exception as e:
            print(f"Error testing {task_type.value}: {e}")
        
        print("-" * 40)

async def test_ensemble_inference():
    """Test ensemble inference for complex tasks"""
    orchestrator = get_orchestrator()
    
    print("\n" + "="*60)
    print("TESTING ENSEMBLE INFERENCE")
    print("="*60)
    
    complex_prompt = """
    Create a comprehensive guide for a new cannabis dispensary owner covering:
    1. Legal compliance requirements
    2. Product selection strategies
    3. Customer education approaches
    """
    
    print(f"Complex Prompt: {complex_prompt}")
    
    try:
        # Run ensemble with multiple models
        result = await orchestrator.ensemble_inference(
            complex_prompt,
            models=["mistral_7b_v3", "qwen_7b", "deepseek_coder"],
            aggregation="majority"
        )
        
        if "error" not in result:
            print(f"\nModels Used: {result.get('models_used', [])}")
            print(f"Aggregation Method: {result.get('aggregation_method', 'unknown')}")
            
            if result.get("ensemble_response"):
                response = result["ensemble_response"]
                if isinstance(response, dict):
                    text = response.get("choices", [{}])[0].get("text", "")
                else:
                    text = str(response)
                print(f"\nEnsemble Response:\n{text[:500]}...")
        else:
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"Error in ensemble inference: {e}")

async def test_adaptive_routing():
    """Test adaptive routing with conversation history"""
    orchestrator = get_orchestrator()
    
    print("\n" + "="*60)
    print("TESTING ADAPTIVE ROUTING")
    print("="*60)
    
    # Simulate conversation history
    history = [
        {"prompt": "What is the chemical formula for THC?"},
        {"prompt": "How does THC bind to CB1 receptors?"},
        {"prompt": "What are the therapeutic effects of THC?"}
    ]
    
    next_prompt = "Compare THC with synthetic cannabinoids"
    
    print("Conversation History: Cannabis chemistry questions")
    print(f"Next Prompt: {next_prompt}")
    
    try:
        result = await orchestrator.adaptive_routing(next_prompt, history)
        
        if result.get("response"):
            response_text = result["response"].get("choices", [{}])[0].get("text", "No response")
            print(f"\nModel Selected: {result.get('model_used', 'unknown')}")
            print(f"Task Type Detected: {result.get('task_type', 'unknown')}")
            print(f"Response: {response_text[:300]}...")
        else:
            print("No response generated")
            
    except Exception as e:
        print(f"Error in adaptive routing: {e}")

async def test_performance_comparison():
    """Compare performance across different models"""
    orchestrator = get_orchestrator()
    
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    
    test_prompt = "Explain the entourage effect in cannabis"
    
    models_to_test = ["mistral_7b_v3", "qwen_7b", "phi_mini"]
    
    for model in models_to_test:
        if model not in orchestrator.hot_swap_manager.get_available_models():
            print(f"Skipping {model} - not available")
            continue
            
        print(f"\nTesting {model}...")
        
        try:
            # Swap to specific model
            success = orchestrator.hot_swap_manager.swap_model(model)
            if not success:
                print(f"Failed to load {model}")
                continue
            
            # Generate response
            start_time = asyncio.get_event_loop().time()
            response = await orchestrator.hot_swap_manager.async_generate(
                test_prompt,
                max_tokens=100
            )
            elapsed = asyncio.get_event_loop().time() - start_time
            
            if response:
                text = response.get("choices", [{}])[0].get("text", "No response")
                print(f"Time: {elapsed:.2f}s")
                print(f"Response Quality: {len(text)} chars")
                print(f"Preview: {text[:100]}...")
            else:
                print("No response generated")
                
        except Exception as e:
            print(f"Error testing {model}: {e}")

async def main():
    """Run all tests"""
    
    print("\n" + "="*60)
    print("MULTI-MODEL ORCHESTRATION TEST SUITE")
    print("="*60)
    print("\nThis test demonstrates how different models excel at different tasks")
    print("and how we can intelligently route queries to the optimal model.")
    
    # Run tests
    await test_individual_models()
    await test_ensemble_inference()
    await test_adaptive_routing()
    await test_performance_comparison()
    
    # Get final performance report
    orchestrator = get_orchestrator()
    report = orchestrator.get_performance_report()
    
    print("\n" + "="*60)
    print("FINAL PERFORMANCE REPORT")
    print("="*60)
    
    if report["model_performance"]:
        for model, stats in report["model_performance"].items():
            success_rate = stats["successful_tasks"] / max(stats["total_tasks"], 1)
            avg_time = stats["total_time"] / max(stats["total_tasks"], 1)
            print(f"\n{model}:")
            print(f"  Tasks: {stats['total_tasks']}")
            print(f"  Success Rate: {success_rate:.1%}")
            print(f"  Avg Time: {avg_time:.2f}s")
    else:
        print("No performance data collected")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())