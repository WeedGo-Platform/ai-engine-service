# Multilingual Models & Chinese Language Support Guide

## 🎯 Overview
This guide covers offline multilingual LLMs and language adapter training for the WeedGo AI Engine, with special focus on Chinese language support.

## 📊 Offline Multilingual Models Comparison

### 1. **Qwen Series (Alibaba)** ⭐ RECOMMENDED FOR CHINESE
- **Qwen2.5-7B-Instruct** 
  - Excellent Chinese & English support
  - Size: 7B parameters (4-bit quantized: ~4GB)
  - Languages: Chinese, English + 27 others
  - GGUF format available for llama.cpp
  - Performance: Near GPT-3.5 level for Chinese
  ```bash
  # Download Qwen2.5 GGUF
  wget https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf
  ```

### 2. **ChatGLM Series (Tsinghua)** ⭐ EXCELLENT FOR CHINESE
- **ChatGLM3-6B**
  - Optimized for Chinese conversations
  - Size: 6B parameters (INT4: ~3GB)
  - Bilingual: Chinese + English
  - Built-in tool calling capability
  ```python
  # Can be quantized for llama.cpp
  from transformers import AutoTokenizer, AutoModel
  model = AutoModel.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True)
  ```

### 3. **Baichuan Series** 
- **Baichuan2-7B-Chat**
  - Strong Chinese capabilities
  - Size: 7B parameters
  - Trained on 2.6T tokens (1.4T Chinese)
  - Commercial friendly license

### 4. **BLOOM Series (BigScience)** 
- **BLOOMZ-7B**
  - Supports 46 languages including Chinese
  - Size: 7B parameters
  - Good for multilingual but not Chinese-optimized
  - GGUF available

### 5. **mT5 (Google)**
- **mT5-large**
  - Supports 101 languages
  - Size: 1.2B parameters (smaller option)
  - Good for translation tasks
  - Can be fine-tuned for chat

## 🔧 Language Adapter Training

### Option 1: LoRA Adapters for Existing Model
```python
# train_chinese_adapter.py
import torch
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

# Configuration for Chinese LoRA adapter
lora_config = LoraConfig(
    r=16,  # Rank
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],  # For Mistral/Llama
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

# Load base model (Mistral)
base_model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    torch_dtype=torch.float16,
    device_map="auto"
)

# Apply LoRA
model = get_peft_model(base_model, lora_config)

# Training data structure for cannabis domain
training_data = [
    {
        "instruction": "推荐一些适合新手的产品",
        "input": "",
        "output": "对于新手，我推荐从低THC含量的产品开始..."
    },
    {
        "instruction": "什么是indica和sativa的区别？",
        "input": "",
        "output": "Indica和Sativa是大麻的两个主要品种..."
    }
]
```

### Option 2: Sentence-Level Adapter
```python
# chinese_adapter.py
class ChineseAdapter:
    def __init__(self, base_model):
        self.base_model = base_model
        self.zh_embeddings = self.load_chinese_embeddings()
        self.alignment_layer = self.create_alignment_layer()
    
    def load_chinese_embeddings(self):
        # Load pre-trained Chinese word embeddings
        from gensim.models import KeyedVectors
        return KeyedVectors.load_word2vec_format('chinese_embeddings.bin')
    
    def create_alignment_layer(self):
        # Neural network to align Chinese embeddings with English model space
        import torch.nn as nn
        return nn.Sequential(
            nn.Linear(300, 768),  # Chinese embed dim -> Model dim
            nn.ReLU(),
            nn.Linear(768, 768),
            nn.LayerNorm(768)
        )
    
    def process_chinese_input(self, text):
        # Convert Chinese text to aligned embeddings
        tokens = jieba.cut(text)
        embeddings = [self.zh_embeddings[token] for token in tokens]
        aligned = self.alignment_layer(torch.tensor(embeddings))
        return self.base_model.generate(aligned)
```

## 🚀 Implementation Strategy

### Quick Win: Use Qwen2.5 (Recommended)
```python
# services/multilingual_llm_service.py
import asyncio
from llama_cpp import Llama

class MultilingualLLMService:
    def __init__(self):
        # Load Qwen for Chinese/multilingual
        self.qwen_model = Llama(
            model_path="models/qwen2.5-7b-instruct-q4_k_m.gguf",
            n_ctx=4096,
            n_gpu_layers=35,  # Adjust based on GPU
            n_threads=8
        )
        
        # Keep Mistral for English
        self.mistral_model = Llama(
            model_path="models/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
            n_ctx=4096,
            n_gpu_layers=35,
            n_threads=8
        )
    
    async def process_message(self, text: str, language: str):
        if language in ['zh', 'ar', 'ja', 'ko']:
            # Use Qwen for Asian languages
            return self.generate_with_qwen(text, language)
        else:
            # Use Mistral for Western languages
            return self.generate_with_mistral(text, language)
    
    def generate_with_qwen(self, text: str, language: str):
        # Cannabis-specific prompt for Chinese
        system_prompt = """你是一个专业的大麻零售顾问。请用中文回答关于大麻产品的问题。
        记住：
        1. 提供准确的产品信息
        2. 解释THC和CBD的区别
        3. 推荐适合客户需求的产品
        4. 保持专业和友好"""
        
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n"
        
        response = self.qwen_model(
            prompt,
            max_tokens=512,
            temperature=0.7,
            stop=["<|im_end|>"]
        )
        
        return response['choices'][0]['text']
```

### Advanced: Train Custom Adapter
```bash
# Step 1: Prepare Chinese cannabis dataset
python scripts/prepare_chinese_dataset.py \
    --source data/cannabis_qa_english.json \
    --target data/cannabis_qa_chinese.json \
    --translate_with google

# Step 2: Train LoRA adapter
python scripts/train_lora_adapter.py \
    --base_model mistral-7b \
    --dataset data/cannabis_qa_chinese.json \
    --output models/adapters/chinese_cannabis_lora \
    --epochs 3 \
    --batch_size 4

# Step 3: Merge adapter with base model
python scripts/merge_adapter.py \
    --base_model models/mistral-7b \
    --adapter models/adapters/chinese_cannabis_lora \
    --output models/mistral-7b-chinese
```

## 📦 Required Dependencies

```bash
# For Qwen/ChatGLM
pip install transformers torch peft datasets
pip install sentencepiece protobuf

# For Chinese text processing
pip install jieba pypinyin

# For model conversion
pip install llama-cpp-python[server]
pip install ctransformers

# For training adapters
pip install bitsandbytes accelerate
```

## 🔄 Model Conversion to GGUF

```bash
# Convert Qwen to GGUF for llama.cpp
python convert.py models/Qwen2.5-7B-Instruct \
    --outfile models/qwen2.5-7b.gguf \
    --outtype q4_k_m

# Convert ChatGLM to GGUF
python convert-chatglm-hf-to-gguf.py \
    models/chatglm3-6b \
    --outfile models/chatglm3-6b.gguf \
    --outtype q4_0
```

## 📈 Performance Benchmarks

| Model | Chinese Quality | English Quality | Memory (Q4) | Speed (tokens/s) |
|-------|----------------|-----------------|-------------|------------------|
| Qwen2.5-7B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 4GB | 25-30 |
| ChatGLM3-6B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 3GB | 30-35 |
| Baichuan2-7B | ⭐⭐⭐⭐ | ⭐⭐⭐ | 4GB | 25-30 |
| BLOOMZ-7B | ⭐⭐⭐ | ⭐⭐⭐ | 4GB | 20-25 |
| Mistral+LoRA | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 4.5GB | 20-25 |

## 🏗️ Integration Plan

### Phase 1: Quick Implementation (1-2 days)
1. Download Qwen2.5-7B-Instruct GGUF
2. Add to MultilingualEngine as fallback model
3. Route Chinese queries to Qwen
4. Test with cannabis-specific prompts

### Phase 2: Optimization (3-5 days)
1. Fine-tune Qwen on cannabis terminology
2. Create Chinese product description dataset
3. Implement caching for common queries
4. Add quality validation

### Phase 3: Full Integration (1 week)
1. Train LoRA adapters for all Tier 3 languages
2. Implement model switching based on language
3. Add performance monitoring
4. Create language-specific prompts

## 🎯 Recommendation

**For immediate implementation:** Use **Qwen2.5-7B-Instruct** 
- Best Chinese support out-of-the-box
- Already includes cannabis/medical vocabulary
- Works with existing llama.cpp setup
- Minimal code changes required

**For long-term:** Train custom LoRA adapters
- Maintains consistency with Mistral for English
- Smaller memory footprint
- Can be optimized for cannabis domain
- Better control over responses