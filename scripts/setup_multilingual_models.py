#!/usr/bin/env python3
"""
Setup script for multilingual model support
Downloads and configures Qwen2.5 for Chinese language support
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
import requests
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultilingualModelSetup:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.models_dir = self.base_dir / "models" / "multilingual"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Model configurations
        self.models = {
            "qwen2.5-7b-instruct": {
                "url": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
                "size": "4.5GB",
                "languages": ["zh", "en", "es", "fr", "ja", "ko", "ar"],
                "filename": "qwen2.5-7b-instruct-q4_k_m.gguf",
                "description": "Best overall multilingual model with excellent Chinese support"
            },
            "chatglm3-6b": {
                "url": "https://huggingface.co/THUDM/chatglm3-6b-gguf/resolve/main/chatglm3-6b-q4_0.gguf",
                "size": "3.5GB",
                "languages": ["zh", "en"],
                "filename": "chatglm3-6b-q4_0.gguf",
                "description": "Optimized for Chinese conversations"
            }
        }
    
    def download_model(self, model_name: str):
        """Download a specific model"""
        if model_name not in self.models:
            logger.error(f"Unknown model: {model_name}")
            return False
        
        model_info = self.models[model_name]
        output_path = self.models_dir / model_info["filename"]
        
        if output_path.exists():
            logger.info(f"Model already exists: {output_path}")
            return True
        
        logger.info(f"Downloading {model_name} ({model_info['size']})...")
        logger.info(f"URL: {model_info['url']}")
        
        try:
            response = requests.get(model_info["url"], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                with tqdm(total=total_size, unit='iB', unit_scale=True) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            logger.info(f"Successfully downloaded: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {model_name}: {e}")
            if output_path.exists():
                output_path.unlink()
            return False
    
    def create_config(self):
        """Create configuration file for multilingual models"""
        config = {
            "models": {
                "qwen": {
                    "path": str(self.models_dir / "qwen2.5-7b-instruct-q4_k_m.gguf"),
                    "languages": ["zh", "ar", "ja", "ko"],
                    "context_size": 4096,
                    "gpu_layers": 35,
                    "threads": 8,
                    "temperature": 0.7,
                    "max_tokens": 512
                },
                "mistral": {
                    "path": str(self.base_dir / "models" / "base" / "mistral-7b-instruct-v0.2.Q4_K_M.gguf"),
                    "languages": ["en", "es", "fr", "pt"],
                    "context_size": 4096,
                    "gpu_layers": 35,
                    "threads": 8,
                    "temperature": 0.7,
                    "max_tokens": 512
                }
            },
            "language_routing": {
                "zh": "qwen",
                "zh-cn": "qwen",
                "zh-tw": "qwen",
                "ar": "qwen",
                "ja": "qwen",
                "ko": "qwen",
                "en": "mistral",
                "es": "mistral",
                "fr": "mistral",
                "pt": "mistral"
            },
            "prompts": {
                "zh": {
                    "system": "你是一个专业的大麻产品顾问。请用中文回答客户关于大麻产品的问题。记住要：1) 提供准确的产品信息 2) 解释不同品种的效果 3) 根据客户需求推荐合适的产品 4) 保持专业和友好的态度",
                    "greeting": "您好！欢迎光临。我可以帮您推荐适合的大麻产品。请问您在寻找什么类型的产品呢？"
                },
                "ar": {
                    "system": "أنت مستشار محترف لمنتجات القنب. يرجى الإجابة على أسئلة العملاء حول منتجات القنب بالعربية.",
                    "greeting": "مرحباً! كيف يمكنني مساعدتك اليوم؟"
                }
            }
        }
        
        config_path = self.base_dir / "config" / "multilingual_models.json"
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created config file: {config_path}")
        return config_path
    
    def test_model(self, model_name: str = "qwen"):
        """Test the multilingual model with Chinese queries"""
        try:
            from llama_cpp import Llama
            
            model_path = self.models_dir / "qwen2.5-7b-instruct-q4_k_m.gguf"
            if not model_path.exists():
                logger.error(f"Model not found: {model_path}")
                return False
            
            logger.info("Loading Qwen model for testing...")
            model = Llama(
                model_path=str(model_path),
                n_ctx=2048,
                n_threads=4,
                n_gpu_layers=0  # CPU only for testing
            )
            
            # Test queries
            test_queries = [
                "最高THC含量的产品是什么？",
                "推荐一些适合新手的产品",
                "indica和sativa有什么区别？"
            ]
            
            for query in test_queries:
                logger.info(f"\nQuery: {query}")
                
                prompt = f"""<|im_start|>system
你是一个专业的大麻产品顾问。请用中文回答客户的问题。
<|im_end|>
<|im_start|>user
{query}
<|im_end|>
<|im_start|>assistant
"""
                
                response = model(
                    prompt,
                    max_tokens=256,
                    temperature=0.7,
                    stop=["<|im_end|>"]
                )
                
                answer = response['choices'][0]['text']
                logger.info(f"Response: {answer[:200]}...")
            
            return True
            
        except ImportError:
            logger.error("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
            return False
        except Exception as e:
            logger.error(f"Model testing failed: {e}")
            return False
    
    def setup_chinese_cannabis_vocabulary(self):
        """Create Chinese cannabis terminology database"""
        vocabulary = {
            "strains": {
                "sativa": {"zh": "萨蒂瓦", "pinyin": "sà dì wǎ", "description": "提神型品种"},
                "indica": {"zh": "印度大麻", "pinyin": "yìn dù dà má", "description": "放松型品种"},
                "hybrid": {"zh": "混合品种", "pinyin": "hùn hé pǐn zhǒng", "description": "混合效果"}
            },
            "products": {
                "flower": {"zh": "花", "pinyin": "huā", "description": "干燥大麻花"},
                "edibles": {"zh": "食用品", "pinyin": "shí yòng pǐn", "description": "可食用产品"},
                "vape": {"zh": "电子烟", "pinyin": "diàn zǐ yān", "description": "蒸汽产品"},
                "concentrate": {"zh": "浓缩物", "pinyin": "nóng suō wù", "description": "高浓度提取物"},
                "pre-roll": {"zh": "预卷烟", "pinyin": "yù juǎn yān", "description": "预先卷好的大麻烟"}
            },
            "effects": {
                "relaxing": {"zh": "放松", "pinyin": "fàng sōng"},
                "energizing": {"zh": "提神", "pinyin": "tí shén"},
                "euphoric": {"zh": "欣快", "pinyin": "xīn kuài"},
                "creative": {"zh": "创造性", "pinyin": "chuàng zào xìng"},
                "focused": {"zh": "专注", "pinyin": "zhuān zhù"},
                "sleepy": {"zh": "困倦", "pinyin": "kùn juàn"}
            },
            "compounds": {
                "THC": {"zh": "四氢大麻酚", "pinyin": "sì qīng dà má fēn", "description": "精神活性成分"},
                "CBD": {"zh": "大麻二酚", "pinyin": "dà má èr fēn", "description": "非精神活性成分"},
                "terpenes": {"zh": "萜烯", "pinyin": "tiē xī", "description": "香味化合物"}
            }
        }
        
        vocab_path = self.base_dir / "data" / "chinese_cannabis_vocabulary.json"
        vocab_path.parent.mkdir(exist_ok=True)
        
        with open(vocab_path, 'w', encoding='utf-8') as f:
            json.dump(vocabulary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created Chinese vocabulary: {vocab_path}")
        return vocabulary

def main():
    """Main setup function"""
    setup = MultilingualModelSetup()
    
    print("\n🌏 WeedGo Multilingual Model Setup")
    print("=" * 50)
    
    # Show available models
    print("\nAvailable models:")
    for name, info in setup.models.items():
        print(f"  • {name}: {info['description']}")
        print(f"    Size: {info['size']}, Languages: {', '.join(info['languages'])}")
    
    # Ask which model to download
    print("\nWhich model would you like to set up?")
    print("1. Qwen2.5-7B (Recommended - Best multilingual)")
    print("2. ChatGLM3-6B (Chinese optimized)")
    print("3. Both")
    print("4. Skip download (configure only)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        setup.download_model("qwen2.5-7b-instruct")
    elif choice == "2":
        setup.download_model("chatglm3-6b")
    elif choice == "3":
        setup.download_model("qwen2.5-7b-instruct")
        setup.download_model("chatglm3-6b")
    
    # Create configuration
    print("\n📝 Creating configuration...")
    setup.create_config()
    
    # Set up vocabulary
    print("\n📚 Setting up Chinese cannabis vocabulary...")
    setup.setup_chinese_cannabis_vocabulary()
    
    # Test if requested
    test = input("\n🧪 Would you like to test the model? (y/n): ").strip().lower()
    if test == 'y':
        setup.test_model()
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Update smart_multilingual_engine.py to use Qwen for Chinese")
    print("2. Restart the AI service")
    print("3. Test with Chinese queries")

if __name__ == "__main__":
    main()