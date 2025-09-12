"""
Generation Engine Service
Implements IGenerationEngine interface following SOLID principles
Handles text generation using loaded models
"""

import time
import logging
from typing import Dict, Any, Optional, Generator
import re

# Import interface
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.interfaces import IGenerationEngine, IModelManager

logger = logging.getLogger(__name__)


class GenerationEngine(IGenerationEngine):
    """
    Generation Engine implementation that handles text generation
    Single Responsibility: Text generation from prompts
    """
    
    def __init__(self, model_manager: IModelManager):
        """
        Initialize the Generation Engine
        
        Args:
            model_manager: Model manager instance for accessing loaded models
        """
        self.model_manager = model_manager
        self.generation_stats = {
            'total_generations': 0,
            'total_tokens': 0,
            'total_time': 0,
            'avg_tokens_per_second': 0
        }
        
        logger.info("GenerationEngine initialized")
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text from a prompt
        
        Args:
            prompt: Input prompt for generation
            **kwargs: Additional generation parameters
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - top_p: Top-p sampling parameter
                - top_k: Top-k sampling parameter
                - repeat_penalty: Repetition penalty
                - stop_sequences: List of stop sequences
                - seed: Random seed for reproducibility
                
        Returns:
            Dictionary containing:
                - text: Generated text
                - tokens: Number of tokens generated
                - time: Generation time in seconds
                - finish_reason: Reason for completion
        """
        start_time = time.time()
        
        # Get the current model
        model = self.model_manager.get_current_model()
        
        if not model:
            logger.error("No model loaded for generation")
            return {
                'text': '',
                'error': 'No model loaded',
                'tokens': 0,
                'time': 0,
                'finish_reason': 'error'
            }
        
        try:
            # Extract generation parameters
            generation_params = self._prepare_generation_params(kwargs)
            
            # Log generation request
            logger.info(f"Generating with params: max_tokens={generation_params['max_new_tokens']}, "
                       f"temperature={generation_params['temperature']}")
            
            # Generate response
            response = model(
                prompt,
                **generation_params
            )
            
            # Extract generated text
            generated_text = response['choices'][0]['text']
            
            # Clean up the response
            generated_text = self._clean_response(generated_text, kwargs.get('stop_sequences', []))
            
            # Calculate statistics
            generation_time = time.time() - start_time
            token_count = response.get('usage', {}).get('completion_tokens', len(generated_text.split()))
            
            # Update statistics
            self._update_stats(token_count, generation_time)
            
            # Build result
            result = {
                'text': generated_text,
                'tokens': token_count,
                'time': round(generation_time, 2),
                'finish_reason': response['choices'][0].get('finish_reason', 'stop'),
                'model': self.model_manager.get_model_info().get('name', 'unknown')
            }
            
            # Add usage information if available
            if 'usage' in response:
                result['usage'] = {
                    'prompt_tokens': response['usage'].get('prompt_tokens', 0),
                    'completion_tokens': response['usage'].get('completion_tokens', 0),
                    'total_tokens': response['usage'].get('total_tokens', 0)
                }
            
            logger.info(f"Generated {token_count} tokens in {generation_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return {
                'text': '',
                'error': str(e),
                'tokens': 0,
                'time': time.time() - start_time,
                'finish_reason': 'error'
            }
    
    def stream_generate(self, prompt: str, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        Stream generation for real-time output
        
        Args:
            prompt: Input prompt for generation
            **kwargs: Additional generation parameters
            
        Yields:
            Dictionary containing partial results
        """
        start_time = time.time()
        
        # Get the current model
        model = self.model_manager.get_current_model()
        
        if not model:
            yield {
                'text': '',
                'error': 'No model loaded',
                'done': True
            }
            return
        
        try:
            # Prepare parameters for streaming
            generation_params = self._prepare_generation_params(kwargs)
            generation_params['stream'] = True
            
            # Start streaming generation
            stream = model(prompt, **generation_params)
            
            accumulated_text = ""
            token_count = 0
            
            for chunk in stream:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    
                    if 'text' in delta:
                        text_chunk = delta['text']
                        accumulated_text += text_chunk
                        token_count += 1
                        
                        yield {
                            'text': text_chunk,
                            'accumulated': accumulated_text,
                            'tokens': token_count,
                            'done': False
                        }
                    
                    # Check for finish reason
                    if chunk['choices'][0].get('finish_reason'):
                        break
            
            # Final yield with statistics
            generation_time = time.time() - start_time
            self._update_stats(token_count, generation_time)
            
            yield {
                'text': '',
                'accumulated': accumulated_text,
                'tokens': token_count,
                'time': round(generation_time, 2),
                'done': True,
                'finish_reason': 'stop'
            }
            
        except Exception as e:
            logger.error(f"Stream generation failed: {e}")
            yield {
                'text': '',
                'error': str(e),
                'done': True
            }
    
    def _prepare_generation_params(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare generation parameters for the model
        
        Args:
            kwargs: Raw generation parameters
            
        Returns:
            Formatted parameters for model generation
        """
        # Default parameters
        params = {
            'max_new_tokens': kwargs.get('max_tokens', 150),
            'temperature': kwargs.get('temperature', 0.7),
            'top_p': kwargs.get('top_p', 0.9),
            'top_k': kwargs.get('top_k', 40),
            'repeat_penalty': kwargs.get('repeat_penalty', 1.1),
            'seed': kwargs.get('seed', -1)
        }
        
        # Add stop sequences if provided
        if 'stop_sequences' in kwargs and kwargs['stop_sequences']:
            params['stop'] = kwargs['stop_sequences']
        
        # Add other model-specific parameters
        for key in ['frequency_penalty', 'presence_penalty', 'mirostat_mode', 'mirostat_tau', 'mirostat_eta']:
            if key in kwargs:
                params[key] = kwargs[key]
        
        return params
    
    def _clean_response(self, text: str, stop_sequences: list) -> str:
        """
        Clean up generated response
        
        Args:
            text: Generated text
            stop_sequences: List of stop sequences to remove
            
        Returns:
            Cleaned text
        """
        # Remove any stop sequences that might have been included
        for stop_seq in stop_sequences:
            if stop_seq in text:
                text = text.split(stop_seq)[0]
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove repeated whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove incomplete sentences at the end (optional)
        # This helps when generation is cut off by max_tokens
        if text and not text[-1] in '.!?':
            # Find the last complete sentence
            last_sentence_end = max(
                text.rfind('.'),
                text.rfind('!'),
                text.rfind('?')
            )
            if last_sentence_end > 0:
                text = text[:last_sentence_end + 1]
        
        return text
    
    def _update_stats(self, tokens: int, time_taken: float):
        """
        Update generation statistics
        
        Args:
            tokens: Number of tokens generated
            time_taken: Time taken for generation
        """
        self.generation_stats['total_generations'] += 1
        self.generation_stats['total_tokens'] += tokens
        self.generation_stats['total_time'] += time_taken
        
        if self.generation_stats['total_time'] > 0:
            self.generation_stats['avg_tokens_per_second'] = (
                self.generation_stats['total_tokens'] / self.generation_stats['total_time']
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get generation statistics
        
        Returns:
            Statistics dictionary
        """
        stats = self.generation_stats.copy()
        
        # Add current model info
        model_info = self.model_manager.get_model_info()
        stats['current_model'] = model_info.get('name', 'none')
        stats['model_loaded'] = model_info.get('loaded', False)
        
        # Round floating point values
        stats['total_time'] = round(stats['total_time'], 2)
        stats['avg_tokens_per_second'] = round(stats['avg_tokens_per_second'], 2)
        
        return stats
    
    def validate_prompt(self, prompt: str, max_length: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate a prompt before generation
        
        Args:
            prompt: Prompt to validate
            max_length: Maximum allowed prompt length
            
        Returns:
            Validation result dictionary
        """
        result = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Check if prompt is empty
        if not prompt or not prompt.strip():
            result['valid'] = False
            result['issues'].append('Prompt is empty')
            return result
        
        # Check prompt length
        prompt_length = len(prompt)
        if max_length and prompt_length > max_length:
            result['valid'] = False
            result['issues'].append(f'Prompt exceeds maximum length ({prompt_length} > {max_length})')
        
        # Check for potential issues
        if prompt_length > 4000:
            result['warnings'].append('Prompt is very long, may affect generation quality')
        
        # Check for special characters that might cause issues
        if '\x00' in prompt:
            result['valid'] = False
            result['issues'].append('Prompt contains null characters')
        
        # Check if model is loaded
        if not self.model_manager.get_current_model():
            result['valid'] = False
            result['issues'].append('No model loaded')
        
        return result
    
    def format_prompt_with_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Format a prompt with additional context
        
        Args:
            prompt: Base prompt
            context: Context dictionary
            
        Returns:
            Formatted prompt with context
        """
        formatted_parts = []
        
        # Add conversation history if present
        if 'history' in context and context['history']:
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in context['history'][-5:]  # Last 5 messages
            ])
            formatted_parts.append(f"Previous conversation:\n{history_text}")
        
        # Add system instruction if present
        if 'system_instruction' in context:
            formatted_parts.append(f"System: {context['system_instruction']}")
        
        # Add the main prompt
        formatted_parts.append(f"User: {prompt}")
        formatted_parts.append("Assistant:")
        
        return "\n\n".join(formatted_parts)