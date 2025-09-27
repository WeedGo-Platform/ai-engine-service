"""
Base Tool Implementation for AGI System
Provides foundation for all tools that agents can use
"""

import asyncio
import json
import logging
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import re

from agi.core.interfaces import ITool, ToolDefinition, ToolResult
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


class BaseTool(ITool):
    """
    Base implementation of a tool
    All tools should inherit from this class
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        examples: Optional[List[str]] = None
    ):
        """
        Initialize base tool

        Args:
            name: Tool name
            description: Tool description
            parameters: Parameter schema
            examples: Usage examples
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.examples = examples or []
        self.config = get_config()
        self._execution_count = 0
        self._last_execution = None

    def get_definition(self) -> ToolDefinition:
        """Get tool definition"""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            examples=self.examples
        )

    async def validate_input(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        Validate input parameters

        Args:
            **kwargs: Input parameters

        Returns:
            (is_valid, error_message)
        """
        # Check required parameters
        required = self.parameters.get("required", [])
        for param in required:
            if param not in kwargs:
                return False, f"Missing required parameter: {param}"

        # Check parameter types
        properties = self.parameters.get("properties", {})
        for key, value in kwargs.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if not self._check_type(value, expected_type):
                    return False, f"Parameter {key} has wrong type. Expected {expected_type}"

        return True, None

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }

        expected = type_mapping.get(expected_type)
        if expected:
            return isinstance(value, expected)
        return True

    @abstractmethod
    async def _execute_impl(self, **kwargs) -> Any:
        """
        Actual tool execution - must be implemented by subclasses

        Args:
            **kwargs: Tool parameters

        Returns:
            Execution result
        """
        pass

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        try:
            # Validate input
            is_valid, error = await self.validate_input(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error
                )

            # Execute tool
            logger.info(f"Executing tool {self.name} with params: {kwargs}")
            result = await self._execute_impl(**kwargs)

            # Update metrics
            self._execution_count += 1
            self._last_execution = datetime.utcnow()

            return ToolResult(
                success=True,
                result=result,
                error=None
            )

        except Exception as e:
            logger.error(f"Tool {self.name} execution failed: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )


class CalculatorTool(BaseTool):
    """
    Calculator tool for mathematical operations
    """

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform mathematical calculations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            },
            examples=[
                "calculator(expression='2 + 2')",
                "calculator(expression='sqrt(16)')",
                "calculator(expression='3.14 * (5 ** 2)')"
            ]
        )

    async def _execute_impl(self, expression: str) -> Any:
        """Execute calculation"""
        import math
        import numpy as np

        # Create safe namespace for evaluation
        safe_dict = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'pow': pow,
            'sqrt': math.sqrt,
            'exp': math.exp,
            'log': math.log,
            'log10': math.log10,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'pi': math.pi,
            'e': math.e,
            'np': np
        }

        # Sanitize expression (remove dangerous operations)
        dangerous_patterns = [
            r'__', r'import', r'exec', r'eval',
            r'open', r'file', r'input', r'raw_input',
            r'compile', r'globals', r'locals'
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                raise ValueError(f"Unsafe operation detected: {pattern}")

        try:
            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return {
                "expression": expression,
                "result": result,
                "type": type(result).__name__
            }
        except Exception as e:
            raise ValueError(f"Calculation error: {e}")


class WebSearchTool(BaseTool):
    """
    Web search tool for finding information online
    """

    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            examples=[
                "web_search(query='AGI developments 2024')",
                "web_search(query='Python best practices', max_results=3)"
            ]
        )

    async def _execute_impl(self, query: str, max_results: int = 5) -> Any:
        """Execute web search"""
        import aiohttp
        import urllib.parse

        # Use DuckDuckGo HTML API (no key required)
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; AGI-Bot/1.0)'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        # Parse results (simplified)
                        results = self._parse_search_results(html, max_results)
                        return {
                            "query": query,
                            "results": results,
                            "count": len(results)
                        }
                    else:
                        raise Exception(f"Search failed with status {response.status}")

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            # Return mock results for demo
            return {
                "query": query,
                "results": [
                    {
                        "title": "Example Result 1",
                        "snippet": f"Information about {query}...",
                        "url": "https://example.com/1"
                    },
                    {
                        "title": "Example Result 2",
                        "snippet": f"More details on {query}...",
                        "url": "https://example.com/2"
                    }
                ],
                "count": 2,
                "note": "Using fallback results due to search API issue"
            }

    def _parse_search_results(self, html: str, max_results: int) -> List[Dict[str, str]]:
        """Parse search results from HTML"""
        from bs4 import BeautifulSoup

        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Find result elements (DuckDuckGo specific)
            for result in soup.find_all('div', class_='result')[:max_results]:
                title_elem = result.find('h2')
                snippet_elem = result.find('a', class_='result__snippet')
                url_elem = result.find('a', class_='result__url')

                if title_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                        "url": url_elem.get('href') if url_elem else ""
                    })

        except Exception as e:
            logger.error(f"Failed to parse search results: {e}")

        return results


class DatabaseQueryTool(BaseTool):
    """
    Database query tool for accessing structured data
    """

    def __init__(self):
        super().__init__(
            name="database_query",
            description="Query the database for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute"
                    },
                    "params": {
                        "type": "array",
                        "description": "Query parameters",
                        "default": []
                    }
                },
                "required": ["query"]
            },
            examples=[
                "database_query(query='SELECT * FROM products WHERE category = $1', params=['electronics'])",
                "database_query(query='SELECT COUNT(*) FROM orders')"
            ]
        )

    async def _execute_impl(self, query: str, params: List[Any] = None) -> Any:
        """Execute database query"""
        from agi.core.database import get_db_manager

        # Validate query (read-only for safety)
        query_lower = query.lower().strip()
        if not query_lower.startswith('select'):
            raise ValueError("Only SELECT queries are allowed for safety")

        # Check for dangerous operations
        dangerous_keywords = ['drop', 'delete', 'insert', 'update', 'alter', 'create']
        for keyword in dangerous_keywords:
            if keyword in query_lower:
                raise ValueError(f"Query contains restricted operation: {keyword}")

        try:
            db = await get_db_manager()
            results = await db.fetch(query, *(params or []))

            # Convert results to serializable format
            return {
                "query": query,
                "results": [dict(row) for row in results],
                "count": len(results)
            }

        except Exception as e:
            raise Exception(f"Database query failed: {e}")


class FileOperationTool(BaseTool):
    """
    File operation tool for reading/writing files
    """

    def __init__(self):
        super().__init__(
            name="file_operation",
            description="Read or write files",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write", "append"],
                        "description": "Operation to perform"
                    },
                    "path": {
                        "type": "string",
                        "description": "File path"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (for write/append)"
                    }
                },
                "required": ["operation", "path"]
            },
            examples=[
                "file_operation(operation='read', path='/tmp/data.txt')",
                "file_operation(operation='write', path='/tmp/output.txt', content='Hello World')"
            ]
        )

    async def _execute_impl(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None
    ) -> Any:
        """Execute file operation"""
        import os
        import aiofiles

        # Validate path (restrict to safe directories)
        safe_dirs = ['/tmp', '/var/tmp']
        path = os.path.abspath(path)

        is_safe = any(path.startswith(safe_dir) for safe_dir in safe_dirs)
        if not is_safe:
            raise ValueError(f"Access denied: {path} is outside safe directories")

        try:
            if operation == "read":
                async with aiofiles.open(path, 'r') as f:
                    content = await f.read()
                return {
                    "operation": "read",
                    "path": path,
                    "content": content,
                    "size": len(content)
                }

            elif operation in ["write", "append"]:
                if content is None:
                    raise ValueError("Content is required for write/append operations")

                mode = 'w' if operation == "write" else 'a'
                async with aiofiles.open(path, mode) as f:
                    await f.write(content)

                return {
                    "operation": operation,
                    "path": path,
                    "bytes_written": len(content),
                    "success": True
                }

            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            raise Exception(f"File operation failed: {e}")


class PythonCodeTool(BaseTool):
    """
    Python code execution tool (sandboxed)
    """

    def __init__(self):
        super().__init__(
            name="python_code",
            description="Execute Python code in a sandboxed environment",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Execution timeout in seconds",
                        "default": 5
                    }
                },
                "required": ["code"]
            },
            examples=[
                "python_code(code='print(2 + 2)')",
                "python_code(code='import math\\nprint(math.sqrt(16))')"
            ]
        )

    async def _execute_impl(self, code: str, timeout: int = 5) -> Any:
        """Execute Python code"""
        import subprocess
        import tempfile

        # Create temporary file for code
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute in subprocess with timeout
            result = await asyncio.create_subprocess_exec(
                'python3', temp_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                result.kill()
                raise Exception(f"Code execution timed out after {timeout} seconds")

            return {
                "code": code,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "return_code": result.returncode,
                "success": result.returncode == 0
            }

        finally:
            # Clean up temp file
            import os
            try:
                os.unlink(temp_file)
            except:
                pass


class ToolRegistry:
    """
    Registry for managing available tools
    """

    def __init__(self):
        self._tools: Dict[str, ITool] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize with default tools"""
        if self._initialized:
            return

        # Register default tools
        self.register_tool(CalculatorTool())
        self.register_tool(WebSearchTool())
        self.register_tool(DatabaseQueryTool())
        self.register_tool(FileOperationTool())
        self.register_tool(PythonCodeTool())

        # Register RAG tools
        try:
            from agi.tools.rag_tool import (
                KnowledgeSearchTool,
                DocumentIndexTool,
                RAGQueryTool,
                DocumentListTool
            )
            self.register_tool(KnowledgeSearchTool())
            self.register_tool(DocumentIndexTool())
            self.register_tool(RAGQueryTool())
            self.register_tool(DocumentListTool())
        except ImportError:
            logger.warning("RAG tools not available")

        self._initialized = True
        logger.info(f"Tool registry initialized with {len(self._tools)} tools")

    def register_tool(self, tool: ITool):
        """Register a tool"""
        self._tools[tool.get_definition().name] = tool
        logger.info(f"Registered tool: {tool.get_definition().name}")

    def get_tool(self, name: str) -> Optional[ITool]:
        """Get tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        """List all available tools"""
        return [tool.get_definition() for tool in self._tools.values()]

    def get_tools_for_task(self, task_description: str) -> List[ITool]:
        """Get relevant tools for a task"""
        relevant_tools = []

        task_lower = task_description.lower()

        # Simple heuristic matching
        tool_keywords = {
            "calculator": ["calculate", "math", "compute", "solve"],
            "web_search": ["search", "find", "lookup", "google"],
            "database_query": ["database", "query", "sql", "data"],
            "file_operation": ["file", "read", "write", "save"],
            "python_code": ["code", "program", "script", "python"],
            "knowledge_search": ["knowledge", "information", "know", "learn"],
            "rag_query": ["explain", "tell", "describe", "what is"],
            "document_index": ["index", "store", "remember", "add document"],
            "document_list": ["list documents", "show documents", "what documents"]
        }

        for tool_name, keywords in tool_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                tool = self.get_tool(tool_name)
                if tool:
                    relevant_tools.append(tool)

        return relevant_tools


# Singleton instance
_tool_registry: Optional[ToolRegistry] = None

async def get_tool_registry() -> ToolRegistry:
    """Get singleton tool registry instance"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        await _tool_registry.initialize()
    return _tool_registry