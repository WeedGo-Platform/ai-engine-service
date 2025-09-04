#!/usr/bin/env python3
"""
Training Impact Test - See Your AI Get Smarter in Real-Time
Run this before and after training to measure improvement
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple
import sys

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
PURPLE = '\033[95m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

API_BASE = "http://localhost:8080/api/v1"

class TrainingImpactTester:
    def __init__(self):
        self.test_queries = [
            # (query, expected_keywords, intent_type)
            ("I'm new to cannabis", ["beginner", "start", "CBD", "low"], "beginner"),
            ("I can't sleep", ["indica", "purple", "CBN", "sleep"], "medical"),
            ("Something for anxiety", ["CBD", "calm", "ratio", "anxiety"], "medical"),
            ("Cheapest option", ["budget", "special", "deal", "$"], "budget"),
            ("Strongest stuff", ["THC", "potent", "%", "strong"], "potency"),
            ("I get paranoid", ["CBD", "balanced", "gentle", "calm"], "safety"),
            ("How much should I take?", ["start", "low", "dose", "wait"], "dosage"),
            ("Do you deliver?", ["delivery", "area", "time", "fee"], "service"),
            ("Tell me about sativa", ["energy", "creative", "daytime", "focus"], "education"),
            ("Something for pain", ["indica", "CBD", "relief", "inflammation"], "medical"),
        ]
        
        self.results_before = []
        self.results_after = []
    
    def test_query(self, query: str) -> Dict:
        """Test a single query against the AI"""
        try:
            start = time.time()
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": query,
                    "customer_id": "test_trainer",
                    "session_id": f"test_{int(time.time())}"
                },
                timeout=10
            )
            response_time = (time.time() - start) * 1000  # Convert to ms
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("message", ""),
                    "confidence": data.get("confidence", 0),
                    "response_time_ms": response_time,
                    "products": data.get("products", []),
                    "quick_replies": data.get("quick_replies", [])
                }
            else:
                return {
                    "success": False,
                    "response": f"Error: {response.status_code}",
                    "confidence": 0,
                    "response_time_ms": response_time,
                    "products": [],
                    "quick_replies": []
                }
        except Exception as e:
            return {
                "success": False,
                "response": str(e),
                "confidence": 0,
                "response_time_ms": 0,
                "products": [],
                "quick_replies": []
            }
    
    def calculate_quality_score(self, response: Dict, expected_keywords: List[str]) -> float:
        """Calculate quality score based on response content"""
        score = 0
        response_text = response.get("response", "").lower()
        
        # Check for expected keywords (40 points)
        keywords_found = sum(1 for keyword in expected_keywords if keyword.lower() in response_text)
        score += (keywords_found / len(expected_keywords)) * 40 if expected_keywords else 0
        
        # Check for specific products mentioned (20 points)
        if response.get("products") or "$" in response_text:
            score += 20
        
        # Check for follow-up question (20 points)
        if "?" in response_text:
            score += 20
        
        # Check confidence level (10 points)
        confidence = response.get("confidence", 0)
        score += confidence * 10
        
        # Response time bonus (10 points if under 3 seconds)
        if 0 < response.get("response_time_ms", 0) < 3000:
            score += 10
        
        return min(score, 100)  # Cap at 100
    
    def run_test_suite(self, test_name: str = "Test") -> Dict:
        """Run all test queries and collect results"""
        print(f"\n{BOLD}Running {test_name}...{RESET}")
        results = []
        
        for query, keywords, intent in self.test_queries:
            print(f"  Testing: '{query[:30]}...'", end="")
            response = self.test_query(query)
            quality = self.calculate_quality_score(response, keywords)
            
            results.append({
                "query": query,
                "intent": intent,
                "response": response,
                "quality_score": quality,
                "expected_keywords": keywords
            })
            
            # Visual feedback
            if quality >= 70:
                print(f" {GREEN}✓ {quality:.0f}%{RESET}")
            elif quality >= 50:
                print(f" {YELLOW}⚡ {quality:.0f}%{RESET}")
            else:
                print(f" {RED}✗ {quality:.0f}%{RESET}")
            
            time.sleep(0.5)  # Avoid overwhelming the API
        
        return {
            "timestamp": datetime.now(),
            "results": results,
            "avg_quality": sum(r["quality_score"] for r in results) / len(results),
            "avg_confidence": sum(r["response"]["confidence"] for r in results) / len(results),
            "avg_response_time": sum(r["response"]["response_time_ms"] for r in results) / len(results),
            "success_rate": sum(1 for r in results if r["response"]["success"]) / len(results) * 100
        }
    
    def print_detailed_comparison(self, before: Dict, after: Dict):
        """Print detailed before/after comparison"""
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}{CYAN}TRAINING IMPACT ANALYSIS{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")
        
        # Overall metrics
        print(f"{BOLD}Overall Performance:{RESET}")
        print(f"  Quality Score: {before['avg_quality']:.1f}% → {after['avg_quality']:.1f}% ", end="")
        quality_change = after['avg_quality'] - before['avg_quality']
        if quality_change > 0:
            print(f"{GREEN}(+{quality_change:.1f}%){RESET}")
        else:
            print(f"{RED}({quality_change:.1f}%){RESET}")
        
        print(f"  Confidence:    {before['avg_confidence']:.2f} → {after['avg_confidence']:.2f} ", end="")
        conf_change = after['avg_confidence'] - before['avg_confidence']
        if conf_change > 0:
            print(f"{GREEN}(+{conf_change:.2f}){RESET}")
        else:
            print(f"{RED}({conf_change:.2f}){RESET}")
        
        print(f"  Response Time: {before['avg_response_time']:.0f}ms → {after['avg_response_time']:.0f}ms ", end="")
        time_change = after['avg_response_time'] - before['avg_response_time']
        if time_change < 0:
            print(f"{GREEN}({time_change:.0f}ms faster){RESET}")
        else:
            print(f"{YELLOW}(+{time_change:.0f}ms slower){RESET}")
        
        # Query-by-query comparison
        print(f"\n{BOLD}Query-by-Query Improvement:{RESET}")
        improvements = []
        
        for i, (b_result, a_result) in enumerate(zip(before['results'], after['results'])):
            improvement = a_result['quality_score'] - b_result['quality_score']
            improvements.append(improvement)
            
            print(f"\n  {BOLD}{i+1}. {b_result['query'][:50]}{RESET}")
            print(f"     Before: {b_result['quality_score']:.0f}% | After: {a_result['quality_score']:.0f}%", end="")
            
            if improvement > 0:
                print(f" {GREEN}(+{improvement:.0f}%){RESET}")
                # Show what improved
                if "$" in a_result['response']['response'] and "$" not in b_result['response']['response']:
                    print(f"     {GREEN}✓ Now includes pricing{RESET}")
                if "?" in a_result['response']['response'] and "?" not in b_result['response']['response']:
                    print(f"     {GREEN}✓ Now asks follow-up questions{RESET}")
                if a_result['response']['products'] and not b_result['response']['products']:
                    print(f"     {GREEN}✓ Now recommends specific products{RESET}")
            elif improvement < 0:
                print(f" {RED}({improvement:.0f}%){RESET}")
                print(f"     {RED}⚠ Response quality decreased{RESET}")
            else:
                print(f" {YELLOW}(No change){RESET}")
        
        # Summary stats
        print(f"\n{BOLD}Training Effectiveness:{RESET}")
        improved = sum(1 for i in improvements if i > 0)
        declined = sum(1 for i in improvements if i < 0)
        unchanged = sum(1 for i in improvements if i == 0)
        
        print(f"  {GREEN}Improved:  {improved}/{len(improvements)} queries{RESET}")
        print(f"  {YELLOW}Unchanged: {unchanged}/{len(improvements)} queries{RESET}")
        print(f"  {RED}Declined:  {declined}/{len(improvements)} queries{RESET}")
        
        avg_improvement = sum(improvements) / len(improvements)
        print(f"\n  {BOLD}Average Improvement: ", end="")
        if avg_improvement > 0:
            print(f"{GREEN}+{avg_improvement:.1f}%{RESET}")
        else:
            print(f"{RED}{avg_improvement:.1f}%{RESET}")
        
        # Training grade
        print(f"\n{BOLD}Training Grade:{RESET} ", end="")
        if avg_improvement >= 20:
            print(f"{GREEN}{BOLD}A+ - Exceptional Training!{RESET} 🌟")
        elif avg_improvement >= 15:
            print(f"{GREEN}A - Excellent Training!{RESET} 🎯")
        elif avg_improvement >= 10:
            print(f"{GREEN}B - Good Training{RESET} 👍")
        elif avg_improvement >= 5:
            print(f"{YELLOW}C - Moderate Training{RESET} 📈")
        elif avg_improvement >= 0:
            print(f"{YELLOW}D - Minimal Impact{RESET} 📊")
        else:
            print(f"{RED}F - Training Made It Worse{RESET} ⚠️")
        
        # Recommendations
        print(f"\n{BOLD}Recommendations:{RESET}")
        if after['avg_quality'] < 60:
            print(f"  {YELLOW}• Add more training examples with specific products{RESET}")
        if after['avg_confidence'] < 0.7:
            print(f"  {YELLOW}• Train more examples for low-confidence intents{RESET}")
        if after['avg_response_time'] > 3000:
            print(f"  {YELLOW}• Reduce Max Tokens to improve response speed{RESET}")
        if improved < len(improvements) / 2:
            print(f"  {YELLOW}• Focus training on queries that didn't improve{RESET}")
        
        if avg_improvement >= 10:
            print(f"\n{GREEN}{BOLD}🎉 Great job! Your training is making the AI significantly smarter!{RESET}")
        elif avg_improvement >= 5:
            print(f"\n{YELLOW}{BOLD}📈 Good progress! Keep training for better results.{RESET}")
        else:
            print(f"\n{RED}{BOLD}⚠️  Limited improvement. Review training examples for quality.{RESET}")

def main():
    print(f"{BOLD}{PURPLE}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          AI TRAINING IMPACT MEASUREMENT TOOL             ║")
    print("║                See Your Training Work!                   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{RESET}")
    
    tester = TrainingImpactTester()
    
    # Run before test
    print(f"\n{BOLD}Phase 1: Testing Current AI Performance{RESET}")
    before_results = tester.run_test_suite("BEFORE Training")
    
    print(f"\n{BOLD}{YELLOW}═══════════════════════════════════════{RESET}")
    print(f"{BOLD}{YELLOW}NOW GO TRAIN YOUR AI!{RESET}")
    print(f"{YELLOW}1. Add training examples in the Admin Portal{RESET}")
    print(f"{YELLOW}2. Upload the POWER_TRAINING_SET.json{RESET}")
    print(f"{YELLOW}3. Apply training{RESET}")
    print(f"{YELLOW}4. Come back and press Enter to test again{RESET}")
    print(f"{BOLD}{YELLOW}═══════════════════════════════════════{RESET}")
    
    input(f"\n{BOLD}Press Enter when you've finished training...{RESET}")
    
    # Run after test
    print(f"\n{BOLD}Phase 2: Testing Improved AI Performance{RESET}")
    after_results = tester.run_test_suite("AFTER Training")
    
    # Show comparison
    tester.print_detailed_comparison(before_results, after_results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"training_impact_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            "before": {
                "avg_quality": before_results['avg_quality'],
                "avg_confidence": before_results['avg_confidence'],
                "avg_response_time": before_results['avg_response_time']
            },
            "after": {
                "avg_quality": after_results['avg_quality'],
                "avg_confidence": after_results['avg_confidence'],
                "avg_response_time": after_results['avg_response_time']
            },
            "improvement": after_results['avg_quality'] - before_results['avg_quality']
        }, f, indent=2)
    
    print(f"\n{BOLD}Results saved to: {filename}{RESET}")
    print(f"\n{BOLD}{GREEN}Training session complete!{RESET} 🚀\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}Error: {str(e)}{RESET}")
        sys.exit(1)