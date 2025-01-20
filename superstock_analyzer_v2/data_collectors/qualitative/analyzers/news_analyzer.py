import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base_analyzer import QualitativeAnalyzer, QualitativeMetrics, AnalysisResult
from ..processors.text_processor import TextProcessor

logger = logging.getLogger(__name__)

class NewsAnalyzer(QualitativeAnalyzer):
    """Analyzer specifically for news articles and press releases."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-1106-preview"):
        """Initialize the news analyzer.
        
        Args:
            api_key: OpenAI API key
            model: GPT model to use
        """
        super().__init__(api_key, model)
        self.text_processor = TextProcessor()
        
    async def analyze(
        self,
        text: str,
        source_type: str = 'news',
        context: Optional[Dict] = None,
        **kwargs
    ) -> AnalysisResult:
        """Analyze news article or press release.
        
        Args:
            text: Article text
            source_type: Type of source ('news' or 'press_release')
            context: Optional context dictionary
            **kwargs: Additional parameters
            
        Returns:
            AnalysisResult containing analysis metrics and data
        """
        try:
            if not self._validate_text(text):
                raise ValueError("Invalid article text")
                
            # Clean and process text
            processed_text = self.text_processor.clean_text(text)
            
            # Extract key phrases
            key_phrases = self.text_processor.extract_key_phrases(processed_text)
            
            # Create system prompt based on source type
            system_prompt = self._get_system_prompt(source_type)
            
            # Create user prompt with context
            user_prompt = self._create_user_prompt(
                text=processed_text,
                key_phrases=key_phrases,
                context=context,
                source_type=source_type
            )
            
            # Analyze with GPT
            analysis = await self._analyze_with_gpt(
                text=processed_text,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3  # Lower temperature for more focused analysis
            )
            
            if not analysis:
                raise ValueError("Failed to get analysis from GPT")
                
            # Create metrics
            metrics = self._create_news_metrics(analysis)
            
            # Create result
            result = AnalysisResult(
                metrics=metrics,
                raw_text=text,
                processed_text=processed_text,
                metadata=self._create_metadata(analysis, context, key_phrases),
                source_type=source_type,
                analysis_type='news'
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing news: {str(e)}")
            return self._create_error_result(text, source_type)
            
    def _get_system_prompt(self, source_type: str) -> str:
        """Get appropriate system prompt based on source type."""
        if source_type == 'press_release':
            return """You are a senior financial analyst specializing in analyzing company press releases.
            Focus on official company announcements, strategic initiatives, and forward-looking statements.
            Look for specific details about company plans, achievements, and potential impact on business performance."""
        else:
            return """You are a senior financial analyst specializing in analyzing financial news articles.
            Focus on market perception, industry trends, and third-party perspectives.
            Look for insights about company performance, competitive position, and market dynamics."""
            
    def _create_user_prompt(
        self,
        text: str,
        key_phrases: List[str],
        context: Optional[Dict],
        source_type: str
    ) -> str:
        """Create user prompt with context."""
        prompt_parts = [
            f"Analyze the following {source_type}:",
            text,
            "\nKey phrases identified:",
            ", ".join(key_phrases)
        ]
        
        if context:
            prompt_parts.extend([
                "\nContext:",
                self._format_context(context)
            ])
            
        prompt_parts.append("""
        Provide a comprehensive analysis focusing on:
        1. Key developments and announcements
        2. Market implications and potential impact
        3. Strategic significance
        4. Risks and challenges
        5. Growth opportunities
        
        Format your response as a JSON object with the following structure:
        {
            "sentiment": "one of: very_positive, positive, neutral, negative, very_negative",
            "key_points": ["list of key points"],
            "market_impact": {
                "short_term": "description",
                "long_term": "description",
                "stock_price_impact": "likely impact"
            },
            "strategic_analysis": {
                "significance": "importance level",
                "alignment": "fit with strategy",
                "execution_risk": "risk level"
            },
            "competitive_implications": {
                "advantages": ["list of advantages"],
                "challenges": ["list of challenges"],
                "market_position": "impact on position"
            },
            "risk_assessment": {
                "operational_risks": ["list of risks"],
                "market_risks": ["list of risks"],
                "mitigation_factors": ["list of factors"]
            },
            "growth_opportunities": {
                "new_markets": ["list of markets"],
                "product_expansion": ["list of opportunities"],
                "strategic_benefits": ["list of benefits"]
            }
        }""")
        
        return "\n".join(prompt_parts)
        
    def _create_news_metrics(self, analysis: Dict) -> QualitativeMetrics:
        """Create metrics specific to news analysis.
        
        Args:
            analysis: Analysis dictionary from GPT
            
        Returns:
            QualitativeMetrics object
        """
        try:
            # Extract sentiment
            sentiment = self._normalize_sentiment(analysis.get('sentiment', 'neutral'))
            
            # Calculate confidence
            confidence = self._calculate_confidence(analysis)
            
            # Extract key points
            key_points = (
                analysis.get('key_points', []) +
                [analysis.get('market_impact', {}).get('short_term', '')] +
                [analysis.get('market_impact', {}).get('long_term', '')]
            )
            
            # Extract risks
            risks = (
                analysis.get('risk_assessment', {}).get('operational_risks', []) +
                analysis.get('risk_assessment', {}).get('market_risks', []) +
                analysis.get('competitive_implications', {}).get('challenges', [])
            )
            
            # Extract opportunities
            opportunities = (
                analysis.get('growth_opportunities', {}).get('new_markets', []) +
                analysis.get('growth_opportunities', {}).get('product_expansion', []) +
                analysis.get('growth_opportunities', {}).get('strategic_benefits', []) +
                analysis.get('competitive_implications', {}).get('advantages', [])
            )
            
            return self._create_metrics(
                sentiment=sentiment,
                confidence=confidence,
                key_points=list(set(p for p in key_points if p)),  # Remove duplicates and empty strings
                risks=list(set(r for r in risks if r)),
                opportunities=list(set(o for o in opportunities if o))
            )
            
        except Exception as e:
            logger.error(f"Error creating news metrics: {str(e)}")
            return self._create_default_metrics()
            
    def _format_context(self, context: Dict) -> str:
        """Format context for prompt."""
        try:
            sections = []
            
            # Format recent performance
            if 'performance' in context:
                perf = context['performance']
                sections.append(
                    "Recent Performance:\n" +
                    "\n".join(f"- {k}: {v}" for k, v in perf.items())
                )
                
            # Format industry context
            if 'industry' in context:
                ind = context['industry']
                sections.append(
                    "Industry Context:\n" +
                    "\n".join(f"- {k}: {v}" for k, v in ind.items())
                )
                
            # Format company background
            if 'company' in context:
                comp = context['company']
                sections.append(
                    "Company Background:\n" +
                    "\n".join(f"- {k}: {v}" for k, v in comp.items())
                )
                
            return "\n\n".join(sections)
            
        except Exception as e:
            logger.error(f"Error formatting context: {str(e)}")
            return ""
            
    def _create_metadata(
        self,
        analysis: Dict,
        context: Optional[Dict],
        key_phrases: List[str]
    ) -> Dict:
        """Create metadata for analysis result."""
        try:
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'model': self.model,
                'analysis_version': '2.0.0',
                'key_phrases': key_phrases
            }
            
            # Add market impact if available
            if 'market_impact' in analysis:
                metadata['market_impact'] = analysis['market_impact']
                
            # Add strategic analysis if available
            if 'strategic_analysis' in analysis:
                metadata['strategic_analysis'] = analysis['strategic_analysis']
                
            # Add competitive implications if available
            if 'competitive_implications' in analysis:
                metadata['competitive_implications'] = analysis['competitive_implications']
                
            # Add context if provided
            if context:
                metadata['context'] = context
                
            return metadata
            
        except Exception as e:
            logger.error(f"Error creating metadata: {str(e)}")
            return {'timestamp': datetime.now().isoformat()}
            
    def _create_error_result(self, text: str, source_type: str) -> AnalysisResult:
        """Create error result when analysis fails."""
        return AnalysisResult(
            metrics=self._create_default_metrics(),
            raw_text=text,
            processed_text=None,
            metadata={'error': True, 'timestamp': datetime.now().isoformat()},
            source_type=source_type,
            analysis_type='news'
        )
