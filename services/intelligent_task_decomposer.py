"""
Intelligent Task Decomposer
Breaks down complex tasks into optimal subtasks for multi-model execution
"""
import re
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SubtaskType(Enum):
    """Types of subtasks that can be identified"""
    INFORMATION_GATHERING = "info_gather"
    REASONING = "reasoning"
    CALCULATION = "calculation"
    TRANSLATION = "translation"
    SEARCH = "search"
    COMPARISON = "comparison"
    GENERATION = "generation"
    VALIDATION = "validation"
    SUMMARIZATION = "summarization"

@dataclass
class Subtask:
    """Represents a single subtask"""
    id: str
    type: SubtaskType
    description: str
    dependencies: List[str]  # IDs of subtasks this depends on
    required_capabilities: List[str]
    estimated_tokens: int
    priority: int  # 1-10, higher is more important
    can_parallelize: bool

class IntelligentTaskDecomposer:
    """
    Intelligently decomposes complex tasks into subtasks
    Uses linguistic analysis and task patterns
    """
    
    def __init__(self, llm_instance=None):
        self.llm = llm_instance
        self.decomposition_patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict:
        """Load task decomposition patterns"""
        return {
            "sequential_indicators": ["then", "after", "next", "finally", "followed by"],
            "parallel_indicators": ["and", "also", "as well as", "additionally"],
            "comparison_indicators": ["compare", "versus", "vs", "better", "difference"],
            "multi_part_indicators": ["first", "second", "third", "lastly"],
            "condition_indicators": ["if", "when", "unless", "provided that"],
        }
    
    async def decompose_task(
        self,
        task: str,
        context: Optional[Dict] = None,
        max_subtasks: int = 10
    ) -> List[Subtask]:
        """
        Decompose a complex task into subtasks
        
        Args:
            task: The complex task to decompose
            context: Additional context
            max_subtasks: Maximum number of subtasks to create
        """
        
        # First, try rule-based decomposition
        subtasks = self._rule_based_decomposition(task)
        
        # If too simple or complex, use model-based decomposition
        if len(subtasks) < 2 or len(subtasks) > max_subtasks:
            if self.llm:
                subtasks = await self._model_based_decomposition(task, context, max_subtasks)
        
        # Add dependencies and priorities
        subtasks = self._analyze_dependencies(subtasks)
        subtasks = self._assign_priorities(subtasks)
        
        return subtasks
    
    def _rule_based_decomposition(self, task: str) -> List[Subtask]:
        """Use rules to decompose task"""
        subtasks = []
        task_lower = task.lower()
        
        # Check for explicit multi-part structure
        if any(indicator in task_lower for indicator in self.decomposition_patterns["multi_part_indicators"]):
            parts = self._extract_numbered_parts(task)
            for i, part in enumerate(parts):
                subtasks.append(self._create_subtask(part, i))
        
        # Check for sequential tasks
        elif any(indicator in task_lower for indicator in self.decomposition_patterns["sequential_indicators"]):
            parts = self._split_sequential(task)
            for i, part in enumerate(parts):
                subtask = self._create_subtask(part, i)
                if i > 0:
                    subtask.dependencies = [f"subtask_{i-1}"]
                subtasks.append(subtask)
        
        # Check for parallel tasks
        elif any(indicator in task_lower for indicator in self.decomposition_patterns["parallel_indicators"]):
            parts = self._split_parallel(task)
            for i, part in enumerate(parts):
                subtask = self._create_subtask(part, i)
                subtask.can_parallelize = True
                subtasks.append(subtask)
        
        # Check for comparison tasks
        elif any(indicator in task_lower for indicator in self.decomposition_patterns["comparison_indicators"]):
            subtasks = self._decompose_comparison(task)
        
        # Single complex task - analyze components
        else:
            components = self._analyze_task_components(task)
            for i, comp in enumerate(components):
                subtasks.append(self._create_subtask(comp, i))
        
        return subtasks
    
    def _extract_numbered_parts(self, task: str) -> List[str]:
        """Extract numbered or listed parts from task"""
        parts = []
        
        # Look for patterns like "1.", "2.", etc.
        numbered_pattern = r'(\d+\.|\d+\))\s*([^\.]+)'
        matches = re.findall(numbered_pattern, task)
        if matches:
            parts = [match[1].strip() for match in matches]
        
        # Look for "first", "second", etc.
        ordinal_parts = []
        ordinals = ["first", "second", "third", "fourth", "fifth"]
        task_lower = task.lower()
        
        for i, ordinal in enumerate(ordinals):
            if ordinal in task_lower:
                # Extract text after ordinal
                start_idx = task_lower.index(ordinal)
                end_idx = len(task)
                
                # Find next ordinal or end
                for next_ord in ordinals[i+1:]:
                    if next_ord in task_lower:
                        end_idx = task_lower.index(next_ord)
                        break
                
                part = task[start_idx:end_idx].strip()
                # Remove the ordinal word itself
                part = re.sub(f'^{ordinal}[,:]?\\s*', '', part, flags=re.IGNORECASE)
                ordinal_parts.append(part)
        
        return parts if parts else ordinal_parts
    
    def _split_sequential(self, task: str) -> List[str]:
        """Split task by sequential indicators"""
        parts = []
        
        # Split by sequential words
        for indicator in self.decomposition_patterns["sequential_indicators"]:
            if indicator in task.lower():
                # Use regex to split while preserving context
                pattern = f'\\s+{indicator}\\s+'
                splits = re.split(pattern, task, flags=re.IGNORECASE)
                if len(splits) > 1:
                    return [s.strip() for s in splits if s.strip()]
        
        # Fallback: split by sentences
        sentences = re.split(r'[.!?]+', task)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_parallel(self, task: str) -> List[str]:
        """Split task by parallel indicators"""
        parts = []
        
        # Split by "and" but be careful about context
        if " and " in task.lower():
            # Don't split if "and" is part of a phrase
            protected_phrases = ["products and prices", "thc and cbd", "indica and sativa"]
            temp_task = task
            
            # Replace protected phrases temporarily
            for phrase in protected_phrases:
                temp_task = temp_task.replace(phrase, phrase.replace(" and ", "_AND_"))
            
            # Now split
            splits = temp_task.split(" and ")
            
            # Restore protected phrases
            parts = []
            for split in splits:
                parts.append(split.replace("_AND_", " and ").strip())
        
        return parts if len(parts) > 1 else [task]
    
    def _decompose_comparison(self, task: str) -> List[Subtask]:
        """Decompose a comparison task"""
        subtasks = []
        
        # Extract items being compared
        comparison_match = re.search(r'compare\s+(.+?)\s+(?:and|with|versus|vs|to)\s+(.+)', task, re.IGNORECASE)
        
        if comparison_match:
            item1 = comparison_match.group(1).strip()
            item2 = comparison_match.group(2).strip()
            
            # Create subtasks for each item
            subtasks.append(Subtask(
                id="subtask_0",
                type=SubtaskType.INFORMATION_GATHERING,
                description=f"Gather information about {item1}",
                dependencies=[],
                required_capabilities=["search", "extraction"],
                estimated_tokens=100,
                priority=8,
                can_parallelize=True
            ))
            
            subtasks.append(Subtask(
                id="subtask_1",
                type=SubtaskType.INFORMATION_GATHERING,
                description=f"Gather information about {item2}",
                dependencies=[],
                required_capabilities=["search", "extraction"],
                estimated_tokens=100,
                priority=8,
                can_parallelize=True
            ))
            
            subtasks.append(Subtask(
                id="subtask_2",
                type=SubtaskType.COMPARISON,
                description=f"Compare {item1} with {item2}",
                dependencies=["subtask_0", "subtask_1"],
                required_capabilities=["reasoning", "analysis"],
                estimated_tokens=200,
                priority=9,
                can_parallelize=False
            ))
        
        return subtasks
    
    def _analyze_task_components(self, task: str) -> List[str]:
        """Analyze and extract components from a complex task"""
        components = []
        
        # Check for questions
        questions = re.findall(r'[^.!?]*\?', task)
        components.extend(questions)
        
        # Check for commands/imperatives
        imperatives = []
        verbs = ["show", "find", "tell", "explain", "describe", "list", "recommend", "suggest"]
        for verb in verbs:
            if task.lower().startswith(verb) or f" {verb} " in task.lower():
                # Extract the clause starting with this verb
                pattern = f'{verb}\\s+[^.!?]+'
                matches = re.findall(pattern, task, re.IGNORECASE)
                imperatives.extend(matches)
        
        components.extend(imperatives)
        
        # If no components found, treat as single task
        if not components:
            components = [task]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_components = []
        for comp in components:
            if comp not in seen:
                seen.add(comp)
                unique_components.append(comp)
        
        return unique_components
    
    def _create_subtask(self, description: str, index: int) -> Subtask:
        """Create a subtask from description"""
        # Determine type based on keywords
        task_type = self._determine_task_type(description)
        
        # Determine required capabilities
        capabilities = self._determine_capabilities(description, task_type)
        
        # Estimate tokens
        tokens = len(description.split()) * 10  # Rough estimate
        
        return Subtask(
            id=f"subtask_{index}",
            type=task_type,
            description=description,
            dependencies=[],
            required_capabilities=capabilities,
            estimated_tokens=tokens,
            priority=5,  # Default priority
            can_parallelize=task_type != SubtaskType.REASONING
        )
    
    def _determine_task_type(self, description: str) -> SubtaskType:
        """Determine the type of a subtask"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ["search", "find", "show", "list"]):
            return SubtaskType.SEARCH
        elif any(word in desc_lower for word in ["translate", "in spanish", "in french"]):
            return SubtaskType.TRANSLATION
        elif any(word in desc_lower for word in ["compare", "versus", "difference"]):
            return SubtaskType.COMPARISON
        elif any(word in desc_lower for word in ["why", "how", "explain"]):
            return SubtaskType.REASONING
        elif any(word in desc_lower for word in ["calculate", "compute", "count"]):
            return SubtaskType.CALCULATION
        elif any(word in desc_lower for word in ["summarize", "summary", "brief"]):
            return SubtaskType.SUMMARIZATION
        elif any(word in desc_lower for word in ["create", "generate", "write"]):
            return SubtaskType.GENERATION
        elif any(word in desc_lower for word in ["check", "verify", "validate"]):
            return SubtaskType.VALIDATION
        else:
            return SubtaskType.INFORMATION_GATHERING
    
    def _determine_capabilities(self, description: str, task_type: SubtaskType) -> List[str]:
        """Determine required capabilities for a subtask"""
        capabilities = []
        
        # Map task types to capabilities
        type_capabilities = {
            SubtaskType.SEARCH: ["search", "retrieval"],
            SubtaskType.TRANSLATION: ["multilingual", "translation"],
            SubtaskType.COMPARISON: ["reasoning", "analysis"],
            SubtaskType.REASONING: ["reasoning", "logic"],
            SubtaskType.CALCULATION: ["math", "computation"],
            SubtaskType.SUMMARIZATION: ["summarization", "extraction"],
            SubtaskType.GENERATION: ["generation", "creativity"],
            SubtaskType.VALIDATION: ["verification", "checking"],
            SubtaskType.INFORMATION_GATHERING: ["extraction", "comprehension"]
        }
        
        capabilities.extend(type_capabilities.get(task_type, []))
        
        # Add language-specific capabilities
        if any(lang in description.lower() for lang in ["spanish", "french", "chinese", "arabic"]):
            capabilities.append("multilingual")
        
        # Add domain-specific capabilities
        if any(term in description.lower() for term in ["thc", "cbd", "strain", "indica", "sativa"]):
            capabilities.append("cannabis_domain")
        
        return list(set(capabilities))  # Remove duplicates
    
    def _analyze_dependencies(self, subtasks: List[Subtask]) -> List[Subtask]:
        """Analyze and set dependencies between subtasks"""
        
        for i, subtask in enumerate(subtasks):
            # Information gathering usually comes first
            if subtask.type == SubtaskType.INFORMATION_GATHERING:
                subtask.dependencies = []
            
            # Reasoning and comparison depend on information
            elif subtask.type in [SubtaskType.REASONING, SubtaskType.COMPARISON]:
                # Depend on all previous info gathering tasks
                deps = [
                    st.id for j, st in enumerate(subtasks[:i])
                    if st.type == SubtaskType.INFORMATION_GATHERING
                ]
                subtask.dependencies = deps
            
            # Summarization usually comes last
            elif subtask.type == SubtaskType.SUMMARIZATION:
                # Depend on all previous tasks
                subtask.dependencies = [st.id for st in subtasks[:i]]
            
            # Validation depends on generation
            elif subtask.type == SubtaskType.VALIDATION:
                # Depend on generation tasks
                deps = [
                    st.id for j, st in enumerate(subtasks[:i])
                    if st.type == SubtaskType.GENERATION
                ]
                subtask.dependencies = deps
        
        return subtasks
    
    def _assign_priorities(self, subtasks: List[Subtask]) -> List[Subtask]:
        """Assign priorities to subtasks"""
        
        for subtask in subtasks:
            # Base priority on type
            type_priorities = {
                SubtaskType.SEARCH: 8,
                SubtaskType.INFORMATION_GATHERING: 7,
                SubtaskType.REASONING: 9,
                SubtaskType.COMPARISON: 8,
                SubtaskType.TRANSLATION: 6,
                SubtaskType.GENERATION: 7,
                SubtaskType.SUMMARIZATION: 5,
                SubtaskType.VALIDATION: 6,
                SubtaskType.CALCULATION: 7
            }
            
            subtask.priority = type_priorities.get(subtask.type, 5)
            
            # Boost priority if no dependencies (can start immediately)
            if not subtask.dependencies:
                subtask.priority += 1
            
            # Cap at 10
            subtask.priority = min(subtask.priority, 10)
        
        return subtasks
    
    async def _model_based_decomposition(
        self,
        task: str,
        context: Optional[Dict],
        max_subtasks: int
    ) -> List[Subtask]:
        """Use LLM to decompose complex task"""
        
        if not self.llm:
            return [self._create_subtask(task, 0)]
        
        prompt = f"""Decompose this complex task into subtasks.

Task: {task}

{f"Context: {context}" if context else ""}

Create a list of subtasks with:
1. Clear, actionable descriptions
2. Logical dependencies
3. Maximum {max_subtasks} subtasks

Format each subtask as:
- Description: [what to do]
- Type: [search/reasoning/translation/generation/etc]
- Depends on: [previous subtask numbers, or "none"]

Subtasks:"""
        
        try:
            response = self.llm(
                prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            text = response.get('choices', [{}])[0].get('text', '')
            
            # Parse response into subtasks
            subtasks = self._parse_model_response(text)
            
            return subtasks if subtasks else [self._create_subtask(task, 0)]
            
        except Exception as e:
            logger.error(f"Model-based decomposition failed: {e}")
            return [self._create_subtask(task, 0)]
    
    def _parse_model_response(self, text: str) -> List[Subtask]:
        """Parse model's decomposition response"""
        subtasks = []
        
        # Split by bullet points or numbers
        lines = text.split('\n')
        current_subtask = {}
        subtask_index = 0
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('- Description:') or line.startswith('Description:'):
                if current_subtask:
                    # Save previous subtask
                    subtasks.append(self._dict_to_subtask(current_subtask, subtask_index))
                    subtask_index += 1
                current_subtask = {'description': line.replace('- Description:', '').replace('Description:', '').strip()}
            
            elif line.startswith('- Type:') or line.startswith('Type:'):
                current_subtask['type'] = line.replace('- Type:', '').replace('Type:', '').strip()
            
            elif line.startswith('- Depends on:') or line.startswith('Depends on:'):
                current_subtask['dependencies'] = line.replace('- Depends on:', '').replace('Depends on:', '').strip()
        
        # Don't forget last subtask
        if current_subtask:
            subtasks.append(self._dict_to_subtask(current_subtask, subtask_index))
        
        return subtasks
    
    def _dict_to_subtask(self, subtask_dict: Dict, index: int) -> Subtask:
        """Convert dictionary to Subtask object"""
        
        # Map type string to enum
        type_str = subtask_dict.get('type', 'information_gathering').lower()
        type_map = {
            'search': SubtaskType.SEARCH,
            'reasoning': SubtaskType.REASONING,
            'translation': SubtaskType.TRANSLATION,
            'generation': SubtaskType.GENERATION,
            'comparison': SubtaskType.COMPARISON,
            'calculation': SubtaskType.CALCULATION,
            'summarization': SubtaskType.SUMMARIZATION,
            'validation': SubtaskType.VALIDATION
        }
        task_type = type_map.get(type_str, SubtaskType.INFORMATION_GATHERING)
        
        # Parse dependencies
        deps = []
        dep_str = subtask_dict.get('dependencies', 'none')
        if dep_str and dep_str.lower() != 'none':
            # Extract numbers from dependency string
            dep_nums = re.findall(r'\d+', dep_str)
            deps = [f"subtask_{num}" for num in dep_nums]
        
        return Subtask(
            id=f"subtask_{index}",
            type=task_type,
            description=subtask_dict.get('description', ''),
            dependencies=deps,
            required_capabilities=self._determine_capabilities(
                subtask_dict.get('description', ''), 
                task_type
            ),
            estimated_tokens=len(subtask_dict.get('description', '').split()) * 10,
            priority=5,
            can_parallelize=len(deps) == 0
        )
    
    def visualize_decomposition(self, subtasks: List[Subtask]) -> str:
        """Create a visual representation of task decomposition"""
        
        lines = ["Task Decomposition Plan:", "=" * 40]
        
        # Group by parallelizable
        parallel_tasks = [st for st in subtasks if st.can_parallelize and not st.dependencies]
        sequential_tasks = [st for st in subtasks if not st.can_parallelize or st.dependencies]
        
        if parallel_tasks:
            lines.append("\n[Parallel Execution]")
            for task in parallel_tasks:
                lines.append(f"  ├─ {task.id}: {task.description[:50]}...")
                lines.append(f"     Type: {task.type.value}, Priority: {task.priority}")
        
        if sequential_tasks:
            lines.append("\n[Sequential Execution]")
            for task in sequential_tasks:
                deps = f" (depends on: {', '.join(task.dependencies)})" if task.dependencies else ""
                lines.append(f"  → {task.id}: {task.description[:50]}...{deps}")
                lines.append(f"     Type: {task.type.value}, Priority: {task.priority}")
        
        lines.append("\n" + "=" * 40)
        lines.append(f"Total subtasks: {len(subtasks)}")
        lines.append(f"Can parallelize: {len(parallel_tasks)}")
        lines.append(f"Sequential: {len(sequential_tasks)}")
        
        return "\n".join(lines)