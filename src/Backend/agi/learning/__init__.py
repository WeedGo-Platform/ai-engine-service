"""AGI Learning Module"""

from .feedback_collector import (
    FeedbackCollector,
    FeedbackType,
    FeedbackSentiment,
    Feedback,
    FeedbackAnalysis,
    get_feedback_collector
)

from .pattern_recognition import (
    PatternRecognitionEngine,
    PatternType,
    Pattern,
    PatternMatch,
    get_pattern_engine
)

from .learning_adapter import (
    LearningAdapter,
    AdaptationType,
    Adaptation,
    LearningInsight,
    get_learning_adapter
)

__all__ = [
    # Feedback Collector
    'FeedbackCollector',
    'FeedbackType',
    'FeedbackSentiment',
    'Feedback',
    'FeedbackAnalysis',
    'get_feedback_collector',

    # Pattern Recognition
    'PatternRecognitionEngine',
    'PatternType',
    'Pattern',
    'PatternMatch',
    'get_pattern_engine',

    # Learning Adapter
    'LearningAdapter',
    'AdaptationType',
    'Adaptation',
    'LearningInsight',
    'get_learning_adapter'
]