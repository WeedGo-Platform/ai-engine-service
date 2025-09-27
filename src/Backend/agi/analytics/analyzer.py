"""
Conversation Analyzer for AGI
Analyzes conversation patterns, sentiment, and quality
"""

import re
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import statistics

from agi.core.database import get_db_manager
from agi.config.agi_config import get_config
from agi.analytics.metrics import MetricType, get_metrics_collector

logger = logging.getLogger(__name__)


class ConversationType(Enum):
    """Types of conversations"""
    QUESTION_ANSWER = "question_answer"
    TASK_COMPLETION = "task_completion"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    TROUBLESHOOTING = "troubleshooting"
    LEARNING = "learning"
    CASUAL = "casual"
    UNKNOWN = "unknown"


class Sentiment(Enum):
    """Sentiment categories"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class ComplexityLevel(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class AnalysisResult:
    """Result of conversation analysis"""
    session_id: str
    conversation_type: ConversationType
    sentiment: Sentiment
    complexity: ComplexityLevel
    topic_keywords: List[str]
    intent: str
    success_indicators: Dict[str, bool]
    quality_score: float
    issues_detected: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]


@dataclass
class ConversationPattern:
    """Pattern detected in conversations"""
    pattern_type: str
    frequency: int
    examples: List[str]
    impact: str
    recommendation: str


class ConversationAnalyzer:
    """
    Analyzes conversations for patterns, quality, and insights
    """

    def __init__(self):
        """Initialize conversation analyzer"""
        self.config = get_config()
        self.db_manager = None
        self.metrics_collector = None
        
        # Analysis patterns
        self._question_patterns = [
            r'what\s+(is|are)\s+',
            r'how\s+(do|does|to)\s+',
            r'why\s+(is|are|do|does)\s+',
            r'when\s+(will|should|do|does)\s+',
            r'where\s+(is|are|can)\s+',
            r'can\s+you\s+',
            r'could\s+you\s+',
            r'\?$'
        ]
        
        self._task_patterns = [
            r'please\s+',
            r'i\s+need\s+',
            r'create\s+',
            r'generate\s+',
            r'build\s+',
            r'implement\s+',
            r'fix\s+',
            r'solve\s+'
        ]
        
        self._sentiment_words = {
            'positive': ['great', 'excellent', 'good', 'thanks', 'perfect', 'awesome', 'helpful'],
            'negative': ['bad', 'wrong', 'error', 'fail', 'issue', 'problem', 'terrible', 'awful']
        }

    async def initialize(self):
        """Initialize the analyzer"""
        self.db_manager = await get_db_manager()
        self.metrics_collector = await get_metrics_collector()
        logger.info("Conversation analyzer initialized")

    async def analyze_conversation(
        self,
        session_id: str,
        messages: List[Dict[str, Any]]
    ) -> AnalysisResult:
        """
        Analyze a conversation
        
        Args:
            session_id: Session identifier
            messages: List of conversation messages
            
        Returns:
            Analysis result
        """
        if not messages:
            return self._empty_result(session_id)
        
        # Extract text content
        user_messages = [m['content'] for m in messages if m.get('role') == 'user']
        assistant_messages = [m['content'] for m in messages if m.get('role') == 'assistant']
        
        # Determine conversation type
        conversation_type = self._classify_conversation(user_messages)
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(messages)
        
        # Assess complexity
        complexity = self._assess_complexity(user_messages, assistant_messages)
        
        # Extract keywords and intent
        keywords = self._extract_keywords(user_messages)
        intent = self._extract_intent(user_messages)
        
        # Check success indicators
        success_indicators = self._check_success_indicators(messages)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            messages, sentiment, success_indicators
        )
        
        # Detect issues
        issues = self._detect_issues(messages, success_indicators)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            conversation_type, issues, quality_score
        )
        
        # Compile metadata
        metadata = {
            'message_count': len(messages),
            'user_message_count': len(user_messages),
            'assistant_message_count': len(assistant_messages),
            'avg_message_length': statistics.mean(
                [len(m['content']) for m in messages]
            ) if messages else 0,
            'conversation_duration': self._calculate_duration(messages)
        }
        
        result = AnalysisResult(
            session_id=session_id,
            conversation_type=conversation_type,
            sentiment=sentiment,
            complexity=complexity,
            topic_keywords=keywords,
            intent=intent,
            success_indicators=success_indicators,
            quality_score=quality_score,
            issues_detected=issues,
            suggestions=suggestions,
            metadata=metadata
        )
        
        # Record metrics
        await self._record_analysis_metrics(result)
        
        return result

    def _classify_conversation(self, user_messages: List[str]) -> ConversationType:
        """Classify the type of conversation"""
        if not user_messages:
            return ConversationType.UNKNOWN
        
        combined_text = ' '.join(user_messages).lower()
        
        # Check for questions
        question_count = sum(
            1 for pattern in self._question_patterns
            if re.search(pattern, combined_text)
        )
        
        # Check for tasks
        task_count = sum(
            1 for pattern in self._task_patterns
            if re.search(pattern, combined_text)
        )
        
        # Check for specific keywords
        if any(word in combined_text for word in ['analyze', 'compare', 'evaluate']):
            return ConversationType.ANALYSIS
        elif any(word in combined_text for word in ['create', 'write', 'generate', 'compose']):
            return ConversationType.CREATIVE
        elif any(word in combined_text for word in ['error', 'bug', 'fix', 'issue', 'problem']):
            return ConversationType.TROUBLESHOOTING
        elif any(word in combined_text for word in ['learn', 'teach', 'explain', 'understand']):
            return ConversationType.LEARNING
        elif task_count > question_count:
            return ConversationType.TASK_COMPLETION
        elif question_count > 0:
            return ConversationType.QUESTION_ANSWER
        else:
            return ConversationType.CASUAL

    def _analyze_sentiment(self, messages: List[Dict[str, Any]]) -> Sentiment:
        """Analyze overall sentiment of conversation"""
        if not messages:
            return Sentiment.NEUTRAL
        
        sentiment_scores = []
        
        for message in messages:
            if message.get('role') == 'user':
                content = message['content'].lower()
                
                positive_score = sum(
                    1 for word in self._sentiment_words['positive']
                    if word in content
                )
                negative_score = sum(
                    1 for word in self._sentiment_words['negative']
                    if word in content
                )
                
                # Check for strong indicators
                if '!' in content:
                    if positive_score > 0:
                        positive_score += 0.5
                    if negative_score > 0:
                        negative_score += 0.5
                
                sentiment_scores.append(positive_score - negative_score)
        
        if not sentiment_scores:
            return Sentiment.NEUTRAL
        
        avg_sentiment = statistics.mean(sentiment_scores)
        
        if avg_sentiment >= 2:
            return Sentiment.VERY_POSITIVE
        elif avg_sentiment >= 0.5:
            return Sentiment.POSITIVE
        elif avg_sentiment <= -2:
            return Sentiment.VERY_NEGATIVE
        elif avg_sentiment <= -0.5:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL

    def _assess_complexity(self, user_messages: List[str], assistant_messages: List[str]) -> ComplexityLevel:
        """Assess conversation complexity"""
        if not user_messages:
            return ComplexityLevel.SIMPLE
        
        # Factors for complexity
        factors = {
            'message_length': statistics.mean([len(m) for m in user_messages]) if user_messages else 0,
            'response_length': statistics.mean([len(m) for m in assistant_messages]) if assistant_messages else 0,
            'technical_terms': self._count_technical_terms(' '.join(user_messages)),
            'multi_step': any(word in ' '.join(user_messages).lower() 
                            for word in ['step', 'steps', 'first', 'then', 'finally']),
            'code_present': '```' in ' '.join(assistant_messages) if assistant_messages else False
        }
        
        complexity_score = 0
        
        # Score based on message length
        if factors['message_length'] > 500:
            complexity_score += 2
        elif factors['message_length'] > 200:
            complexity_score += 1
        
        # Score based on response length
        if factors['response_length'] > 1000:
            complexity_score += 2
        elif factors['response_length'] > 500:
            complexity_score += 1
        
        # Technical content
        if factors['technical_terms'] > 5:
            complexity_score += 2
        elif factors['technical_terms'] > 2:
            complexity_score += 1
        
        # Multi-step tasks
        if factors['multi_step']:
            complexity_score += 1
        
        # Code generation
        if factors['code_present']:
            complexity_score += 1
        
        # Map to complexity level
        if complexity_score >= 6:
            return ComplexityLevel.VERY_COMPLEX
        elif complexity_score >= 4:
            return ComplexityLevel.COMPLEX
        elif complexity_score >= 2:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.SIMPLE

    def _count_technical_terms(self, text: str) -> int:
        """Count technical terms in text"""
        technical_terms = [
            'api', 'database', 'function', 'algorithm', 'variable',
            'class', 'method', 'parameter', 'array', 'object',
            'server', 'client', 'request', 'response', 'protocol',
            'authentication', 'encryption', 'deployment', 'architecture'
        ]
        
        text_lower = text.lower()
        return sum(1 for term in technical_terms if term in text_lower)

    def _extract_keywords(self, messages: List[str]) -> List[str]:
        """Extract key topic words from messages"""
        if not messages:
            return []
        
        combined_text = ' '.join(messages).lower()
        
        # Remove common words
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
            'in', 'with', 'to', 'for', 'of', 'as', 'from', 'by', 'that', 'this',
            'it', 'can', 'be', 'are', 'was', 'were', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]+\b', combined_text)
        
        # Count frequencies
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:10]]

    def _extract_intent(self, messages: List[str]) -> str:
        """Extract primary intent from messages"""
        if not messages:
            return "unknown"
        
        first_message = messages[0].lower()
        
        # Common intent patterns
        intents = {
            'information_seeking': ['what', 'how', 'why', 'when', 'where', 'explain'],
            'task_execution': ['create', 'build', 'generate', 'make', 'implement'],
            'problem_solving': ['fix', 'solve', 'debug', 'error', 'issue'],
            'learning': ['teach', 'learn', 'understand', 'tutorial'],
            'analysis': ['analyze', 'compare', 'evaluate', 'assess'],
            'assistance': ['help', 'assist', 'support', 'guide']
        }
        
        for intent, keywords in intents.items():
            if any(keyword in first_message for keyword in keywords):
                return intent
        
        return "general_conversation"

    def _check_success_indicators(self, messages: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Check for success indicators in conversation"""
        indicators = {
            'task_completed': False,
            'question_answered': False,
            'no_errors': True,
            'user_satisfied': False,
            'follow_up_handled': False
        }
        
        if not messages:
            return indicators
        
        # Check last messages for completion
        if len(messages) >= 2:
            last_user = None
            last_assistant = None
            
            for msg in reversed(messages):
                if msg.get('role') == 'user' and not last_user:
                    last_user = msg['content'].lower()
                elif msg.get('role') == 'assistant' and not last_assistant:
                    last_assistant = msg['content'].lower()
                
                if last_user and last_assistant:
                    break
            
            # Check for satisfaction indicators
            if last_user:
                satisfaction_words = ['thanks', 'thank you', 'perfect', 'great', 'excellent', 'works']
                indicators['user_satisfied'] = any(word in last_user for word in satisfaction_words)
            
            # Check for errors
            error_words = ['error', 'fail', 'exception', 'not working', 'broken']
            for msg in messages:
                if any(word in msg['content'].lower() for word in error_words):
                    indicators['no_errors'] = False
                    break
            
            # Check if questions were answered
            question_count = sum(1 for msg in messages if msg.get('role') == 'user' and '?' in msg['content'])
            answer_count = sum(1 for msg in messages if msg.get('role') == 'assistant')
            if question_count > 0 and answer_count >= question_count:
                indicators['question_answered'] = True
            
            # Check for task completion
            if 'done' in last_assistant or 'completed' in last_assistant or 'finished' in last_assistant:
                indicators['task_completed'] = True
        
        return indicators

    def _calculate_quality_score(self, messages: List[Dict[str, Any]], 
                                sentiment: Sentiment, 
                                success_indicators: Dict[str, bool]) -> float:
        """Calculate conversation quality score (0-1)"""
        score = 0.5  # Base score
        
        # Sentiment contribution
        sentiment_scores = {
            Sentiment.VERY_POSITIVE: 0.2,
            Sentiment.POSITIVE: 0.1,
            Sentiment.NEUTRAL: 0,
            Sentiment.NEGATIVE: -0.1,
            Sentiment.VERY_NEGATIVE: -0.2
        }
        score += sentiment_scores.get(sentiment, 0)
        
        # Success indicators contribution
        for indicator, achieved in success_indicators.items():
            if achieved:
                if indicator == 'user_satisfied':
                    score += 0.2
                else:
                    score += 0.075
        
        # Message coherence
        if messages:
            # Check for back-and-forth pattern
            roles = [msg['role'] for msg in messages]
            expected_pattern = ['user', 'assistant'] * (len(roles) // 2)
            if roles[:len(expected_pattern)] == expected_pattern[:len(roles)]:
                score += 0.1
        
        return max(0, min(1, score))

    def _detect_issues(self, messages: List[Dict[str, Any]], 
                      success_indicators: Dict[str, bool]) -> List[str]:
        """Detect potential issues in conversation"""
        issues = []
        
        # Check for errors
        if not success_indicators['no_errors']:
            issues.append("Errors or failures detected in conversation")
        
        # Check for repetition
        if self._has_repetition(messages):
            issues.append("Repetitive responses detected")
        
        # Check for unanswered questions
        if not success_indicators['question_answered']:
            issues.append("Some questions may not have been fully answered")
        
        # Check for confusion indicators
        confusion_words = ['confused', "don't understand", 'unclear', 'what do you mean']
        for msg in messages:
            if msg.get('role') == 'user':
                if any(word in msg['content'].lower() for word in confusion_words):
                    issues.append("User confusion detected")
                    break
        
        # Check for conversation length
        if len(messages) > 20:
            issues.append("Long conversation - may indicate difficulty resolving issue")
        
        return issues

    def _has_repetition(self, messages: List[Dict[str, Any]]) -> bool:
        """Check for repetitive patterns in messages"""
        if len(messages) < 4:
            return False
        
        assistant_messages = [m['content'] for m in messages if m.get('role') == 'assistant']
        
        if len(assistant_messages) < 2:
            return False
        
        # Check for very similar consecutive messages
        for i in range(len(assistant_messages) - 1):
            similarity = self._calculate_similarity(
                assistant_messages[i], 
                assistant_messages[i + 1]
            )
            if similarity > 0.8:
                return True
        
        return False

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (0-1)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

    def _generate_suggestions(self, conversation_type: ConversationType,
                             issues: List[str], 
                             quality_score: float) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Quality-based suggestions
        if quality_score < 0.5:
            suggestions.append("Consider providing more detailed responses")
            suggestions.append("Ensure questions are fully addressed")
        
        # Issue-based suggestions
        if "Errors or failures detected" in issues:
            suggestions.append("Implement better error handling and recovery")
        
        if "User confusion detected" in issues:
            suggestions.append("Provide clearer explanations and examples")
        
        if "Repetitive responses detected" in issues:
            suggestions.append("Vary response patterns and provide more context")
        
        # Type-specific suggestions
        if conversation_type == ConversationType.TROUBLESHOOTING:
            suggestions.append("Consider systematic debugging approaches")
        elif conversation_type == ConversationType.LEARNING:
            suggestions.append("Break down complex concepts into smaller parts")
        elif conversation_type == ConversationType.CREATIVE:
            suggestions.append("Offer multiple creative alternatives")
        
        return suggestions[:3]  # Limit to top 3 suggestions

    def _calculate_duration(self, messages: List[Dict[str, Any]]) -> float:
        """Calculate conversation duration in seconds"""
        if not messages or len(messages) < 2:
            return 0
        
        # If messages have timestamps
        timestamps = []
        for msg in messages:
            if 'timestamp' in msg:
                timestamps.append(msg['timestamp'])
        
        if len(timestamps) >= 2:
            # Convert to datetime if needed and calculate difference
            try:
                start = timestamps[0]
                end = timestamps[-1]
                if isinstance(start, str):
                    start = datetime.fromisoformat(start)
                if isinstance(end, str):
                    end = datetime.fromisoformat(end)
                return (end - start).total_seconds()
            except:
                pass
        
        # Estimate based on message count (30 seconds per exchange)
        return len(messages) * 15

    def _empty_result(self, session_id: str) -> AnalysisResult:
        """Return empty analysis result"""
        return AnalysisResult(
            session_id=session_id,
            conversation_type=ConversationType.UNKNOWN,
            sentiment=Sentiment.NEUTRAL,
            complexity=ComplexityLevel.SIMPLE,
            topic_keywords=[],
            intent="unknown",
            success_indicators={},
            quality_score=0,
            issues_detected=["No messages to analyze"],
            suggestions=[],
            metadata={}
        )

    async def _record_analysis_metrics(self, result: AnalysisResult):
        """Record analysis metrics"""
        if self.metrics_collector:
            # Record quality score
            await self.metrics_collector.record(
                MetricType.CUSTOM,
                result.quality_score,
                session_id=result.session_id,
                metadata={'metric_name': 'conversation_quality'}
            )
            
            # Record complexity
            complexity_values = {
                ComplexityLevel.SIMPLE: 1,
                ComplexityLevel.MODERATE: 2,
                ComplexityLevel.COMPLEX: 3,
                ComplexityLevel.VERY_COMPLEX: 4
            }
            await self.metrics_collector.record(
                MetricType.CUSTOM,
                complexity_values.get(result.complexity, 1),
                session_id=result.session_id,
                metadata={'metric_name': 'conversation_complexity'}
            )

    async def find_patterns(
        self,
        time_window_hours: int = 24
    ) -> List[ConversationPattern]:
        """Find patterns across conversations"""
        # This would analyze multiple conversations to find patterns
        # For now, return example patterns
        patterns = [
            ConversationPattern(
                pattern_type="frequent_errors",
                frequency=0,
                examples=[],
                impact="May indicate system issues",
                recommendation="Review error handling and logging"
            )
        ]
        
        return patterns


# Singleton instance
_conversation_analyzer: Optional[ConversationAnalyzer] = None

async def get_conversation_analyzer() -> ConversationAnalyzer:
    """Get singleton conversation analyzer instance"""
    global _conversation_analyzer
    if _conversation_analyzer is None:
        _conversation_analyzer = ConversationAnalyzer()
        await _conversation_analyzer.initialize()
    return _conversation_analyzer