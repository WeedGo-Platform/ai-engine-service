"""
Specialized Code Agent
Expert in software development, debugging, and code generation
"""

import ast
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import subprocess
import tempfile
import os

from agi.core.interfaces import IAgent, ConversationContext, ToolResult
from agi.tools import get_tool_registry
from agi.models.registry import get_model_registry

logger = logging.getLogger(__name__)


@dataclass
class CodeAnalysis:
    """Code analysis results"""
    language: str
    complexity: int
    issues: List[str]
    suggestions: List[str]
    dependencies: List[str]
    test_coverage: Optional[float] = None


class CodeAgent(IAgent):
    """
    Specialized agent for code-related tasks
    Capabilities: code generation, debugging, refactoring, testing
    """

    def __init__(self):
        super().__init__()
        self.agent_id = "code_specialist"
        self.name = "Code Specialist Agent"
        self.description = "Expert in software development and code analysis"
        self.capabilities = [
            "code_generation",
            "debugging",
            "refactoring",
            "testing",
            "documentation",
            "optimization",
            "security_analysis"
        ]
        self.supported_languages = [
            "python", "javascript", "typescript", "java",
            "c++", "go", "rust", "ruby", "swift", "kotlin"
        ]
        self.code_patterns = self._load_code_patterns()

    def _load_code_patterns(self) -> Dict[str, Any]:
        """Load common code patterns and best practices"""
        return {
            "design_patterns": {
                "singleton": "Ensures a class has only one instance",
                "factory": "Creates objects without specifying exact class",
                "observer": "Defines one-to-many dependency between objects",
                "strategy": "Defines family of algorithms and makes them interchangeable"
            },
            "best_practices": {
                "DRY": "Don't Repeat Yourself",
                "SOLID": "Single responsibility, Open/closed, Liskov substitution, Interface segregation, Dependency inversion",
                "KISS": "Keep It Simple, Stupid",
                "YAGNI": "You Aren't Gonna Need It"
            },
            "security": {
                "input_validation": "Always validate and sanitize user input",
                "sql_injection": "Use parameterized queries",
                "xss": "Escape output in web applications",
                "authentication": "Use secure authentication methods"
            }
        }

    async def process(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Process code-related request"""
        # Analyze request type
        request_type = self._classify_request(request)

        logger.info(f"CodeAgent processing {request_type} request")

        if request_type == "generate":
            return await self._generate_code(request, context)
        elif request_type == "debug":
            return await self._debug_code(request, context)
        elif request_type == "refactor":
            return await self._refactor_code(request, context)
        elif request_type == "test":
            return await self._generate_tests(request, context)
        elif request_type == "analyze":
            return await self._analyze_code(request, context)
        elif request_type == "document":
            return await self._generate_documentation(request, context)
        elif request_type == "optimize":
            return await self._optimize_code(request, context)
        else:
            return await self._general_code_help(request, context)

    def _classify_request(self, request: str) -> str:
        """Classify the type of code request"""
        request_lower = request.lower()

        keywords = {
            "generate": ["create", "write", "implement", "build", "generate"],
            "debug": ["debug", "fix", "error", "bug", "issue", "problem"],
            "refactor": ["refactor", "improve", "clean", "restructure"],
            "test": ["test", "testing", "unit test", "integration test"],
            "analyze": ["analyze", "review", "check", "audit"],
            "document": ["document", "docs", "comment", "explain"],
            "optimize": ["optimize", "performance", "speed up", "efficiency"]
        }

        for request_type, words in keywords.items():
            if any(word in request_lower for word in words):
                return request_type

        return "general"

    async def _generate_code(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Generate code based on requirements"""
        # Extract language and requirements
        language = self._extract_language(request)
        requirements = self._extract_requirements(request)

        # Get appropriate model for code generation
        registry = await get_model_registry()
        model = await registry.get_model("deepseek_coder_6_7b_instruct_q4_k_m")

        if not model:
            # Fallback to default model
            model = await registry.get_model(registry.config.models.default_model)

        # Create code generation prompt
        prompt = f"""
        Generate {language} code for the following requirements:
        {request}

        Requirements:
        {chr(10).join(f'- {req}' for req in requirements)}

        Follow best practices and include:
        - Error handling
        - Type hints/annotations (if applicable)
        - Comments for complex logic
        - Efficient algorithms

        Code:
        """

        response = await model.generate(prompt, context)

        # Extract and format code
        code = self._extract_code_blocks(response)

        if code:
            # Validate syntax if Python
            if language == "python":
                validation = self._validate_python_syntax(code[0])
                if validation:
                    return f"Generated {language} code:\n\n```{language}\n{code[0]}\n```\n\nNote: {validation}"

            return f"Generated {language} code:\n\n```{language}\n{code[0]}\n```"

        return response

    async def _debug_code(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Debug code and identify issues"""
        # Extract code from request
        code_blocks = self._extract_code_blocks(request)

        if not code_blocks:
            return "Please provide the code you want to debug."

        code = code_blocks[0]
        language = self._detect_language(code)

        issues = []
        suggestions = []

        # Language-specific debugging
        if language == "python":
            syntax_error = self._validate_python_syntax(code)
            if syntax_error:
                issues.append(f"Syntax Error: {syntax_error}")
                suggestions.append("Fix the syntax error first")

            # Check for common issues
            common_issues = self._check_common_python_issues(code)
            issues.extend(common_issues)

        # Use model for deeper analysis
        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        debug_prompt = f"""
        Debug the following {language} code and identify issues:

        ```{language}
        {code}
        ```

        Identify:
        1. Syntax errors
        2. Logic errors
        3. Performance issues
        4. Security vulnerabilities
        5. Best practice violations

        Provide fixes for each issue found.
        """

        analysis = await model.generate(debug_prompt, context)

        return f"""
## Debug Analysis

### Detected Issues:
{chr(10).join(f'- {issue}' for issue in issues)}

### Suggestions:
{chr(10).join(f'- {suggestion}' for suggestion in suggestions)}

### Detailed Analysis:
{analysis}
"""

    async def _refactor_code(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Refactor code for better quality"""
        code_blocks = self._extract_code_blocks(request)

        if not code_blocks:
            return "Please provide the code you want to refactor."

        code = code_blocks[0]
        language = self._detect_language(code)

        # Apply refactoring patterns
        refactored = code

        if language == "python":
            refactored = self._apply_python_refactoring(code)

        # Use model for advanced refactoring
        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        refactor_prompt = f"""
        Refactor the following {language} code following SOLID principles and best practices:

        Original code:
        ```{language}
        {code}
        ```

        Apply these refactoring techniques:
        1. Extract methods/functions for repeated code
        2. Improve variable and function names
        3. Reduce complexity
        4. Apply appropriate design patterns
        5. Add proper error handling

        Refactored code:
        """

        response = await model.generate(refactor_prompt, context)

        return f"""
## Refactored Code

### Original:
```{language}
{code}
```

### Refactored:
{response}

### Applied Principles:
- DRY (Don't Repeat Yourself)
- SOLID principles
- Clean code practices
- Improved readability
"""

    async def _generate_tests(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Generate test cases for code"""
        code_blocks = self._extract_code_blocks(request)

        if not code_blocks:
            return "Please provide the code you want to test."

        code = code_blocks[0]
        language = self._detect_language(code)

        # Generate test framework based on language
        test_framework = self._get_test_framework(language)

        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        test_prompt = f"""
        Generate comprehensive unit tests for the following {language} code:

        ```{language}
        {code}
        ```

        Use {test_framework} framework and include:
        1. Happy path tests
        2. Edge case tests
        3. Error handling tests
        4. Boundary value tests
        5. Mock external dependencies

        Test code:
        """

        tests = await model.generate(test_prompt, context)

        return f"""
## Generated Tests

### Test Framework: {test_framework}

### Test Cases:
{tests}

### Coverage Areas:
- Functionality testing
- Edge cases
- Error handling
- Performance
- Security
"""

    async def _analyze_code(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Analyze code quality and metrics"""
        code_blocks = self._extract_code_blocks(request)

        if not code_blocks:
            return "Please provide the code to analyze."

        code = code_blocks[0]
        language = self._detect_language(code)

        # Calculate metrics
        metrics = self._calculate_code_metrics(code)

        # Security analysis
        security_issues = self._check_security_issues(code)

        # Performance analysis
        performance_issues = self._check_performance_issues(code)

        return f"""
## Code Analysis Report

### Language: {language}

### Metrics:
- Lines of Code: {metrics['loc']}
- Cyclomatic Complexity: {metrics['complexity']}
- Functions/Methods: {metrics['functions']}
- Classes: {metrics['classes']}

### Security Issues:
{chr(10).join(f'- {issue}' for issue in security_issues) if security_issues else '- No security issues detected'}

### Performance Issues:
{chr(10).join(f'- {issue}' for issue in performance_issues) if performance_issues else '- No performance issues detected'}

### Code Quality:
- Readability: {metrics['readability']}/10
- Maintainability: {metrics['maintainability']}/10
- Testability: {metrics['testability']}/10

### Recommendations:
{chr(10).join(f'- {rec}' for rec in metrics['recommendations'])}
"""

    async def _generate_documentation(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Generate documentation for code"""
        code_blocks = self._extract_code_blocks(request)

        if not code_blocks:
            return "Please provide the code to document."

        code = code_blocks[0]
        language = self._detect_language(code)

        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        doc_prompt = f"""
        Generate comprehensive documentation for the following {language} code:

        ```{language}
        {code}
        ```

        Include:
        1. Overview/Purpose
        2. Function/Method descriptions
        3. Parameter documentation
        4. Return value documentation
        5. Usage examples
        6. Error handling notes

        Documentation:
        """

        documentation = await model.generate(doc_prompt, context)

        return f"""
## Code Documentation

### Language: {language}

{documentation}

### Documentation Standards:
- Clear descriptions
- Parameter types and descriptions
- Return value documentation
- Usage examples
- Error handling information
"""

    async def _optimize_code(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Optimize code for performance"""
        code_blocks = self._extract_code_blocks(request)

        if not code_blocks:
            return "Please provide the code to optimize."

        code = code_blocks[0]
        language = self._detect_language(code)

        # Analyze current performance
        performance = self._analyze_performance(code)

        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        optimize_prompt = f"""
        Optimize the following {language} code for better performance:

        ```{language}
        {code}
        ```

        Apply these optimizations:
        1. Algorithm improvements
        2. Data structure optimizations
        3. Memory usage reduction
        4. Cache utilization
        5. Parallel processing (if applicable)

        Optimized code:
        """

        optimized = await model.generate(optimize_prompt, context)

        return f"""
## Code Optimization

### Original Performance:
- Time Complexity: {performance['time_complexity']}
- Space Complexity: {performance['space_complexity']}

### Optimized Code:
{optimized}

### Improvements:
- Reduced time complexity
- Better memory usage
- Improved cache locality
- Parallelization opportunities

### Performance Gains:
- Estimated speedup: 2-5x (depends on input size)
- Memory reduction: ~30%
"""

    async def _general_code_help(
        self,
        request: str,
        context: ConversationContext
    ) -> str:
        """Provide general code help"""
        registry = await get_model_registry()
        model = await registry.get_model(registry.config.models.default_model)

        help_prompt = f"""
        As a code expert, help with the following request:
        {request}

        Provide:
        1. Clear explanation
        2. Code examples if relevant
        3. Best practices
        4. Common pitfalls to avoid
        """

        return await model.generate(help_prompt, context)

    def _extract_language(self, text: str) -> str:
        """Extract programming language from text"""
        text_lower = text.lower()

        for lang in self.supported_languages:
            if lang in text_lower:
                return lang

        return "python"  # Default

    def _extract_requirements(self, text: str) -> List[str]:
        """Extract requirements from request"""
        requirements = []

        # Look for bullet points or numbered lists
        lines = text.split('\n')
        for line in lines:
            if re.match(r'^[-*•]\s+', line) or re.match(r'^\d+\.\s+', line):
                requirements.append(line.strip('- *•0123456789.').strip())

        # If no explicit requirements, extract key phrases
        if not requirements:
            # Simple extraction of key phrases
            if "must" in text:
                requirements.append(text.split("must")[1].split('.')[0].strip())
            if "should" in text:
                requirements.append(text.split("should")[1].split('.')[0].strip())

        return requirements if requirements else ["Implement requested functionality"]

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks from text"""
        # Look for markdown code blocks
        pattern = r'```[\w]*\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            return matches

        # Look for indented code
        lines = text.split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            if line.startswith('    ') or line.startswith('\t'):
                code_lines.append(line[4:] if line.startswith('    ') else line[1:])
                in_code = True
            elif in_code and line.strip() == '':
                code_lines.append('')
            elif in_code:
                break

        if code_lines:
            return ['\n'.join(code_lines)]

        return []

    def _detect_language(self, code: str) -> str:
        """Detect programming language from code"""
        # Simple heuristics
        if 'def ' in code and ':' in code:
            return 'python'
        elif 'function' in code or 'const ' in code or 'let ' in code:
            return 'javascript'
        elif 'public class' in code or 'public static void' in code:
            return 'java'
        elif '#include' in code:
            return 'c++'
        elif 'func ' in code and 'go' in code.lower():
            return 'go'
        elif 'fn ' in code and '->' in code:
            return 'rust'

        return 'python'  # Default

    def _validate_python_syntax(self, code: str) -> Optional[str]:
        """Validate Python syntax"""
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return f"Line {e.lineno}: {e.msg}"

    def _check_common_python_issues(self, code: str) -> List[str]:
        """Check for common Python issues"""
        issues = []

        # Check for common anti-patterns
        if 'except:' in code:
            issues.append("Bare except clause - specify exception type")

        if 'eval(' in code:
            issues.append("Use of eval() - potential security risk")

        if 'global ' in code:
            issues.append("Use of global variables - consider refactoring")

        # Check for missing imports
        if 're.' in code and 'import re' not in code:
            issues.append("Missing import: re module")

        return issues

    def _apply_python_refactoring(self, code: str) -> str:
        """Apply basic Python refactoring"""
        refactored = code

        # Replace print statements with logging
        refactored = re.sub(
            r'print\((.*?)\)',
            r'logger.info(\1)',
            refactored
        )

        # Add type hints for simple cases
        refactored = re.sub(
            r'def (\w+)\((\w+)\):',
            r'def \1(\2: Any) -> Any:',
            refactored
        )

        return refactored

    def _get_test_framework(self, language: str) -> str:
        """Get appropriate test framework for language"""
        frameworks = {
            'python': 'pytest',
            'javascript': 'jest',
            'typescript': 'jest',
            'java': 'JUnit',
            'c++': 'Google Test',
            'go': 'testing package',
            'rust': 'cargo test',
            'ruby': 'RSpec',
            'swift': 'XCTest',
            'kotlin': 'JUnit'
        }
        return frameworks.get(language, 'unit test')

    def _calculate_code_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate code metrics"""
        lines = code.split('\n')

        return {
            'loc': len(lines),
            'complexity': min(10, len([l for l in lines if 'if ' in l or 'for ' in l or 'while ' in l]) + 1),
            'functions': len([l for l in lines if 'def ' in l or 'function ' in l]),
            'classes': len([l for l in lines if 'class ' in l]),
            'readability': 7,  # Simplified scoring
            'maintainability': 7,
            'testability': 8,
            'recommendations': [
                "Add more comments for complex logic",
                "Consider breaking down large functions",
                "Add type hints for better IDE support"
            ]
        }

    def _check_security_issues(self, code: str) -> List[str]:
        """Check for security vulnerabilities"""
        issues = []

        security_patterns = {
            r'eval\(': "Use of eval() - code injection risk",
            r'exec\(': "Use of exec() - code injection risk",
            r'os\.system': "Use of os.system() - command injection risk",
            r'subprocess\.call\([^,]*shell=True': "Shell=True in subprocess - command injection risk",
            r'pickle\.loads': "Pickle deserialization - arbitrary code execution risk",
            r'input\(': "Direct use of input() - validate user input",
            r'\.format\(.*request': "Potential format string vulnerability",
            r'password\s*=\s*["\']': "Hardcoded password detected"
        }

        for pattern, issue in security_patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(issue)

        return issues

    def _check_performance_issues(self, code: str) -> List[str]:
        """Check for performance issues"""
        issues = []

        performance_patterns = {
            r'for .+ in .+:\s*for .+ in .+:': "Nested loops - O(n²) complexity",
            r'\.append\(.+\) for': "List append in loop - consider list comprehension",
            r'\+= .+ for': "String concatenation in loop - use join()",
            r'time\.sleep': "Blocking sleep - consider async alternatives",
            r're\.compile.*for': "Regex compilation in loop - compile once",
            r'global ': "Global variable access - slower than local"
        }

        for pattern, issue in performance_patterns.items():
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                issues.append(issue)

        return issues

    def _analyze_performance(self, code: str) -> Dict[str, str]:
        """Analyze code performance characteristics"""
        # Simplified complexity analysis
        nested_loops = len(re.findall(r'for .+ in .+:\s*for .+ in .+:', code))

        time_complexity = "O(1)"
        if nested_loops >= 2:
            time_complexity = "O(n³)"
        elif nested_loops == 1:
            time_complexity = "O(n²)"
        elif 'for ' in code or 'while ' in code:
            time_complexity = "O(n)"

        space_complexity = "O(1)"
        if '= []' in code or '= {}' in code:
            space_complexity = "O(n)"

        return {
            'time_complexity': time_complexity,
            'space_complexity': space_complexity
        }

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "supported_languages": self.supported_languages,
            "status": "active"
        }