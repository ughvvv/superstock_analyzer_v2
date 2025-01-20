"""Qualitative analysis package.

This package provides tools for analyzing qualitative data such as earnings call
transcripts, news articles, and press releases. It includes specialized analyzers
for different types of content, text processing utilities, and prompt management.
"""

from .analyzers.base_analyzer import QualitativeAnalyzer, QualitativeMetrics, AnalysisResult
from .analyzers.earnings_analyzer import EarningsAnalyzer
from .analyzers.news_analyzer import NewsAnalyzer
from .processors.text_processor import TextProcessor

__all__ = [
    'QualitativeAnalyzer',
    'QualitativeMetrics',
    'AnalysisResult',
    'EarningsAnalyzer',
    'NewsAnalyzer',
    'TextProcessor'
]

# Version of the qualitative analysis package
__version__ = '2.0.0'

# Package metadata
__author__ = 'Blake Cole'
__description__ = 'Qualitative analysis tools for financial data'

# Configuration defaults
DEFAULT_CONFIG = {
    'model': {
        'name': 'gpt-4-1106-preview',
        'temperature': 0.7,
        'max_tokens': 4000,
        'top_p': 1.0,
        'frequency_penalty': 0.0,
        'presence_penalty': 0.0
    },
    'text_processing': {
        'max_segment_length': 2000,
        'max_key_phrases': 10,
        'context_window_size': 100
    },
    'analysis': {
        'min_text_length': 50,
        'confidence_threshold': 0.5,
        'cache_duration': 3600  # 1 hour in seconds
    }
}

# Sentiment classification settings
SENTIMENT_CONFIG = {
    'very_positive': {
        'score_range': (0.8, 1.0),
        'confidence_boost': 0.2
    },
    'positive': {
        'score_range': (0.3, 0.8),
        'confidence_boost': 0.1
    },
    'neutral': {
        'score_range': (-0.3, 0.3),
        'confidence_boost': 0.0
    },
    'negative': {
        'score_range': (-0.8, -0.3),
        'confidence_boost': 0.1
    },
    'very_negative': {
        'score_range': (-1.0, -0.8),
        'confidence_boost': 0.2
    }
}

# Analysis type configurations
ANALYSIS_TYPES = {
    'earnings': {
        'required_sections': ['prepared_remarks', 'qa'],
        'key_topics': ['guidance', 'performance', 'strategy'],
        'confidence_weights': {
            'has_numbers': 0.3,
            'has_comparisons': 0.2,
            'has_forward_looking': 0.3,
            'has_management_quotes': 0.2
        }
    },
    'news': {
        'required_sections': ['headline', 'body'],
        'key_topics': ['announcements', 'market_impact', 'analysis'],
        'confidence_weights': {
            'has_quotes': 0.2,
            'has_sources': 0.3,
            'has_context': 0.3,
            'has_data': 0.2
        }
    },
    'press_release': {
        'required_sections': ['headline', 'body'],
        'key_topics': ['announcements', 'strategic', 'financial'],
        'confidence_weights': {
            'has_details': 0.3,
            'has_quotes': 0.2,
            'has_numbers': 0.3,
            'has_timeline': 0.2
        }
    }
}

def create_analyzer(
    analyzer_type: str,
    api_key: str,
    config: dict = None
) -> QualitativeAnalyzer:
    """Create a new instance of a qualitative analyzer.
    
    This is the recommended way to instantiate analyzers, as it ensures proper
    initialization and configuration.
    
    Args:
        analyzer_type: Type of analyzer ('earnings' or 'news')
        api_key: OpenAI API key
        config: Optional configuration dictionary
        
    Returns:
        Configured analyzer instance
    """
    config = config or DEFAULT_CONFIG
    
    if analyzer_type == 'earnings':
        return EarningsAnalyzer(
            api_key=api_key,
            model=config['model']['name']
        )
    elif analyzer_type == 'news':
        return NewsAnalyzer(
            api_key=api_key,
            model=config['model']['name']
        )
    else:
        raise ValueError(f"Unknown analyzer type: {analyzer_type}")

def create_text_processor(config: dict = None) -> TextProcessor:
    """Create a new instance of TextProcessor.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured TextProcessor instance
    """
    return TextProcessor()

def get_version() -> str:
    """Get the current version of the qualitative analysis package.
    
    Returns:
        Version string
    """
    return __version__

def get_config() -> dict:
    """Get the current configuration settings.
    
    Returns:
        Dictionary containing all configuration settings
    """
    return {
        'default_config': DEFAULT_CONFIG,
        'sentiment_config': SENTIMENT_CONFIG,
        'analysis_types': ANALYSIS_TYPES
    }
