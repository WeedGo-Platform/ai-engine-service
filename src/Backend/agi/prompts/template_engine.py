"""
Prompt Template Engine for AGI
Handles dynamic prompt templates with variable substitution and composition
"""

import re
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from agi.core.database import get_db_manager
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Types of templates"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    CONTEXT = "context"
    CHAIN = "chain"
    CUSTOM = "custom"


@dataclass
class PromptTemplate:
    """Represents a prompt template"""
    id: str
    name: str
    type: TemplateType
    template: str
    variables: List[str]
    description: str
    examples: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class TemplateEngine:
    """
    Engine for managing and rendering prompt templates
    """

    def __init__(self):
        """Initialize template engine"""
        self.config = get_config()
        self.db_manager = None
        self._templates: Dict[str, PromptTemplate] = {}
        self._default_templates_loaded = False
        self._variable_pattern = re.compile(r'\{\{\s*(\w+)\s*\}\}')
        self._conditional_pattern = re.compile(r'\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}', re.DOTALL)
        self._loop_pattern = re.compile(r'\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}', re.DOTALL)

    async def initialize(self):
        """Initialize the template engine"""
        self.db_manager = await get_db_manager()
        await self._create_tables()
        await self._load_default_templates()
        logger.info("Template engine initialized")

    async def _create_tables(self):
        """Create necessary database tables"""
        conn = await self.db_manager.get_connection()
        try:
            query = """
            CREATE TABLE IF NOT EXISTS agi.prompt_templates (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                type VARCHAR(50) NOT NULL,
                template TEXT NOT NULL,
                variables JSONB,
                description TEXT,
                examples JSONB,
                metadata JSONB,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(query)
        finally:
            await self.db_manager.release_connection(conn)

    async def _load_default_templates(self):
        """Load default templates into the system"""
        if self._default_templates_loaded:
            return

        default_templates = [
            {
                "id": "chain_of_thought",
                "name": "Chain of Thought",
                "type": TemplateType.SYSTEM,
                "template": """Let's approach this step-by-step:

{{ question }}

Step 1: Understand the problem
- What are we trying to solve?
- What information do we have?

Step 2: Break down the approach
- What steps do we need to take?
- What methods should we use?

Step 3: Execute the solution
{% if context %}
Using the following context:
{{ context }}
{% endif %}

Step 4: Verify and conclude
- Does our answer make sense?
- Have we addressed all aspects?

Final Answer:""",
                "variables": ["question", "context"],
                "description": "Template for chain-of-thought reasoning",
                "examples": [
                    {
                        "question": "What is 15% of 200?",
                        "context": None,
                        "expected": "Step-by-step calculation leading to 30"
                    }
                ]
            },
            {
                "id": "few_shot_learning",
                "name": "Few-Shot Learning",
                "type": TemplateType.USER,
                "template": """Here are some examples of {{ task_type }}:

{% for example in examples %}
Input: {{ example.input }}
Output: {{ example.output }}

{% endfor %}
Now, please {{ task_description }}:

Input: {{ input }}
Output:""",
                "variables": ["task_type", "task_description", "examples", "input"],
                "description": "Template for few-shot learning tasks",
                "examples": [
                    {
                        "task_type": "sentiment analysis",
                        "task_description": "analyze the sentiment",
                        "examples": [
                            {"input": "I love this!", "output": "Positive"},
                            {"input": "This is terrible", "output": "Negative"}
                        ],
                        "input": "It's okay I guess"
                    }
                ]
            },
            {
                "id": "tool_use",
                "name": "Tool Use",
                "type": TemplateType.TOOL,
                "template": """You have access to the following tools:

{% for tool in available_tools %}
- {{ tool.name }}: {{ tool.description }}
  Parameters: {{ tool.parameters }}
{% endfor %}

To use a tool, format your response as:
Thought: [Your reasoning about what to do]
Action: [Tool name]
Action Input: [Tool parameters as JSON]

Question: {{ question }}

Let's solve this step by step.""",
                "variables": ["available_tools", "question"],
                "description": "Template for tool usage",
                "examples": [
                    {
                        "available_tools": [
                            {
                                "name": "calculator",
                                "description": "Perform calculations",
                                "parameters": {"expression": "string"}
                            }
                        ],
                        "question": "What is 25 * 4?"
                    }
                ]
            },
            {
                "id": "rag_context",
                "name": "RAG Context",
                "type": TemplateType.CONTEXT,
                "template": """Answer the following question based on the provided context.

Context:
{% for chunk in context_chunks %}
[{{ loop.index }}] {{ chunk.content }}
(Source: {{ chunk.source }})

{% endfor %}

Question: {{ question }}

Instructions:
- Base your answer on the provided context
- If the context doesn't contain relevant information, say so
- Cite sources when making specific claims

Answer:""",
                "variables": ["context_chunks", "question"],
                "description": "Template for RAG-based responses",
                "examples": [
                    {
                        "context_chunks": [
                            {
                                "content": "Python is a high-level programming language.",
                                "source": "python_guide.pdf"
                            }
                        ],
                        "question": "What is Python?"
                    }
                ]
            },
            {
                "id": "code_generation",
                "name": "Code Generation",
                "type": TemplateType.SYSTEM,
                "template": """Generate {{ language }} code for the following task:

Task: {{ task }}

{% if requirements %}
Requirements:
{% for req in requirements %}
- {{ req }}
{% endfor %}
{% endif %}

{% if constraints %}
Constraints:
{% for constraint in constraints %}
- {{ constraint }}
{% endfor %}
{% endif %}

{% if examples %}
Example usage:
```{{ language }}
{{ examples }}
```
{% endif %}

Please provide:
1. Clean, well-commented code
2. Error handling where appropriate
3. Example usage if not provided

Code:""",
                "variables": ["language", "task", "requirements", "constraints", "examples"],
                "description": "Template for code generation tasks",
                "examples": [
                    {
                        "language": "Python",
                        "task": "Create a function to calculate factorial",
                        "requirements": ["Handle edge cases", "Use recursion"],
                        "constraints": ["Must be efficient"],
                        "examples": "factorial(5) # Returns 120"
                    }
                ]
            },
            {
                "id": "summarization",
                "name": "Summarization",
                "type": TemplateType.USER,
                "template": """Please summarize the following text:

Text:
{{ text }}

{% if style %}
Summary Style: {{ style }}
{% endif %}

{% if max_length %}
Maximum Length: {{ max_length }} words
{% endif %}

{% if key_points %}
Focus on these key points:
{% for point in key_points %}
- {{ point }}
{% endfor %}
{% endif %}

Summary:""",
                "variables": ["text", "style", "max_length", "key_points"],
                "description": "Template for text summarization",
                "examples": [
                    {
                        "text": "Long article text here...",
                        "style": "bullet points",
                        "max_length": 100,
                        "key_points": ["main findings", "methodology"]
                    }
                ]
            },
            {
                "id": "dialogue",
                "name": "Dialogue",
                "type": TemplateType.CHAIN,
                "template": """{{ system_message }}

{% for message in conversation_history %}
{{ message.role }}: {{ message.content }}
{% endfor %}

{{ current_role }}: {{ current_message }}

Assistant:""",
                "variables": ["system_message", "conversation_history", "current_role", "current_message"],
                "description": "Template for dialogue interactions",
                "examples": [
                    {
                        "system_message": "You are a helpful assistant.",
                        "conversation_history": [
                            {"role": "User", "content": "Hello"},
                            {"role": "Assistant", "content": "Hi! How can I help you?"}
                        ],
                        "current_role": "User",
                        "current_message": "What's the weather like?"
                    }
                ]
            }
        ]

        for template_data in default_templates:
            await self.create_template(**template_data)

        self._default_templates_loaded = True

    async def create_template(
        self,
        id: str,
        name: str,
        type: TemplateType,
        template: str,
        variables: List[str],
        description: str,
        examples: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> PromptTemplate:
        """Create a new template"""
        
        # Check if template already exists
        existing = await self.get_template(id)
        if existing:
            logger.info(f"Template {id} already exists")
            return existing

        prompt_template = PromptTemplate(
            id=id,
            name=name,
            type=type if isinstance(type, TemplateType) else TemplateType(type),
            template=template,
            variables=variables,
            description=description,
            examples=examples,
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )

        # Store in database
        query = """
        INSERT INTO agi.prompt_templates (
            id, name, type, template, variables,
            description, examples, metadata, is_active
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO NOTHING
        """

        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(
                query,
                prompt_template.id,
                prompt_template.name,
                prompt_template.type.value,
                prompt_template.template,
                json.dumps(prompt_template.variables),
                prompt_template.description,
                json.dumps(prompt_template.examples),
                json.dumps(prompt_template.metadata),
                prompt_template.is_active
            )
        finally:
            await self.db_manager.release_connection(conn)

        # Cache it
        self._templates[prompt_template.id] = prompt_template

        logger.info(f"Created template: {prompt_template.name}")
        return prompt_template

    async def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a template by ID"""
        # Check cache first
        if template_id in self._templates:
            return self._templates[template_id]

        # Query database
        query = """
        SELECT * FROM agi.prompt_templates WHERE id = $1 AND is_active = TRUE
        """

        conn = await self.db_manager.get_connection()
        try:
            row = await conn.fetchrow(query, template_id)
        finally:
            await self.db_manager.release_connection(conn)

        if row:
            prompt_template = PromptTemplate(
                id=row['id'],
                name=row['name'],
                type=TemplateType(row['type']),
                template=row['template'],
                variables=json.loads(row['variables']),
                description=row['description'],
                examples=json.loads(row['examples']),
                metadata=json.loads(row['metadata']),
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                is_active=row['is_active']
            )

            # Cache it
            self._templates[template_id] = prompt_template
            return prompt_template

        return None

    def render(
        self,
        template: Union[str, PromptTemplate],
        variables: Dict[str, Any]
    ) -> str:
        """
        Render a template with variables
        
        Args:
            template: Template string or PromptTemplate object
            variables: Variables to substitute
            
        Returns:
            Rendered template
        """
        if isinstance(template, PromptTemplate):
            template_str = template.template
        else:
            template_str = template

        # Process loops first
        template_str = self._process_loops(template_str, variables)
        
        # Process conditionals
        template_str = self._process_conditionals(template_str, variables)
        
        # Process simple variables
        template_str = self._process_variables(template_str, variables)
        
        return template_str.strip()

    def _process_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Process simple variable substitution"""
        def replace_var(match):
            var_name = match.group(1)
            if var_name in variables:
                value = variables[var_name]
                if value is None:
                    return ""
                elif isinstance(value, (list, dict)):
                    return json.dumps(value, indent=2)
                else:
                    return str(value)
            return match.group(0)  # Keep original if not found
        
        return self._variable_pattern.sub(replace_var, template)

    def _process_conditionals(self, template: str, variables: Dict[str, Any]) -> str:
        """Process conditional blocks"""
        def process_condition(match):
            condition_var = match.group(1)
            content = match.group(2)
            
            # Check if condition is true
            if condition_var in variables:
                value = variables[condition_var]
                # Check truthiness
                if value and value != "" and value != [] and value != {}:
                    return content
            return ""
        
        return self._conditional_pattern.sub(process_condition, template)

    def _process_loops(self, template: str, variables: Dict[str, Any]) -> str:
        """Process loop blocks"""
        def process_loop(match):
            item_var = match.group(1)
            collection_var = match.group(2)
            loop_content = match.group(3)

            if collection_var not in variables:
                return ""

            collection = variables[collection_var]
            if not isinstance(collection, (list, tuple)):
                return ""

            results = []
            for index, item in enumerate(collection):
                # Create loop context
                loop_vars = variables.copy()
                loop_vars[item_var] = item
                loop_vars['loop'] = {'index': index + 1, 'first': index == 0, 'last': index == len(collection) - 1}

                # Process the loop content with loop variables
                # Also handle nested variables within loop items
                processed = loop_content
                for key, value in loop_vars.items():
                    if isinstance(value, dict) and key == item_var:
                        # Replace nested variables like {{ tool.name }}
                        for nested_key, nested_value in value.items():
                            pattern = f"{{{{ {key}.{nested_key} }}}}"
                            processed = processed.replace(pattern, str(nested_value))

                # Process remaining simple variables
                processed = self._process_variables(processed, loop_vars)
                results.append(processed)

            return "".join(results)

        return self._loop_pattern.sub(process_loop, template)

    async def list_templates(self, active_only: bool = True) -> List[PromptTemplate]:
        """List all templates"""
        query = """
        SELECT * FROM agi.prompt_templates
        """
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY created_at DESC"

        conn = await self.db_manager.get_connection()
        try:
            rows = await conn.fetch(query)
        finally:
            await self.db_manager.release_connection(conn)

        templates = []
        for row in rows:
            prompt_template = PromptTemplate(
                id=row['id'],
                name=row['name'],
                type=TemplateType(row['type']),
                template=row['template'],
                variables=json.loads(row['variables']),
                description=row['description'],
                examples=json.loads(row['examples']),
                metadata=json.loads(row['metadata']),
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                is_active=row['is_active']
            )
            templates.append(prompt_template)

        return templates

    async def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> Optional[PromptTemplate]:
        """Update a template"""
        template = await self.get_template(template_id)
        if not template:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = datetime.now()

        # Extract variables from updated template
        if 'template' in updates:
            template.variables = self.extract_variables(template.template)

        # Update in database
        query = """
        UPDATE agi.prompt_templates
        SET name = $2, template = $3, variables = $4,
            description = $5, examples = $6, metadata = $7,
            updated_at = $8
        WHERE id = $1
        """

        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(
                query,
                template.id,
                template.name,
                template.template,
                json.dumps(template.variables),
                template.description,
                json.dumps(template.examples),
                json.dumps(template.metadata),
                template.updated_at
            )
        finally:
            await self.db_manager.release_connection(conn)

        # Update cache
        self._templates[template_id] = template

        return template

    async def delete_template(self, template_id: str):
        """Soft delete a template"""
        query = """
        UPDATE agi.prompt_templates
        SET is_active = FALSE, updated_at = $2
        WHERE id = $1
        """

        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(query, template_id, datetime.now())
        finally:
            await self.db_manager.release_connection(conn)

        # Remove from cache
        if template_id in self._templates:
            del self._templates[template_id]

        logger.info(f"Deleted template: {template_id}")

    def extract_variables(self, template_str: str) -> List[str]:
        """Extract variable names from a template string"""
        variables = set()
        
        # Extract simple variables
        for match in self._variable_pattern.finditer(template_str):
            variables.add(match.group(1))
        
        # Extract conditional variables
        for match in self._conditional_pattern.finditer(template_str):
            variables.add(match.group(1))
        
        # Extract loop variables
        for match in self._loop_pattern.finditer(template_str):
            variables.add(match.group(2))  # Collection variable
        
        return sorted(list(variables))

    def compose_templates(
        self,
        templates: List[Union[str, PromptTemplate]],
        variables: Dict[str, Any],
        separator: str = "\n\n"
    ) -> str:
        """
        Compose multiple templates together
        
        Args:
            templates: List of templates to compose
            variables: Variables for all templates
            separator: String to join templates
            
        Returns:
            Composed and rendered template
        """
        rendered_parts = []
        
        for template in templates:
            rendered = self.render(template, variables)
            if rendered:  # Only add non-empty parts
                rendered_parts.append(rendered)
        
        return separator.join(rendered_parts)


# Singleton instance
_template_engine: Optional[TemplateEngine] = None

async def get_template_engine() -> TemplateEngine:
    """Get singleton template engine instance"""
    global _template_engine
    if _template_engine is None:
        _template_engine = TemplateEngine()
        await _template_engine.initialize()
    return _template_engine