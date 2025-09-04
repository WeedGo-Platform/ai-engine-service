#!/usr/bin/env python3
"""
Prompt Management Service
Handles all operations for managing AI prompt files
"""

import os
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
from dataclasses import dataclass, asdict
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class PromptFile:
    """Represents a prompt file with metadata"""
    name: str
    path: str
    description: str
    prompt_count: int
    last_modified: str
    size_bytes: int
    hash: str
    
@dataclass
class Prompt:
    """Represents a single prompt"""
    id: str
    file: str
    template: str
    variables: List[str]
    output_format: str
    description: Optional[str] = None
    max_length: Optional[int] = None
    valid_outputs: Optional[List[str]] = None

@dataclass
class PromptTestResult:
    """Result from testing a prompt"""
    success: bool
    output: str
    execution_time_ms: float
    error: Optional[str] = None
    variables_used: Optional[Dict] = None

class PromptManagementService:
    """
    Service for managing prompt files and templates
    """
    
    def __init__(self, prompts_dir: str = None, backup_dir: str = None, llm_function=None):
        """
        Initialize the prompt management service
        
        Args:
            prompts_dir: Directory containing prompt files
            backup_dir: Directory for backups
            llm_function: Function to test prompts with
        """
        base_dir = Path(__file__).parent.parent
        self.prompts_dir = Path(prompts_dir or base_dir / "prompts")
        self.backup_dir = Path(backup_dir or base_dir / "prompt_backups")
        self.llm = llm_function
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # File descriptions
        self.file_descriptions = {
            "intent.json": "Intent detection and classification prompts",
            "search.json": "Product search and extraction prompts",
            "analytics.json": "Analytics and reporting prompts",
            "conversation.json": "Conversation flow and response prompts",
            "context.json": "Context understanding and reference resolution prompts"
        }
        
        logger.info(f"Initialized PromptManagementService with dir: {self.prompts_dir}")
    
    async def get_all_files(self) -> List[PromptFile]:
        """
        Get all prompt files with metadata
        """
        files = []
        
        for json_file in self.prompts_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    content = f.read()
                    data = json.loads(content)
                
                # Get file stats
                stats = json_file.stat()
                
                # Calculate hash for version tracking
                file_hash = hashlib.md5(content.encode()).hexdigest()
                
                # Count prompts
                prompt_count = len(data) if isinstance(data, dict) else 0
                
                file_info = PromptFile(
                    name=json_file.name,
                    path=str(json_file),
                    description=self.file_descriptions.get(
                        json_file.name, 
                        f"Custom prompt file: {json_file.name}"
                    ),
                    prompt_count=prompt_count,
                    last_modified=datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    size_bytes=stats.st_size,
                    hash=file_hash
                )
                
                files.append(file_info)
                
            except Exception as e:
                logger.error(f"Error reading file {json_file}: {e}")
                continue
        
        # Sort by name
        files.sort(key=lambda x: x.name)
        return files
    
    async def get_file_content(self, filename: str) -> Dict:
        """
        Get the content of a specific prompt file
        """
        file_path = self.prompts_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file {filename} not found")
        
        if not file_path.suffix == '.json':
            raise ValueError("Only JSON files are supported")
        
        with open(file_path, 'r') as f:
            content = f.read()
            return json.loads(content)
    
    async def get_prompts_from_file(self, filename: str) -> List[Prompt]:
        """
        Get all prompts from a specific file
        """
        content = await self.get_file_content(filename)
        prompts = []
        
        for prompt_id, prompt_data in content.items():
            prompt = Prompt(
                id=prompt_id,
                file=filename,
                template=prompt_data.get('template', ''),
                variables=prompt_data.get('variables', []),
                output_format=prompt_data.get('output_format', 'text'),
                description=prompt_data.get('description'),
                max_length=prompt_data.get('max_length'),
                valid_outputs=prompt_data.get('valid_outputs')
            )
            prompts.append(prompt)
        
        return prompts
    
    async def update_prompt(self, filename: str, prompt_id: str, prompt_data: Dict) -> bool:
        """
        Update a specific prompt in a file
        """
        file_path = self.prompts_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file {filename} not found")
        
        # Create backup first
        await self.create_backup(filename)
        
        # Read current content
        with open(file_path, 'r') as f:
            content = f.read()
            data = json.loads(content)
        
        # Update the prompt
        data[prompt_id] = prompt_data
        
        # Write back
        with open(file_path, 'w') as f:
            f.write(json.dumps(data, indent=2))
        
        logger.info(f"Updated prompt {prompt_id} in {filename}")
        return True
    
    async def add_prompt(self, filename: str, prompt_id: str, prompt_data: Dict) -> bool:
        """
        Add a new prompt to a file
        """
        file_path = self.prompts_dir / filename
        
        if not file_path.exists():
            # Create new file if it doesn't exist
            data = {}
        else:
            # Create backup first
            await self.create_backup(filename)
            
            # Read current content
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                data = json.loads(content)
        
        # Check if prompt ID already exists
        if prompt_id in data:
            raise ValueError(f"Prompt {prompt_id} already exists in {filename}")
        
        # Add the new prompt
        data[prompt_id] = prompt_data
        
        # Write back
        with open(file_path, 'w') as f:
            f.write(json.dumps(data, indent=2))
        
        logger.info(f"Added prompt {prompt_id} to {filename}")
        return True
    
    async def delete_prompt(self, filename: str, prompt_id: str) -> bool:
        """
        Delete a prompt from a file
        """
        file_path = self.prompts_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file {filename} not found")
        
        # Create backup first
        await self.create_backup(filename)
        
        # Read current content
        with open(file_path, 'r') as f:
            content = f.read()
            data = json.loads(content)
        
        # Delete the prompt
        if prompt_id not in data:
            raise ValueError(f"Prompt {prompt_id} not found in {filename}")
        
        del data[prompt_id]
        
        # Write back
        with open(file_path, 'w') as f:
            f.write(json.dumps(data, indent=2))
        
        logger.info(f"Deleted prompt {prompt_id} from {filename}")
        return True
    
    async def create_backup(self, filename: str) -> str:
        """
        Create a backup of a prompt file
        """
        source_path = self.prompts_dir / filename
        
        if not source_path.exists():
            raise FileNotFoundError(f"Prompt file {filename} not found")
        
        # Create timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filename}.{timestamp}.backup"
        backup_path = self.backup_dir / backup_name
        
        # Copy file
        shutil.copy2(source_path, backup_path)
        
        logger.info(f"Created backup: {backup_name}")
        return backup_name
    
    async def list_backups(self, filename: str = None) -> List[Dict]:
        """
        List all backups, optionally filtered by filename
        """
        backups = []
        
        pattern = f"{filename}.*" if filename else "*.backup"
        
        for backup_file in self.backup_dir.glob(pattern):
            stats = backup_file.stat()
            
            # Parse the backup filename
            parts = backup_file.name.split('.')
            if len(parts) >= 3:
                original_name = f"{parts[0]}.{parts[1]}"
                timestamp_str = parts[2]
            else:
                original_name = "unknown"
                timestamp_str = "unknown"
            
            backups.append({
                'filename': backup_file.name,
                'original_file': original_name,
                'created_at': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'size_bytes': stats.st_size,
                'timestamp': timestamp_str
            })
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups
    
    async def restore_backup(self, backup_filename: str) -> bool:
        """
        Restore a prompt file from backup
        """
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup {backup_filename} not found")
        
        # Parse the original filename from backup name
        parts = backup_filename.split('.')
        if len(parts) >= 3:
            original_filename = f"{parts[0]}.{parts[1]}"
        else:
            raise ValueError(f"Invalid backup filename format: {backup_filename}")
        
        target_path = self.prompts_dir / original_filename
        
        # Create backup of current file before restoring
        if target_path.exists():
            await self.create_backup(original_filename)
        
        # Restore the backup
        shutil.copy2(backup_path, target_path)
        
        logger.info(f"Restored {original_filename} from backup {backup_filename}")
        return True
    
    async def test_prompt(self, prompt_template: str, variables: Dict[str, Any]) -> PromptTestResult:
        """
        Test a prompt with the LLM
        """
        if not self.llm:
            return PromptTestResult(
                success=False,
                output="",
                execution_time_ms=0,
                error="LLM not available for testing"
            )
        
        try:
            # Replace variables in template
            test_prompt = prompt_template
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                test_prompt = test_prompt.replace(placeholder, str(var_value))
            
            # Execute with LLM
            start_time = datetime.now()
            
            response = self.llm(
                test_prompt,
                max_tokens=200,
                temperature=0.7,
                echo=False
            )
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response and response.get('choices'):
                output = response['choices'][0]['text'].strip()
                
                return PromptTestResult(
                    success=True,
                    output=output,
                    execution_time_ms=execution_time,
                    variables_used=variables
                )
            else:
                return PromptTestResult(
                    success=False,
                    output="",
                    execution_time_ms=execution_time,
                    error="No response from LLM"
                )
                
        except Exception as e:
            logger.error(f"Error testing prompt: {e}")
            return PromptTestResult(
                success=False,
                output="",
                execution_time_ms=0,
                error=str(e)
            )
    
    async def validate_prompt_syntax(self, prompt_data: Dict) -> Dict[str, Any]:
        """
        Validate prompt syntax and structure
        """
        errors = []
        warnings = []
        
        # Required fields
        if 'template' not in prompt_data:
            errors.append("Missing required field: template")
        
        if 'variables' not in prompt_data:
            errors.append("Missing required field: variables")
        elif not isinstance(prompt_data['variables'], list):
            errors.append("Field 'variables' must be a list")
        
        # Check template for variables
        if 'template' in prompt_data and 'variables' in prompt_data:
            template = prompt_data['template']
            variables = prompt_data['variables']
            
            # Find all placeholders in template
            import re
            placeholders = re.findall(r'\{(\w+)\}', template)
            
            # Check for undefined variables
            for placeholder in placeholders:
                if placeholder not in variables:
                    warnings.append(f"Variable '{placeholder}' used in template but not defined in variables list")
            
            # Check for unused variables
            for variable in variables:
                if f"{{{variable}}}" not in template:
                    warnings.append(f"Variable '{variable}' defined but not used in template")
        
        # Validate output format
        valid_formats = ['text', 'json', 'yes_no', 'number', 'list']
        if 'output_format' in prompt_data:
            if prompt_data['output_format'] not in valid_formats:
                warnings.append(f"Unknown output format: {prompt_data['output_format']}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    async def export_prompts(self, filename: str = None) -> bytes:
        """
        Export prompts to a downloadable format
        """
        if filename:
            # Export single file
            content = await self.get_file_content(filename)
            return json.dumps(content, indent=2).encode()
        else:
            # Export all files
            all_prompts = {}
            for json_file in self.prompts_dir.glob("*.json"):
                content = await self.get_file_content(json_file.name)
                all_prompts[json_file.name] = content
            
            return json.dumps(all_prompts, indent=2).encode()
    
    async def import_prompts(self, filename: str, content: bytes, overwrite: bool = False) -> Dict:
        """
        Import prompts from uploaded content
        """
        try:
            # Parse the content
            data = json.loads(content.decode())
            
            file_path = self.prompts_dir / filename
            
            # Check if file exists
            if file_path.exists() and not overwrite:
                return {
                    'success': False,
                    'error': f"File {filename} already exists. Set overwrite=true to replace."
                }
            
            # Validate the structure
            if not isinstance(data, dict):
                return {
                    'success': False,
                    'error': "Invalid prompt file structure. Expected JSON object."
                }
            
            # Create backup if overwriting
            if file_path.exists():
                await self.create_backup(filename)
            
            # Write the new content
            with open(file_path, 'w') as f:
                f.write(json.dumps(data, indent=2))
            
            return {
                'success': True,
                'message': f"Successfully imported {len(data)} prompts to {filename}"
            }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f"Invalid JSON: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_prompt_statistics(self) -> Dict:
        """
        Get statistics about all prompts
        """
        stats = {
            'total_files': 0,
            'total_prompts': 0,
            'total_size_bytes': 0,
            'files': {},
            'most_variables': None,
            'longest_template': None,
            'backup_count': 0
        }
        
        max_variables = 0
        max_template_length = 0
        
        for json_file in self.prompts_dir.glob("*.json"):
            try:
                content = await self.get_file_content(json_file.name)
                prompts = await self.get_prompts_from_file(json_file.name)
                
                stats['total_files'] += 1
                stats['total_prompts'] += len(prompts)
                stats['total_size_bytes'] += json_file.stat().st_size
                
                stats['files'][json_file.name] = {
                    'prompt_count': len(prompts),
                    'size_bytes': json_file.stat().st_size
                }
                
                # Find prompt with most variables and longest template
                for prompt in prompts:
                    if len(prompt.variables) > max_variables:
                        max_variables = len(prompt.variables)
                        stats['most_variables'] = {
                            'prompt_id': prompt.id,
                            'file': prompt.file,
                            'variable_count': len(prompt.variables)
                        }
                    
                    if len(prompt.template) > max_template_length:
                        max_template_length = len(prompt.template)
                        stats['longest_template'] = {
                            'prompt_id': prompt.id,
                            'file': prompt.file,
                            'template_length': len(prompt.template)
                        }
                        
            except Exception as e:
                logger.error(f"Error processing {json_file.name}: {e}")
        
        # Count backups
        stats['backup_count'] = len(list(self.backup_dir.glob("*.backup")))
        
        return stats

# Export the service class
__all__ = ['PromptManagementService', 'Prompt', 'PromptFile', 'PromptTestResult']