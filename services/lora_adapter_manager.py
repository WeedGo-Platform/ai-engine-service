"""
LoRA Adapter Management System for Multilingual Support
Manages language-specific and domain-specific LoRA adapters
"""

import os
import json
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from pathlib import Path

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

logger = logging.getLogger(__name__)

class AdapterType(Enum):
    """Types of LoRA adapters"""
    LANGUAGE = "language"      # Language-specific
    DOMAIN = "domain"          # Domain-specific (medical, cannabis)
    STYLE = "style"            # Response style
    TASK = "task"              # Task-specific

@dataclass
class LoRAConfig:
    """Configuration for a LoRA adapter"""
    name: str
    type: AdapterType
    path: str
    rank: int                   # LoRA rank (8, 16, 32)
    alpha: float               # LoRA alpha scaling
    dropout: float = 0.05      # Dropout rate
    target_modules: List[str] = field(default_factory=list)
    language: Optional[str] = None
    description: str = ""
    version: str = "1.0"
    compatibility: List[str] = field(default_factory=list)  # Compatible models

@dataclass 
class AdapterStack:
    """Stack of adapters to apply"""
    base_model: str
    adapters: List[LoRAConfig]
    weights: List[float]       # Mixing weights for adapters
    merge_strategy: str = "sequential"  # sequential, weighted, dynamic

class LoRAAdapterManager:
    """
    Manages LoRA adapters for multilingual and domain-specific adaptations
    """
    
    def __init__(
        self,
        adapters_dir: str = "models/lora_adapters",
        cache_dir: str = "cache/adapters"
    ):
        """
        Initialize LoRA adapter manager
        
        Args:
            adapters_dir: Directory containing LoRA adapters
            cache_dir: Directory for adapter cache
        """
        
        self.adapters_dir = Path(adapters_dir)
        self.cache_dir = Path(cache_dir)
        
        # Create directories
        self.adapters_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Adapter registry
        self.adapters: Dict[str, LoRAConfig] = {}
        self.loaded_adapters: Dict[str, Any] = {}
        
        # Language-specific adapter configurations
        self.language_adapters = self._initialize_language_adapters()
        
        # Domain-specific adapter configurations
        self.domain_adapters = self._initialize_domain_adapters()
        
        # Load existing adapters
        self._load_adapter_registry()
        
        # Metrics
        self.metrics = {
            'total_loads': 0,
            'cache_hits': 0,
            'active_adapters': 0
        }
    
    def _initialize_language_adapters(self) -> Dict[str, LoRAConfig]:
        """Initialize language-specific adapter configurations"""
        
        return {
            'spanish': LoRAConfig(
                name='spanish_base',
                type=AdapterType.LANGUAGE,
                path='lora_adapters/spanish_base.bin',
                rank=8,
                alpha=16,
                language='es',
                target_modules=['q_proj', 'v_proj', 'o_proj'],
                description='Spanish language adaptation',
                compatibility=['qwen-14b', 'qwen-7b']
            ),
            'french': LoRAConfig(
                name='french_base',
                type=AdapterType.LANGUAGE,
                path='lora_adapters/french_base.bin',
                rank=8,
                alpha=16,
                language='fr',
                target_modules=['q_proj', 'v_proj', 'o_proj'],
                description='French language adaptation',
                compatibility=['qwen-14b', 'qwen-7b']
            ),
            'portuguese': LoRAConfig(
                name='portuguese_base',
                type=AdapterType.LANGUAGE,
                path='lora_adapters/portuguese_base.bin',
                rank=8,
                alpha=16,
                language='pt',
                target_modules=['q_proj', 'v_proj', 'o_proj'],
                description='Portuguese language adaptation',
                compatibility=['qwen-14b', 'qwen-7b']
            ),
            'chinese': LoRAConfig(
                name='chinese_enhanced',
                type=AdapterType.LANGUAGE,
                path='lora_adapters/chinese_enhanced.bin',
                rank=16,  # Higher rank for non-Latin script
                alpha=32,
                language='zh',
                target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'],
                description='Enhanced Chinese language adaptation',
                compatibility=['qwen-14b', 'qwen-7b']
            ),
            'arabic': LoRAConfig(
                name='arabic_enhanced',
                type=AdapterType.LANGUAGE,
                path='lora_adapters/arabic_enhanced.bin',
                rank=16,  # Higher rank for non-Latin script
                alpha=32,
                language='ar',
                target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'],
                description='Enhanced Arabic language adaptation with RTL support',
                compatibility=['qwen-14b', 'qwen-7b']
            )
        }
    
    def _initialize_domain_adapters(self) -> Dict[str, LoRAConfig]:
        """Initialize domain-specific adapter configurations"""
        
        return {
            'cannabis': LoRAConfig(
                name='cannabis_expert',
                type=AdapterType.DOMAIN,
                path='lora_adapters/cannabis_expert.bin',
                rank=16,
                alpha=32,
                target_modules=['q_proj', 'v_proj', 'o_proj', 'mlp'],
                description='Cannabis industry terminology and knowledge',
                compatibility=['qwen-14b', 'qwen-7b']
            ),
            'medical': LoRAConfig(
                name='medical_cannabis',
                type=AdapterType.DOMAIN,
                path='lora_adapters/medical_cannabis.bin',
                rank=16,
                alpha=32,
                target_modules=['q_proj', 'v_proj', 'o_proj', 'mlp'],
                description='Medical cannabis and health information',
                compatibility=['qwen-14b', 'qwen-7b']
            ),
            'retail': LoRAConfig(
                name='retail_assistant',
                type=AdapterType.STYLE,
                path='lora_adapters/retail_assistant.bin',
                rank=8,
                alpha=16,
                target_modules=['o_proj', 'mlp'],
                description='Retail customer service style',
                compatibility=['qwen-14b', 'qwen-7b']
            )
        }
    
    def _load_adapter_registry(self):
        """Load adapter registry from disk"""
        
        registry_path = self.adapters_dir / "registry.json"
        
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    registry_data = json.load(f)
                    
                for adapter_data in registry_data.get('adapters', []):
                    adapter_type = AdapterType[adapter_data['type']]
                    config = LoRAConfig(
                        name=adapter_data['name'],
                        type=adapter_type,
                        path=adapter_data['path'],
                        rank=adapter_data['rank'],
                        alpha=adapter_data['alpha'],
                        dropout=adapter_data.get('dropout', 0.05),
                        target_modules=adapter_data.get('target_modules', []),
                        language=adapter_data.get('language'),
                        description=adapter_data.get('description', ''),
                        version=adapter_data.get('version', '1.0'),
                        compatibility=adapter_data.get('compatibility', [])
                    )
                    self.adapters[config.name] = config
                    
                logger.info(f"Loaded {len(self.adapters)} adapters from registry")
                
            except Exception as e:
                logger.error(f"Failed to load adapter registry: {e}")
    
    def register_adapter(self, config: LoRAConfig) -> bool:
        """
        Register a new LoRA adapter
        
        Args:
            config: LoRA adapter configuration
            
        Returns:
            Success status
        """
        
        try:
            # Validate adapter path
            adapter_path = Path(self.adapters_dir) / config.path
            if not adapter_path.exists():
                logger.warning(f"Adapter file not found: {adapter_path}")
            
            # Add to registry
            self.adapters[config.name] = config
            
            # Save registry
            self._save_registry()
            
            logger.info(f"Registered adapter: {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register adapter: {e}")
            return False
    
    def get_adapter_stack(
        self,
        language: str,
        domain: Optional[str] = None,
        style: Optional[str] = None
    ) -> AdapterStack:
        """
        Get optimal adapter stack for given requirements
        
        Args:
            language: Target language
            domain: Optional domain (cannabis, medical)
            style: Optional style (retail, formal, casual)
            
        Returns:
            AdapterStack with selected adapters and weights
        """
        
        adapters = []
        weights = []
        
        # Add language adapter if not English
        if language != 'en':
            lang_adapter_name = self._get_language_adapter_name(language)
            if lang_adapter_name in self.language_adapters:
                adapters.append(self.language_adapters[lang_adapter_name])
                weights.append(1.0)  # Full weight for language
        
        # Add domain adapter
        if domain:
            if domain in self.domain_adapters:
                adapters.append(self.domain_adapters[domain])
                weights.append(0.8)  # High weight for domain
        
        # Add cannabis adapter by default for this application
        if 'cannabis' in self.domain_adapters and domain != 'cannabis':
            adapters.append(self.domain_adapters['cannabis'])
            weights.append(0.5)  # Medium weight for general cannabis
        
        # Add style adapter
        if style and style in self.domain_adapters:
            adapters.append(self.domain_adapters[style])
            weights.append(0.3)  # Lower weight for style
        
        # Normalize weights
        if weights:
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]
        
        return AdapterStack(
            base_model='qwen-14b',
            adapters=adapters,
            weights=weights,
            merge_strategy='weighted'
        )
    
    def _get_language_adapter_name(self, language: str) -> str:
        """Get adapter name for language code"""
        
        language_map = {
            'es': 'spanish',
            'fr': 'french',
            'pt': 'portuguese',
            'zh': 'chinese',
            'ar': 'arabic'
        }
        
        return language_map.get(language, '')
    
    def load_adapter(self, config: LoRAConfig) -> Optional[Any]:
        """
        Load a LoRA adapter into memory
        
        Args:
            config: Adapter configuration
            
        Returns:
            Loaded adapter object or None
        """
        
        # Check cache
        if config.name in self.loaded_adapters:
            self.metrics['cache_hits'] += 1
            return self.loaded_adapters[config.name]
        
        try:
            adapter_path = Path(self.adapters_dir) / config.path
            
            if adapter_path.exists():
                # In production, this would load actual LoRA weights
                # For now, we'll create a placeholder
                adapter_data = {
                    'config': config,
                    'weights': None,  # Would be actual tensor weights
                    'loaded': True
                }
                
                self.loaded_adapters[config.name] = adapter_data
                self.metrics['total_loads'] += 1
                self.metrics['active_adapters'] = len(self.loaded_adapters)
                
                logger.info(f"Loaded adapter: {config.name}")
                return adapter_data
            else:
                logger.warning(f"Adapter file not found: {adapter_path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load adapter: {e}")
            return None
    
    def apply_adapters(
        self,
        model: Any,
        adapter_stack: AdapterStack
    ) -> Any:
        """
        Apply adapter stack to model
        
        Args:
            model: Base model
            adapter_stack: Stack of adapters to apply
            
        Returns:
            Model with adapters applied
        """
        
        if not adapter_stack.adapters:
            return model
        
        try:
            # Load all adapters in stack
            for adapter_config in adapter_stack.adapters:
                adapter = self.load_adapter(adapter_config)
                if adapter:
                    # In production, this would actually apply LoRA weights
                    # using the merge strategy and weights
                    logger.debug(f"Applied adapter: {adapter_config.name}")
            
            logger.info(f"Applied {len(adapter_stack.adapters)} adapters")
            return model
            
        except Exception as e:
            logger.error(f"Failed to apply adapters: {e}")
            return model
    
    def create_adapter_from_data(
        self,
        name: str,
        adapter_type: AdapterType,
        training_data: List[Dict],
        base_model: str = 'qwen-14b',
        rank: int = 8
    ) -> bool:
        """
        Create a new LoRA adapter from training data
        (Placeholder - actual training would require GPU and training loop)
        
        Args:
            name: Adapter name
            adapter_type: Type of adapter
            training_data: Training examples
            base_model: Base model name
            rank: LoRA rank
            
        Returns:
            Success status
        """
        
        try:
            # Generate adapter path
            adapter_path = f"lora_adapters/{name}.bin"
            
            # Create configuration
            config = LoRAConfig(
                name=name,
                type=adapter_type,
                path=adapter_path,
                rank=rank,
                alpha=rank * 2,
                target_modules=['q_proj', 'v_proj', 'o_proj'],
                description=f"Custom adapter created from {len(training_data)} examples",
                compatibility=[base_model]
            )
            
            # In production, this would:
            # 1. Initialize LoRA weights
            # 2. Run training loop on training_data
            # 3. Save trained weights to adapter_path
            
            # Register the adapter
            self.register_adapter(config)
            
            logger.info(f"Created adapter: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create adapter: {e}")
            return False
    
    def merge_adapters(
        self,
        adapter_names: List[str],
        output_name: str,
        merge_strategy: str = 'average'
    ) -> bool:
        """
        Merge multiple adapters into one
        
        Args:
            adapter_names: Names of adapters to merge
            output_name: Name for merged adapter
            merge_strategy: How to merge (average, weighted, svd)
            
        Returns:
            Success status
        """
        
        try:
            # Get adapter configs
            adapters_to_merge = []
            for name in adapter_names:
                if name in self.adapters:
                    adapters_to_merge.append(self.adapters[name])
            
            if len(adapters_to_merge) < 2:
                logger.warning("Need at least 2 adapters to merge")
                return False
            
            # In production, this would:
            # 1. Load all adapter weights
            # 2. Merge using specified strategy
            # 3. Save merged weights
            
            # Create merged config
            merged_config = LoRAConfig(
                name=output_name,
                type=AdapterType.DOMAIN,
                path=f"lora_adapters/{output_name}.bin",
                rank=max(a.rank for a in adapters_to_merge),
                alpha=max(a.alpha for a in adapters_to_merge),
                target_modules=list(set(
                    module for a in adapters_to_merge 
                    for module in a.target_modules
                )),
                description=f"Merged from: {', '.join(adapter_names)}",
                compatibility=list(set(
                    model for a in adapters_to_merge 
                    for model in a.compatibility
                ))
            )
            
            # Register merged adapter
            self.register_adapter(merged_config)
            
            logger.info(f"Merged {len(adapters_to_merge)} adapters into {output_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to merge adapters: {e}")
            return False
    
    def unload_adapter(self, name: str):
        """Unload adapter from memory"""
        
        if name in self.loaded_adapters:
            del self.loaded_adapters[name]
            self.metrics['active_adapters'] = len(self.loaded_adapters)
            logger.info(f"Unloaded adapter: {name}")
    
    def clear_cache(self):
        """Clear all loaded adapters from memory"""
        
        self.loaded_adapters.clear()
        self.metrics['active_adapters'] = 0
        logger.info("Cleared adapter cache")
    
    def get_metrics(self) -> Dict:
        """Get adapter manager metrics"""
        
        return {
            **self.metrics,
            'registered_adapters': len(self.adapters),
            'language_adapters': len(self.language_adapters),
            'domain_adapters': len(self.domain_adapters),
            'cache_hit_rate': (
                self.metrics['cache_hits'] / self.metrics['total_loads']
                if self.metrics['total_loads'] > 0 else 0
            )
        }
    
    def _save_registry(self):
        """Save adapter registry to disk"""
        
        try:
            registry_path = self.adapters_dir / "registry.json"
            
            registry_data = {
                'version': '1.0',
                'adapters': [
                    {
                        'name': config.name,
                        'type': config.type.name,
                        'path': config.path,
                        'rank': config.rank,
                        'alpha': config.alpha,
                        'dropout': config.dropout,
                        'target_modules': config.target_modules,
                        'language': config.language,
                        'description': config.description,
                        'version': config.version,
                        'compatibility': config.compatibility
                    }
                    for config in self.adapters.values()
                ]
            }
            
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
                
            logger.info("Saved adapter registry")
            
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def get_adapter_info(self, name: str) -> Optional[Dict]:
        """Get detailed information about an adapter"""
        
        if name in self.adapters:
            config = self.adapters[name]
            return {
                'name': config.name,
                'type': config.type.value,
                'language': config.language,
                'description': config.description,
                'rank': config.rank,
                'target_modules': config.target_modules,
                'compatibility': config.compatibility,
                'loaded': name in self.loaded_adapters
            }
        return None