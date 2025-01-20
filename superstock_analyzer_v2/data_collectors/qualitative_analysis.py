"""Essential qualitative analysis for MVP."""

import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class QualitativeInsights:
    """Basic structure for qualitative insights."""
    def __init__(self):
        self.sentiment_score: float = 0.0
        self.key_points: List[str] = []
        self.risks: List[str] = []
        self.opportunities: List[str] = []
        self.management_assessment: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert insights to dictionary format."""
        return {
            'sentiment_score': self.sentiment_score,
            'key_points': self.key_points,
            'risks': self.risks,
            'opportunities': self.opportunities,
            'management_assessment': self.management_assessment
        }

class QualitativeAnalyzer:
    """Basic analyzer for qualitative data."""
    
    def __init__(self, api_key: str = None):
        """Initialize the analyzer."""
        self.api_key = api_key
        self.model = "gpt-4-1106-preview"
        self.client = None
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
    async def initialize(self):
        """Initialize OpenAI client."""
        if not self.client and self.openai_api_key:
            self.client = AsyncOpenAI(api_key=self.openai_api_key)
            
    async def analyze_earnings_call(self, transcript: str) -> Dict[str, Any]:
        """Analyze earnings call transcript with basic insights."""
        try:
            if not transcript:
                return {}
                
            await self.initialize()
            if not self.client:
                logger.error("OpenAI client not initialized")
                return {}

            prompt = """Analyze this earnings call transcript and provide:
            1. Overall sentiment (very positive, positive, neutral, negative, very negative)
            2. Key points about company performance
            3. Main risks and challenges
            4. Growth opportunities
            5. Management effectiveness assessment

            Format response as JSON with these sections."""

            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst."},
                    {"role": "user", "content": f"{prompt}\n\nTranscript:\n{transcript}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error analyzing earnings call: {str(e)}")
            return {}

    async def analyze_news(self, articles: List[Dict]) -> Dict[str, Any]:
        """Analyze recent news articles."""
        try:
            if not articles:
                return {}
                
            await self.initialize()
            if not self.client:
                logger.error("OpenAI client not initialized")
                return {}

            # Prepare recent news content
            recent_articles = sorted(
                articles,
                key=lambda x: datetime.strptime(x.get('publishedDate', '2000-01-01'), '%Y-%m-%d'),
                reverse=True
            )[:5]  # Only analyze 5 most recent articles

            content = "\n\n".join([
                f"Title: {article.get('title', '')}\n"
                f"Date: {article.get('publishedDate', '')}\n"
                f"Summary: {article.get('text', '')}"
                for article in recent_articles
            ])

            prompt = """Analyze these news articles and provide:
            1. Overall market sentiment
            2. Key developments or announcements
            3. Potential risks
            4. Growth opportunities

            Format response as JSON with these sections."""

            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst."},
                    {"role": "user", "content": f"{prompt}\n\nArticles:\n{content}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error analyzing news: {str(e)}")
            return {}

    def _convert_sentiment_to_score(self, sentiment: str) -> float:
        """Convert sentiment string to numerical score."""
        sentiment_scores = {
            'very_positive': 1.0,
            'positive': 0.75,
            'neutral': 0.5,
            'negative': 0.25,
            'very_negative': 0.0
        }
        return sentiment_scores.get(sentiment.lower(), 0.5)

    async def get_qualitative_data(self, symbol: str, earnings_data: Optional[str] = None, 
                                 news_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Get qualitative insights from available data."""
        insights = QualitativeInsights()
        
        try:
            # Analyze earnings call if available
            if earnings_data:
                earnings_analysis = await self.analyze_earnings_call(earnings_data)
                if earnings_analysis:
                    insights.sentiment_score = self._convert_sentiment_to_score(
                        earnings_analysis.get('sentiment', 'neutral')
                    )
                    insights.key_points.extend(earnings_analysis.get('key_points', []))
                    insights.risks.extend(earnings_analysis.get('risks', []))
                    insights.opportunities.extend(earnings_analysis.get('opportunities', []))
                    insights.management_assessment.update(
                        earnings_analysis.get('management_assessment', {})
                    )

            # Analyze news if available
            if news_data:
                news_analysis = await self.analyze_news(news_data)
                if news_analysis:
                    # Average sentiment with earnings if both available
                    news_sentiment = self._convert_sentiment_to_score(
                        news_analysis.get('sentiment', 'neutral')
                    )
                    if earnings_data:
                        insights.sentiment_score = (insights.sentiment_score + news_sentiment) / 2
                    else:
                        insights.sentiment_score = news_sentiment
                        
                    insights.key_points.extend(news_analysis.get('key_points', []))
                    insights.risks.extend(news_analysis.get('risks', []))
                    insights.opportunities.extend(news_analysis.get('opportunities', []))

            return insights.to_dict()
            
        except Exception as e:
            logger.error(f"Error getting qualitative data for {symbol}: {str(e)}")
            return {}
