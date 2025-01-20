import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
import json
import aiohttp
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

@dataclass
class QualitativeMetrics:
    """Base metrics for qualitative analysis."""
    sentiment_score: float  # -1 to 1, indicating negative to positive sentiment
    confidence_score: float  # 0 to 1, indicating analysis confidence
    key_points: List[str]  # List of important points identified
    risks: List[str]      # List of identified risks
    opportunities: List[str]  # List of identified opportunities
    timestamp: datetime   # When the analysis was performed

@dataclass
class AnalysisResult:
    """Container for qualitative analysis results."""
    metrics: QualitativeMetrics
    raw_text: str
    processed_text: Optional[str] = None
    metadata: Dict = None
    source_type: str = None
    analysis_type: str = None

class QualitativeAnalyzer(ABC):
    """Base class for qualitative analyzers."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-1106-preview"):
        """Initialize the analyzer.
        
        Args:
            api_key: OpenAI API key
            model: GPT model to use
        """
        self.api_key = api_key
        self.model = model
        self._session = None
        self.client = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
        
    async def initialize(self):
        """Initialize async resources."""
        if not self._session:
            self._session = aiohttp.ClientSession()
            self.client = AsyncOpenAI(api_key=self.api_key)
            
    async def cleanup(self):
        """Cleanup async resources."""
        if self._session:
            await self._session.close()
            self._session = None
            self.client = None
            
    @abstractmethod
    async def analyze(self, text: str, **kwargs) -> AnalysisResult:
        """Analyze text content.
        
        Args:
            text: Text content to analyze
            **kwargs: Additional analyzer-specific parameters
            
        Returns:
            AnalysisResult containing analysis metrics and data
        """
        pass
        
    async def _analyze_with_gpt(
        self,
        text: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> Dict:
        """Analyze text using GPT model.
        
        Args:
            text: Text to analyze
            system_prompt: System role prompt
            user_prompt: User role prompt
            temperature: Model temperature (default: 0.7)
            
        Returns:
            Dictionary containing GPT analysis
        """
        try:
            if not text:
                logger.error("Empty text provided for analysis")
                return {}

            if not self.client:
                await self.initialize()

            # Prepare messages for the API
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt.format(text=text)
                }
            ]

            logger.info("Making GPT API call...")
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=4000,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    response_format={"type": "json_object"}
                )
                
                if response.choices and response.choices[0].message.content:
                    content = response.choices[0].message.content
                    logger.info("Successfully received GPT response")
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse GPT response as JSON: {str(e)}")
                        return {}
                else:
                    logger.error("No response content from GPT")
                    return {}
                    
            except Exception as e:
                logger.error(f"Error in GPT API call: {str(e)}")
                return {}

        except Exception as e:
            logger.error(f"Error in GPT analysis: {str(e)}")
            return {}
            
    def _create_metrics(
        self,
        sentiment: float,
        confidence: float,
        key_points: List[str],
        risks: List[str],
        opportunities: List[str]
    ) -> QualitativeMetrics:
        """Create QualitativeMetrics object.
        
        Args:
            sentiment: Sentiment score (-1 to 1)
            confidence: Confidence score (0 to 1)
            key_points: List of key points
            risks: List of risks
            opportunities: List of opportunities
            
        Returns:
            QualitativeMetrics object
        """
        return QualitativeMetrics(
            sentiment_score=max(-1.0, min(1.0, sentiment)),
            confidence_score=max(0.0, min(1.0, confidence)),
            key_points=key_points,
            risks=risks,
            opportunities=opportunities,
            timestamp=datetime.now()
        )
        
    def _validate_text(self, text: str) -> bool:
        """Validate input text.
        
        Args:
            text: Text to validate
            
        Returns:
            bool indicating if text is valid
        """
        if not text:
            logger.error("Empty text provided")
            return False
            
        if not isinstance(text, str):
            logger.error(f"Invalid text type: {type(text)}")
            return False
            
        if len(text.strip()) < 50:  # Minimum length for meaningful analysis
            logger.error(f"Text too short: {len(text)} characters")
            return False
            
        return True
        
    def _normalize_sentiment(self, raw_sentiment: str) -> float:
        """Normalize sentiment string to float.
        
        Args:
            raw_sentiment: Raw sentiment string
            
        Returns:
            float between -1 and 1
        """
        sentiment_map = {
            'very_positive': 1.0,
            'positive': 0.5,
            'neutral': 0.0,
            'negative': -0.5,
            'very_negative': -1.0
        }
        return sentiment_map.get(raw_sentiment.lower(), 0.0)
        
    def _calculate_confidence(self, analysis: Dict) -> float:
        """Calculate confidence score from analysis.
        
        Args:
            analysis: Analysis dictionary
            
        Returns:
            float between 0 and 1
        """
        try:
            # Factors that contribute to confidence
            factors = {
                'has_key_points': bool(analysis.get('key_points')),
                'has_risks': bool(analysis.get('risks')),
                'has_opportunities': bool(analysis.get('opportunities')),
                'sentiment_strength': abs(self._normalize_sentiment(analysis.get('sentiment', 'neutral')))
            }
            
            # Calculate weighted average
            weights = {
                'has_key_points': 0.3,
                'has_risks': 0.2,
                'has_opportunities': 0.2,
                'sentiment_strength': 0.3
            }
            
            confidence = sum(
                value * weights[factor]
                for factor, value in factors.items()
            )
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.5  # Default to medium confidence
