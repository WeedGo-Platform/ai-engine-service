#!/usr/bin/env python3
"""
Test Voice System
Comprehensive test of voice endpoints and functionality
"""
import asyncio
import requests
import json
import base64
import numpy as np
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "http://localhost:5024/api/voice"

class VoiceSystemTester:
    """Test voice system functionality"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.test_results = {}
        
    def generate_test_audio(self, duration_seconds: float = 1.0) -> bytes:
        """Generate test audio data"""
        sample_rate = 16000
        samples = int(duration_seconds * sample_rate)
        
        # Generate a simple sine wave
        t = np.linspace(0, duration_seconds, samples)
        frequency = 440  # A4 note
        audio = np.sin(2 * np.pi * frequency * t)
        
        # Add some noise to simulate speech
        noise = np.random.normal(0, 0.05, samples)
        audio = audio + noise
        
        # Convert to int16
        audio_int16 = (audio * 32767).astype(np.int16)
        
        return audio_int16.tobytes()
    
    def test_status_endpoint(self):
        """Test /status endpoint"""
        logger.info("\n🔍 Testing /status endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/status")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Status: {data['status']}")
            logger.info(f"   Models: STT={data['models']['stt']['available']}, "
                       f"TTS={data['models']['tts']['available']}, "
                       f"VAD={data['models']['vad']['available']}")
            
            self.test_results["status"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ Status test failed: {e}")
            self.test_results["status"] = f"FAIL: {e}"
            return False
    
    def test_configure_endpoint(self):
        """Test /configure endpoint"""
        logger.info("\n🔧 Testing /configure endpoint...")
        
        config = {
            "domain": "budtender",
            "voice_speed": 1.1,
            "voice_pitch": -1.0,
            "enable_interruption": True,
            "enable_backchanneling": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/configure",
                json=config
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Configuration updated: {data['updates']}")
            
            self.test_results["configure"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ Configure test failed: {e}")
            self.test_results["configure"] = f"FAIL: {e}"
            return False
    
    def test_transcribe_endpoint(self):
        """Test /transcribe endpoint"""
        logger.info("\n🎤 Testing /transcribe endpoint...")
        
        # Generate test audio
        audio_data = self.generate_test_audio(2.0)
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        request_data = {
            "audio_data": audio_b64,
            "format": "wav",
            "domain": "budtender"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/transcribe",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Transcription: {data.get('transcription', {}).get('text', 'N/A')}")
            
            self.test_results["transcribe"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ Transcribe test failed: {e}")
            self.test_results["transcribe"] = f"FAIL: {e}"
            return False
    
    def test_synthesize_endpoint(self):
        """Test /synthesize endpoint"""
        logger.info("\n🔊 Testing /synthesize endpoint...")
        
        request_data = {
            "text": "Hello, welcome to the cannabis dispensary. How can I help you today?",
            "domain": "budtender",
            "emotion": "friendly"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/synthesize",
                json=request_data
            )
            response.raise_for_status()
            
            # Check if we got audio data
            content_type = response.headers.get('content-type', '')
            if 'audio' in content_type:
                logger.info(f"✅ TTS synthesis successful, received {len(response.content)} bytes")
                
                # Save audio for inspection
                with open("test_speech.wav", "wb") as f:
                    f.write(response.content)
                logger.info("   Audio saved to test_speech.wav")
            else:
                logger.warning("⚠️  No audio data received")
            
            self.test_results["synthesize"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ Synthesize test failed: {e}")
            self.test_results["synthesize"] = f"FAIL: {e}"
            return False
    
    def test_conversation_endpoint(self):
        """Test /conversation endpoint"""
        logger.info("\n💬 Testing /conversation endpoint...")
        
        # Generate test audio
        audio_data = self.generate_test_audio(3.0)
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        request_data = {
            "audio_data": audio_b64,
            "session_id": "test_session_123",
            "domain": "budtender",
            "metadata": {
                "user_id": "test_user",
                "location": "US"
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/conversation",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Conversation processed:")
            logger.info(f"   User text: {data.get('user_text', 'N/A')}")
            logger.info(f"   AI response: {data.get('ai_text', 'N/A')[:100]}...")
            logger.info(f"   Audio response: {'Yes' if data.get('audio_response') else 'No'}")
            
            self.test_results["conversation"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ Conversation test failed: {e}")
            self.test_results["conversation"] = f"FAIL: {e}"
            return False
    
    def test_performance_endpoint(self):
        """Test /performance endpoint"""
        logger.info("\n📊 Testing /performance endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/performance")
            response.raise_for_status()
            
            data = response.json()
            logger.info("✅ Performance metrics:")
            logger.info(f"   STT latency: {data['performance']['stt']['expected_latency_ms']}ms")
            logger.info(f"   TTS latency: {data['performance']['tts']['expected_latency_ms']}ms")
            logger.info(f"   Optimizations: {data['optimization']}")
            
            self.test_results["performance"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            self.test_results["performance"] = f"FAIL: {e}"
            return False
    
    def test_domains_endpoint(self):
        """Test /domains endpoint"""
        logger.info("\n🌍 Testing /domains endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/domains")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Available domains: {data['available_domains']}")
            logger.info(f"   Current domain: {data['current_domain']}")
            
            self.test_results["domains"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ Domains test failed: {e}")
            self.test_results["domains"] = f"FAIL: {e}"
            return False
    
    def test_calibrate_endpoint(self):
        """Test /calibrate endpoint"""
        logger.info("\n🎛️ Testing /calibrate endpoint...")
        
        try:
            response = requests.post(f"{self.base_url}/calibrate")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Calibration complete:")
            logger.info(f"   Noise level: {data['calibration']['noise_level']}")
            logger.info(f"   Recommendations: {data['recommendations']}")
            
            self.test_results["calibrate"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ Calibrate test failed: {e}")
            self.test_results["calibrate"] = f"FAIL: {e}"
            return False
    
    def test_latency(self):
        """Test system latency"""
        logger.info("\n⚡ Testing latency...")
        
        # Generate test audio
        audio_data = self.generate_test_audio(1.0)
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        latencies = []
        
        for i in range(5):
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.base_url}/transcribe",
                    json={
                        "audio_data": audio_b64,
                        "format": "wav"
                    }
                )
                response.raise_for_status()
                
                latency = (time.time() - start_time) * 1000
                latencies.append(latency)
                logger.info(f"   Request {i+1}: {latency:.1f}ms")
                
            except Exception as e:
                logger.error(f"   Request {i+1} failed: {e}")
        
        if latencies:
            avg_latency = np.mean(latencies)
            logger.info(f"✅ Average latency: {avg_latency:.1f}ms")
            
            if avg_latency < 200:
                logger.info("   🎯 Excellent! Under 200ms target")
            elif avg_latency < 500:
                logger.info("   ✓ Good! Under 500ms")
            else:
                logger.warning("   ⚠️ Latency above 500ms")
            
            self.test_results["latency"] = f"PASS: {avg_latency:.1f}ms"
        else:
            self.test_results["latency"] = "FAIL: No successful requests"
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("="*60)
        logger.info("🎙️ VOICE SYSTEM TEST SUITE")
        logger.info("="*60)
        
        # Run tests
        self.test_status_endpoint()
        self.test_configure_endpoint()
        self.test_transcribe_endpoint()
        self.test_synthesize_endpoint()
        self.test_conversation_endpoint()
        self.test_performance_endpoint()
        self.test_domains_endpoint()
        self.test_calibrate_endpoint()
        self.test_latency()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*60)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results.items():
            status = "✅" if result == "PASS" or result.startswith("PASS:") else "❌"
            logger.info(f"{status} {test_name}: {result}")
            
            if result == "PASS" or result.startswith("PASS:"):
                passed += 1
            else:
                failed += 1
        
        logger.info(f"\n✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        
        if failed == 0:
            logger.info("\n🎉 All tests passed! Voice system is ready!")
        else:
            logger.warning(f"\n⚠️ {failed} test(s) failed. Check the logs above.")

def main():
    """Main entry point"""
    tester = VoiceSystemTester()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        logger.info("✅ Voice API server is running")
    except:
        logger.error("❌ Voice API server is not running!")
        logger.info("Start the server with: python api_server.py")
        return
    
    # Run tests
    tester.run_all_tests()

if __name__ == "__main__":
    main()