#!/usr/bin/env python3
"""
Model Trainer for Cannabis Virtual Budtender
Fine-tunes base models with cannabis knowledge and distinct personalities
Uses LoRA/QLoRA for efficient training
"""

import os
import json
import asyncio
import asyncpg
import logging
import torch
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import uuid
from tqdm import tqdm

# Check for required libraries
try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
        DataCollatorForLanguageModeling
    )
    from peft import (
        LoraConfig,
        get_peft_model,
        TaskType,
        prepare_model_for_kbit_training
    )
    from datasets import Dataset
    import bitsandbytes as bnb
    TRAINING_LIBS_AVAILABLE = True
except ImportError as e:
    TRAINING_LIBS_AVAILABLE = False
    logging.warning(f"Training libraries not fully installed: {e}")

logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Configuration for model training"""
    # Model settings
    base_model_name: str = "meta-llama/Llama-2-7b-chat-hf"
    model_type: str = "llama"
    
    # LoRA settings
    use_lora: bool = True
    lora_r: int = 16  # LoRA rank
    lora_alpha: int = 32  # LoRA alpha
    lora_dropout: float = 0.05
    target_modules: List[str] = None
    
    # Training settings
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    warmup_steps: int = 100
    max_length: int = 512
    
    # Optimization
    use_8bit: bool = True  # Use 8-bit quantization
    use_gradient_checkpointing: bool = True
    fp16: bool = True  # Use mixed precision
    
    # Personality training
    personality_weight: float = 0.3  # How much to weight personality in training
    cannabis_weight: float = 0.7  # How much to weight cannabis knowledge
    
    # Paths
    output_dir: str = "models/trained"
    checkpoint_dir: str = "models/checkpoints"
    
    def __post_init__(self):
        if self.target_modules is None:
            # Default LoRA target modules for Llama
            self.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]

@dataclass
class TrainingExample:
    """Single training example"""
    instruction: str
    input: str
    output: str
    personality_id: Optional[str] = None
    example_type: str = "general"  # general, product, personality, medical

class ModelTrainer:
    """
    Handles model fine-tuning with cannabis knowledge and personalities
    """
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        self.db_pool = db_pool
        self.config = TrainingConfig()
        self.model = None
        self.tokenizer = None
        self.training_examples = []
        self.validation_examples = []
        self.current_session_id = None
        
        # Paths
        self.models_dir = Path("/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/models")
        self.trained_dir = self.models_dir / "trained"
        self.checkpoint_dir = self.models_dir / "checkpoints"
        
        # Ensure directories exist
        self.trained_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize_db(self):
        """Initialize database connection"""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                host='localhost',
                port=5434,
                database='ai_engine',
                user='weedgo',
                password='weedgo123',
                min_size=2,
                max_size=10
            )
    
    async def prepare_training_data(self, 
                                  dataset_ids: Optional[List[str]] = None,
                                  personality_ids: Optional[List[str]] = None) -> int:
        """
        Prepare training data from database
        Combines cannabis knowledge with personality traits
        """
        if not self.db_pool:
            await self.initialize_db()
        
        self.training_examples = []
        
        async with self.db_pool.acquire() as conn:
            # Load training examples from database
            query = """
                SELECT query, expected_intent, expected_response, 
                       entities, dataset_id, dataset_name
                FROM training_examples
                WHERE is_active = true
            """
            params = []
            
            if dataset_ids:
                query += f" AND dataset_id = ANY($1)"
                params.append(dataset_ids)
            
            results = await conn.fetch(query, *params)
            
            # Convert to training examples
            for row in results:
                example = TrainingExample(
                    instruction="You are a cannabis budtender. Help the customer with their request.",
                    input=row['query'],
                    output=row['expected_response'] or self._generate_default_response(row['query'], row['expected_intent'])
                )
                self.training_examples.append(example)
            
            # Load personality-specific examples if specified
            if personality_ids:
                personalities = await conn.fetch("""
                    SELECT * FROM ai_personalities
                    WHERE id = ANY($1) AND active = true
                """, personality_ids)
                
                for personality in personalities:
                    # Create personality-specific training examples
                    self._add_personality_examples(personality)
            
            # Add cannabis domain knowledge examples
            await self._add_cannabis_knowledge_examples()
        
        # Split into training and validation
        split_idx = int(len(self.training_examples) * 0.9)
        self.validation_examples = self.training_examples[split_idx:]
        self.training_examples = self.training_examples[:split_idx]
        
        logger.info(f"Prepared {len(self.training_examples)} training examples and {len(self.validation_examples)} validation examples")
        return len(self.training_examples)
    
    def _generate_default_response(self, query: str, intent: str) -> str:
        """Generate default response based on intent"""
        responses = {
            'product_search': f"I'll help you find products that match '{query}'. Let me search our inventory for you.",
            'medical_recommendation': f"For your medical needs regarding '{query}', I recommend consulting our medical cannabis selection.",
            'greeting': "Welcome! I'm here to help you find the perfect cannabis products. What are you looking for today?",
            'general': f"I understand you're asking about '{query}'. Let me provide you with helpful information."
        }
        return responses.get(intent, f"I'll help you with: {query}")
    
    def _add_personality_examples(self, personality: Dict):
        """Add personality-specific training examples"""
        p_name = personality['name']
        p_style = personality.get('communication_style', 'friendly')
        p_traits = json.loads(personality.get('traits', '[]'))
        
        # Greeting examples with personality
        greetings = [
            f"Hey, I'm {p_name}! What can I help you find today?",
            f"Welcome! {p_name} here, your personal budtender. What brings you in?",
            f"Hi there! I'm {p_name}. Ready to find your perfect cannabis match?"
        ]
        
        for greeting in greetings:
            self.training_examples.append(TrainingExample(
                instruction=f"You are {p_name}, a {p_style} budtender with these traits: {', '.join(p_traits)}. Greet the customer.",
                input="Hello",
                output=greeting,
                personality_id=str(personality['id']),
                example_type="personality"
            ))
        
        # Product recommendation examples with personality flair
        if 'knowledgeable' in p_traits:
            self.training_examples.append(TrainingExample(
                instruction=f"You are {p_name}, known for deep cannabis knowledge. Recommend a product.",
                input="What's good for anxiety?",
                output=f"Based on terpene profiles and cannabinoid research, I'd recommend high-CBD strains with linalool and limonene. These terpenes have anxiolytic properties. Our Blue Dream CBD or AC/DC strains would be excellent choices.",
                personality_id=str(personality['id']),
                example_type="personality"
            ))
    
    async def _add_cannabis_knowledge_examples(self):
        """Add cannabis domain knowledge training examples"""
        
        # Strain types
        strain_examples = [
            ("What's the difference between indica and sativa?",
             "Indica strains typically provide relaxing, body-focused effects - great for evening use, pain relief, and sleep. Sativa strains offer energizing, cerebral effects - perfect for daytime use, creativity, and social activities. Hybrids blend both characteristics."),
            
            ("Tell me about terpenes",
             "Terpenes are aromatic compounds that give cannabis its unique flavors and contribute to effects. Myrcene promotes relaxation, limonene elevates mood, pinene aids focus, and linalool reduces anxiety. Understanding terpenes helps you choose strains beyond just THC content."),
            
            ("What's good for first-time users?",
             "For beginners, I recommend starting with low-THC options (5-10%) or balanced CBD:THC ratios. Microdose edibles (2.5-5mg), CBD-dominant strains, or 1:1 products provide gentle introduction. Always start low and go slow!"),
        ]
        
        for input_text, output_text in strain_examples:
            self.training_examples.append(TrainingExample(
                instruction="You are an expert cannabis budtender. Provide accurate, helpful information.",
                input=input_text,
                output=output_text,
                example_type="general"
            ))
        
        # Product-specific examples
        product_examples = [
            ("I need something for chronic pain",
             "For chronic pain, I recommend high-THC indica strains like OG Kush or Granddaddy Purple. Consider also trying topicals for localized relief, or RSO (Rick Simpson Oil) for systemic pain. Many patients find success with a combination approach."),
            
            ("What edibles do you have?",
             "We carry a variety of edibles including gummies (2.5-10mg pieces), chocolates, beverages, and baked goods. For precise dosing, gummies are ideal. First-timers should start with 2.5-5mg and wait 2 hours before taking more."),
        ]
        
        for input_text, output_text in product_examples:
            self.training_examples.append(TrainingExample(
                instruction="You are a cannabis budtender helping with product selection.",
                input=input_text,
                output=output_text,
                example_type="product"
            ))
    
    def prepare_model_for_training(self):
        """
        Load and prepare model for fine-tuning
        Uses LoRA for efficient training
        """
        if not TRAINING_LIBS_AVAILABLE:
            raise ImportError("Training libraries not installed. Install with: pip install transformers peft bitsandbytes")
        
        logger.info(f"Loading base model: {self.config.base_model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model_name,
            trust_remote_code=True
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model with quantization for memory efficiency
        if self.config.use_8bit:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.base_model_name,
                load_in_8bit=True,
                device_map="auto",
                trust_remote_code=True
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.base_model_name,
                torch_dtype=torch.float16 if self.config.fp16 else torch.float32,
                device_map="auto",
                trust_remote_code=True
            )
        
        # Prepare for k-bit training if using quantization
        if self.config.use_8bit:
            self.model = prepare_model_for_kbit_training(self.model)
        
        # Apply LoRA
        if self.config.use_lora:
            lora_config = LoraConfig(
                r=self.config.lora_r,
                lora_alpha=self.config.lora_alpha,
                target_modules=self.config.target_modules,
                lora_dropout=self.config.lora_dropout,
                bias="none",
                task_type=TaskType.CAUSAL_LM
            )
            
            self.model = get_peft_model(self.model, lora_config)
            self.model.print_trainable_parameters()
        
        # Enable gradient checkpointing
        if self.config.use_gradient_checkpointing:
            self.model.gradient_checkpointing_enable()
        
        logger.info("Model prepared for training")
    
    def _format_training_example(self, example: TrainingExample) -> str:
        """Format training example into prompt"""
        if self.config.model_type == "llama":
            # Llama 2 chat format
            return f"""<s>[INST] <<SYS>>
{example.instruction}
<</SYS>>

{example.input} [/INST] {example.output} </s>"""
        else:
            # Generic format
            return f"""### Instruction:
{example.instruction}

### Input:
{example.input}

### Response:
{example.output}"""
    
    def _create_dataset(self, examples: List[TrainingExample]) -> Dataset:
        """Create HuggingFace dataset from examples"""
        formatted_examples = []
        
        for example in examples:
            text = self._format_training_example(example)
            formatted_examples.append({"text": text})
        
        dataset = Dataset.from_list(formatted_examples)
        
        # Tokenize dataset
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                padding="max_length",
                max_length=self.config.max_length
            )
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        return tokenized_dataset
    
    async def train(self, 
                   session_name: Optional[str] = None,
                   save_checkpoints: bool = True) -> Dict[str, Any]:
        """
        Execute training
        Returns training metrics and model path
        """
        if not self.training_examples:
            raise ValueError("No training data prepared. Call prepare_training_data first.")
        
        if not self.model:
            self.prepare_model_for_training()
        
        # Generate session ID
        self.current_session_id = session_name or f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create datasets
        train_dataset = self._create_dataset(self.training_examples)
        eval_dataset = self._create_dataset(self.validation_examples) if self.validation_examples else None
        
        # Training arguments
        output_dir = self.checkpoint_dir / self.current_session_id
        training_args = TrainingArguments(
            output_dir=str(output_dir),
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            warmup_steps=self.config.warmup_steps,
            learning_rate=self.config.learning_rate,
            fp16=self.config.fp16,
            logging_steps=10,
            evaluation_strategy="steps" if eval_dataset else "no",
            eval_steps=50 if eval_dataset else None,
            save_strategy="steps" if save_checkpoints else "no",
            save_steps=100 if save_checkpoints else None,
            save_total_limit=3,
            load_best_model_at_end=True if eval_dataset else False,
            report_to="none"  # Disable wandb/tensorboard
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator
        )
        
        # Start training
        logger.info(f"Starting training session: {self.current_session_id}")
        train_result = trainer.train()
        
        # Save final model
        final_model_path = self.trained_dir / f"{self.current_session_id}_final"
        trainer.save_model(str(final_model_path))
        
        # Save training metrics
        metrics = {
            "session_id": self.current_session_id,
            "train_loss": train_result.training_loss,
            "train_runtime": train_result.metrics['train_runtime'],
            "train_samples": len(train_dataset),
            "epochs": self.config.num_epochs,
            "model_path": str(final_model_path),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to database
        await self._save_training_session(metrics)
        
        logger.info(f"Training completed. Model saved to {final_model_path}")
        return metrics
    
    async def _save_training_session(self, metrics: Dict[str, Any]):
        """Save training session to database"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO training_sessions 
                    (session_id, examples_trained, accuracy_after, 
                     improvements, status, completed_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, metrics['session_id'], metrics['train_samples'],
                    1.0 - metrics.get('train_loss', 1.0),  # Rough accuracy estimate
                    json.dumps(metrics), 'completed', datetime.now())
                
                # Register model version
                await conn.execute("""
                    INSERT INTO model_versions
                    (version_id, model_name, base_model, version_number,
                     training_method, model_path, file_size_mb, status,
                     training_examples_count, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, metrics['session_id'], f"budtender_{metrics['session_id']}",
                    self.config.base_model_name, "1.0.0", "lora",
                    metrics['model_path'], 
                    os.path.getsize(metrics['model_path']) / (1024*1024) if os.path.exists(metrics['model_path']) else 0,
                    'ready', metrics['train_samples'], 'trainer')
                    
        except Exception as e:
            logger.error(f"Failed to save training session: {e}")
    
    async def export_to_gguf(self, model_path: str, output_path: Optional[str] = None) -> str:
        """
        Export trained model to GGUF format for use with llama-cpp-python
        Note: This requires additional conversion tools
        """
        if output_path is None:
            output_path = str(self.models_dir / "exports" / f"{Path(model_path).stem}.gguf")
        
        logger.info(f"Exporting model to GGUF format: {output_path}")
        
        # Note: Actual GGUF conversion requires llama.cpp convert.py script
        # This is a placeholder for the conversion process
        logger.warning("GGUF conversion requires llama.cpp tools. Please run manually:")
        logger.warning(f"python convert.py {model_path} --outfile {output_path}")
        
        return output_path
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.model:
            del self.model
            self.model = None
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
        if self.db_pool:
            await self.db_pool.close()
        
        # Clear GPU cache if using CUDA
        if torch.cuda.is_available():
            torch.cuda.empty_cache()