"""
Persona Management System for AGI
Handles different AI personas with unique characteristics and behaviors
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from agi.core.database import get_db_manager
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


class PersonaType(Enum):
    """Types of personas"""
    ASSISTANT = "assistant"
    EXPERT = "expert"
    TEACHER = "teacher"
    FRIEND = "friend"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    ANALYST = "analyst"
    CUSTOM = "custom"


@dataclass
class Persona:
    """Represents an AI persona"""
    id: str
    name: str
    type: PersonaType
    description: str
    system_prompt: str
    characteristics: Dict[str, Any]
    language_style: Dict[str, Any]
    knowledge_domains: List[str]
    constraints: List[str]
    examples: List[Dict[str, str]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class PersonaManager:
    """
    Manages AI personas for different interaction styles
    """

    def __init__(self):
        """Initialize persona manager"""
        self.config = get_config()
        self.db_manager = None
        self._personas: Dict[str, Persona] = {}
        self._default_personas_loaded = False

    async def initialize(self):
        """Initialize the persona manager"""
        self.db_manager = await get_db_manager()
        await self._create_tables()
        await self._load_default_personas()
        logger.info("Persona manager initialized")

    async def _create_tables(self):
        """Create necessary database tables"""
        conn = await self.db_manager.get_connection()
        try:
            query = """
            CREATE TABLE IF NOT EXISTS agi.personas (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                type VARCHAR(50) NOT NULL,
                description TEXT,
                system_prompt TEXT NOT NULL,
                characteristics JSONB,
                language_style JSONB,
                knowledge_domains JSONB,
                constraints JSONB,
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

    async def _load_default_personas(self):
        """Load default personas into the system"""
        if self._default_personas_loaded:
            return

        default_personas = [
            {
                "id": "helpful_assistant",
                "name": "Helpful Assistant",
                "type": PersonaType.ASSISTANT,
                "description": "A friendly and helpful AI assistant",
                "system_prompt": "You are a helpful, harmless, and honest AI assistant. You aim to provide accurate, relevant, and thoughtful responses while being respectful and professional.",
                "characteristics": {
                    "tone": "friendly",
                    "formality": "moderate",
                    "empathy": "high",
                    "clarity": "high",
                    "patience": "high"
                },
                "language_style": {
                    "vocabulary": "accessible",
                    "sentence_structure": "clear and concise",
                    "use_examples": True,
                    "use_analogies": True
                },
                "knowledge_domains": ["general", "everyday tasks", "problem-solving"],
                "constraints": [
                    "Be truthful and accurate",
                    "Admit when uncertain",
                    "Respect user privacy",
                    "Avoid harmful content"
                ],
                "examples": [
                    {"user": "How do I cook pasta?", "assistant": "Here's how to cook pasta perfectly..."},
                    {"user": "What's the weather?", "assistant": "I don't have real-time weather data, but I can help you find weather resources..."}
                ]
            },
            {
                "id": "technical_expert",
                "name": "Technical Expert",
                "type": PersonaType.EXPERT,
                "description": "A technical expert focused on programming and technology",
                "system_prompt": "You are a technical expert specializing in software development, programming languages, and technology. Provide detailed, accurate technical information with code examples when appropriate.",
                "characteristics": {
                    "tone": "professional",
                    "formality": "high",
                    "precision": "very high",
                    "detail_level": "comprehensive",
                    "use_technical_terms": True
                },
                "language_style": {
                    "vocabulary": "technical",
                    "sentence_structure": "precise and structured",
                    "use_code_examples": True,
                    "use_documentation_style": True
                },
                "knowledge_domains": ["programming", "software engineering", "computer science", "technology"],
                "constraints": [
                    "Provide working code examples",
                    "Follow best practices",
                    "Cite sources when needed",
                    "Explain complex concepts clearly"
                ],
                "examples": [
                    {"user": "How do I implement a singleton in Python?", "assistant": "Here's how to implement a singleton pattern in Python..."}
                ]
            },
            {
                "id": "creative_writer",
                "name": "Creative Writer",
                "type": PersonaType.CREATIVE,
                "description": "A creative writing assistant with artistic flair",
                "system_prompt": "You are a creative writing assistant with a passion for storytelling, poetry, and artistic expression. Help users with creative writing, brainstorming, and artistic projects.",
                "characteristics": {
                    "tone": "imaginative",
                    "formality": "flexible",
                    "creativity": "very high",
                    "expressiveness": "high",
                    "use_metaphors": True
                },
                "language_style": {
                    "vocabulary": "rich and varied",
                    "sentence_structure": "flowing and artistic",
                    "use_literary_devices": True,
                    "use_vivid_descriptions": True
                },
                "knowledge_domains": ["creative writing", "literature", "poetry", "storytelling", "arts"],
                "constraints": [
                    "Encourage creativity",
                    "Respect artistic vision",
                    "Provide constructive feedback",
                    "Inspire imagination"
                ],
                "examples": [
                    {"user": "Help me write a poem about the ocean", "assistant": "Let's craft a poem that captures the ocean's essence..."}
                ]
            },
            {
                "id": "data_analyst",
                "name": "Data Analyst",
                "type": PersonaType.ANALYST,
                "description": "A data-focused analyst providing insights and analysis",
                "system_prompt": "You are a data analyst skilled in statistics, data interpretation, and analytical thinking. Provide data-driven insights, help with analysis, and explain statistical concepts clearly.",
                "characteristics": {
                    "tone": "analytical",
                    "formality": "professional",
                    "objectivity": "very high",
                    "precision": "very high",
                    "use_data": True
                },
                "language_style": {
                    "vocabulary": "analytical and precise",
                    "sentence_structure": "logical and structured",
                    "use_statistics": True,
                    "use_visualizations": True
                },
                "knowledge_domains": ["statistics", "data analysis", "business intelligence", "research methods"],
                "constraints": [
                    "Base conclusions on data",
                    "Acknowledge limitations",
                    "Provide confidence levels",
                    "Suggest appropriate methods"
                ],
                "examples": [
                    {"user": "Analyze this sales trend", "assistant": "Let me analyze the sales trend data..."}
                ]
            },
            {
                "id": "friendly_tutor",
                "name": "Friendly Tutor",
                "type": PersonaType.TEACHER,
                "description": "An educational tutor focused on learning and understanding",
                "system_prompt": "You are a patient and encouraging tutor who helps users learn and understand concepts. Break down complex topics, provide examples, and adapt to different learning styles.",
                "characteristics": {
                    "tone": "encouraging",
                    "formality": "casual",
                    "patience": "very high",
                    "adaptability": "high",
                    "use_scaffolding": True
                },
                "language_style": {
                    "vocabulary": "grade-appropriate",
                    "sentence_structure": "simple and clear",
                    "use_examples": True,
                    "use_questions": True
                },
                "knowledge_domains": ["education", "learning strategies", "various subjects"],
                "constraints": [
                    "Adapt to learning level",
                    "Encourage questions",
                    "Provide step-by-step guidance",
                    "Check understanding"
                ],
                "examples": [
                    {"user": "I don't understand fractions", "assistant": "Let's break down fractions step by step..."}
                ]
            }
        ]

        for persona_data in default_personas:
            await self.create_persona(**persona_data)

        self._default_personas_loaded = True

    async def create_persona(
        self,
        id: str,
        name: str,
        type: PersonaType,
        description: str,
        system_prompt: str,
        characteristics: Dict[str, Any],
        language_style: Dict[str, Any],
        knowledge_domains: List[str],
        constraints: List[str],
        examples: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Persona:
        """Create a new persona"""

        # Check if persona already exists
        existing = await self.get_persona(id)
        if existing:
            logger.info(f"Persona {id} already exists")
            return existing

        persona = Persona(
            id=id,
            name=name,
            type=type if isinstance(type, PersonaType) else PersonaType(type),
            description=description,
            system_prompt=system_prompt,
            characteristics=characteristics,
            language_style=language_style,
            knowledge_domains=knowledge_domains,
            constraints=constraints,
            examples=examples,
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )

        # Store in database
        query = """
        INSERT INTO agi.personas (
            id, name, type, description, system_prompt,
            characteristics, language_style, knowledge_domains,
            constraints, examples, metadata, is_active
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        ON CONFLICT (id) DO NOTHING
        """

        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(
                query,
                persona.id,
                persona.name,
                persona.type.value,
                persona.description,
                persona.system_prompt,
                json.dumps(persona.characteristics),
                json.dumps(persona.language_style),
                json.dumps(persona.knowledge_domains),
                json.dumps(persona.constraints),
                json.dumps(persona.examples),
                json.dumps(persona.metadata),
                persona.is_active
            )
        finally:
            await self.db_manager.release_connection(conn)

        # Cache it
        self._personas[persona.id] = persona

        logger.info(f"Created persona: {persona.name}")
        return persona

    async def get_persona(self, persona_id: str) -> Optional[Persona]:
        """Get a persona by ID"""
        # Check cache first
        if persona_id in self._personas:
            return self._personas[persona_id]

        # Query database
        query = """
        SELECT * FROM agi.personas WHERE id = $1 AND is_active = TRUE
        """

        conn = await self.db_manager.get_connection()
        try:
            row = await conn.fetchrow(query, persona_id)
        finally:
            await self.db_manager.release_connection(conn)

        if row:
            persona = Persona(
                id=row['id'],
                name=row['name'],
                type=PersonaType(row['type']),
                description=row['description'],
                system_prompt=row['system_prompt'],
                characteristics=json.loads(row['characteristics']),
                language_style=json.loads(row['language_style']),
                knowledge_domains=json.loads(row['knowledge_domains']),
                constraints=json.loads(row['constraints']),
                examples=json.loads(row['examples']),
                metadata=json.loads(row['metadata']),
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                is_active=row['is_active']
            )

            # Cache it
            self._personas[persona_id] = persona
            return persona

        return None

    async def list_personas(self, active_only: bool = True) -> List[Persona]:
        """List all personas"""
        query = """
        SELECT * FROM agi.personas
        """
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY created_at DESC"

        conn = await self.db_manager.get_connection()
        try:
            rows = await conn.fetch(query)
        finally:
            await self.db_manager.release_connection(conn)

        personas = []
        for row in rows:
            persona = Persona(
                id=row['id'],
                name=row['name'],
                type=PersonaType(row['type']),
                description=row['description'],
                system_prompt=row['system_prompt'],
                characteristics=json.loads(row['characteristics']),
                language_style=json.loads(row['language_style']),
                knowledge_domains=json.loads(row['knowledge_domains']),
                constraints=json.loads(row['constraints']),
                examples=json.loads(row['examples']),
                metadata=json.loads(row['metadata']),
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                is_active=row['is_active']
            )
            personas.append(persona)

        return personas

    async def update_persona(
        self,
        persona_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Persona]:
        """Update a persona"""
        persona = await self.get_persona(persona_id)
        if not persona:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(persona, key):
                setattr(persona, key, value)

        persona.updated_at = datetime.now()

        # Update in database
        query = """
        UPDATE agi.personas
        SET name = $2, description = $3, system_prompt = $4,
            characteristics = $5, language_style = $6,
            knowledge_domains = $7, constraints = $8,
            examples = $9, metadata = $10,
            updated_at = $11
        WHERE id = $1
        """

        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(
                query,
                persona.id,
                persona.name,
                persona.description,
                persona.system_prompt,
                json.dumps(persona.characteristics),
                json.dumps(persona.language_style),
                json.dumps(persona.knowledge_domains),
                json.dumps(persona.constraints),
                json.dumps(persona.examples),
                json.dumps(persona.metadata),
                persona.updated_at
            )
        finally:
            await self.db_manager.release_connection(conn)

        # Update cache
        self._personas[persona_id] = persona

        return persona

    async def delete_persona(self, persona_id: str):
        """Soft delete a persona"""
        query = """
        UPDATE agi.personas
        SET is_active = FALSE, updated_at = $2
        WHERE id = $1
        """

        conn = await self.db_manager.get_connection()
        try:
            await conn.execute(query, persona_id, datetime.now())
        finally:
            await self.db_manager.release_connection(conn)

        # Remove from cache
        if persona_id in self._personas:
            del self._personas[persona_id]

        logger.info(f"Deleted persona: {persona_id}")

    def build_system_prompt(self, persona: Persona, context: Optional[Dict[str, Any]] = None) -> str:
        """Build a complete system prompt from persona"""
        prompt_parts = [persona.system_prompt]

        # Add characteristics
        if persona.characteristics:
            char_str = ", ".join([f"{k}: {v}" for k, v in persona.characteristics.items()])
            prompt_parts.append(f"\nCharacteristics: {char_str}")

        # Add language style
        if persona.language_style:
            style_str = ", ".join([f"{k}: {v}" for k, v in persona.language_style.items()])
            prompt_parts.append(f"Language Style: {style_str}")

        # Add knowledge domains
        if persona.knowledge_domains:
            prompt_parts.append(f"Knowledge Domains: {', '.join(persona.knowledge_domains)}")

        # Add constraints
        if persona.constraints:
            prompt_parts.append("\nConstraints:")
            for constraint in persona.constraints:
                prompt_parts.append(f"- {constraint}")

        # Add context if provided
        if context:
            prompt_parts.append(f"\nContext: {json.dumps(context, indent=2)}")

        return "\n".join(prompt_parts)


# Singleton instance
_persona_manager: Optional[PersonaManager] = None

async def get_persona_manager() -> PersonaManager:
    """Get singleton persona manager instance"""
    global _persona_manager
    if _persona_manager is None:
        _persona_manager = PersonaManager()
        await _persona_manager.initialize()
    return _persona_manager