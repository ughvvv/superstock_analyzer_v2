import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base_analyzer import QualitativeAnalyzer, QualitativeMetrics, AnalysisResult
from ..prompts.earnings_prompts import EARNINGS_SYSTEM_PROMPT, EARNINGS_USER_PROMPT

logger = logging.getLogger(__name__)

class EarningsAnalyzer(QualitativeAnalyzer):
    """Analyzer specifically for earnings call transcripts."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-1106-preview"):
        """Initialize the earnings analyzer.
        
        Args:
            api_key: OpenAI API key
            model: GPT model to use
        """
        super().__init__(api_key, model)
        
    async def analyze(
        self,
        text: str,
        context: Optional[Dict] = None,
        **kwargs
    ) -> AnalysisResult:
        """Analyze earnings call transcript.
        
        Args:
            text: Earnings call transcript text
            context: Optional context dictionary containing financial metrics
            **kwargs: Additional parameters
            
        Returns:
            AnalysisResult containing analysis metrics and data
        """
        try:
            if not self._validate_text(text):
                raise ValueError("Invalid transcript text")
                
            # Format context for prompt
            context_str = self._format_context(context) if context else ""
            
            # Analyze with GPT
            analysis = await self._analyze_with_gpt(
                text=text,
                system_prompt=EARNINGS_SYSTEM_PROMPT,
                user_prompt=EARNINGS_USER_PROMPT.format(
                    text=text,
                    context=context_str
                )
            )
            
            if not analysis:
                raise ValueError("Failed to get analysis from GPT")
                
            # Create metrics
            metrics = self._create_earnings_metrics(analysis)
            
            # Create result
            result = AnalysisResult(
                metrics=metrics,
                raw_text=text,
                processed_text=self._extract_key_segments(text),
                metadata=self._create_metadata(analysis, context),
                source_type='earnings_call',
                analysis_type='earnings'
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing earnings call: {str(e)}")
            return self._create_error_result(text)
            
    def _create_earnings_metrics(self, analysis: Dict) -> QualitativeMetrics:
        """Create metrics specific to earnings analysis.
        
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
                analysis.get('financial_performance', {}).get('key_metrics', []) +
                analysis.get('guidance', {}).get('key_points', [])
            )
            
            # Extract risks
            risks = (
                analysis.get('risks', []) +
                analysis.get('risk_assessment', {}).get('operational_risks', []) +
                analysis.get('risk_assessment', {}).get('market_risks', [])
            )
            
            # Extract opportunities
            opportunities = (
                analysis.get('opportunities', []) +
                analysis.get('guidance', {}).get('growth_drivers', []) +
                analysis.get('strategic_initiatives', {}).get('key_projects', [])
            )
            
            return self._create_metrics(
                sentiment=sentiment,
                confidence=confidence,
                key_points=list(set(key_points)),  # Remove duplicates
                risks=list(set(risks)),
                opportunities=list(set(opportunities))
            )
            
        except Exception as e:
            logger.error(f"Error creating earnings metrics: {str(e)}")
            return self._create_default_metrics()
            
    def _format_context(self, context: Dict) -> str:
        """Format context for prompt.
        
        Args:
            context: Context dictionary
            
        Returns:
            Formatted context string
        """
        try:
            if not context:
                return ""
                
            sections = []
            
            # Format previous quarter performance
            if 'previous_quarter' in context:
                prev = context['previous_quarter']
                sections.append(
                    "Previous Quarter Performance:\n"
                    f"Revenue: {prev.get('revenue', 'N/A')}\n"
                    f"EPS: {prev.get('eps', 'N/A')}\n"
                    f"Key Metrics: {prev.get('key_metrics', 'N/A')}"
                )
                
            # Format analyst expectations
            if 'expectations' in context:
                exp = context['expectations']
                sections.append(
                    "Analyst Expectations:\n"
                    f"Revenue Est: {exp.get('revenue', 'N/A')} "
                    f"(Range: {exp.get('revenue_low', 'N/A')} - {exp.get('revenue_high', 'N/A')})\n"
                    f"EPS Est: {exp.get('eps', 'N/A')} "
                    f"(Range: {exp.get('eps_low', 'N/A')} - {exp.get('eps_high', 'N/A')})\n"
                    f"Analyst Coverage: {exp.get('analyst_count', 'N/A')}"
                )
                
            return "\n\n".join(sections)
            
        except Exception as e:
            logger.error(f"Error formatting context: {str(e)}")
            return ""
            
    def _extract_key_segments(self, text: str) -> str:
        """Extract key segments from transcript.
        
        Args:
            text: Full transcript text
            
        Returns:
            Processed text containing key segments
        """
        try:
            segments = []
            
            # Try to extract prepared remarks
            if "prepared remarks" in text.lower():
                prepared_section = text.lower().split("prepared remarks")[1]
                prepared_section = prepared_section.split("question")[0]
                segments.append(prepared_section)
                
            # Try to extract Q&A highlights
            if "question-and-answer" in text.lower():
                qa_section = text.lower().split("question-and-answer")[1]
                segments.append(qa_section)
                
            # If no segments found, return original text
            if not segments:
                return text
                
            return "\n\n".join(segments)
            
        except Exception as e:
            logger.error(f"Error extracting key segments: {str(e)}")
            return text
            
    def _create_metadata(self, analysis: Dict, context: Optional[Dict]) -> Dict:
        """Create metadata for analysis result.
        
        Args:
            analysis: Analysis dictionary from GPT
            context: Optional context dictionary
            
        Returns:
            Metadata dictionary
        """
        try:
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'model': self.model,
                'analysis_version': '2.0.0'
            }
            
            # Add management assessment if available
            if 'management_execution' in analysis:
                metadata['management'] = {
                    'confidence': analysis['management_execution'].get('confidence_level'),
                    'strengths': analysis['management_execution'].get('key_strengths', []),
                    'improvements': analysis['management_execution'].get('areas_of_improvement', [])
                }
                
            # Add guidance assessment if available
            if 'guidance' in analysis:
                metadata['guidance'] = {
                    'revenue_outlook': analysis['guidance'].get('revenue_outlook'),
                    'earnings_outlook': analysis['guidance'].get('earnings_outlook'),
                    'growth_drivers': analysis['guidance'].get('growth_drivers', [])
                }
                
            # Add context if provided
            if context:
                metadata['context'] = context
                
            return metadata
            
        except Exception as e:
            logger.error(f"Error creating metadata: {str(e)}")
            return {'timestamp': datetime.now().isoformat()}
            
    def _create_error_result(self, text: str) -> AnalysisResult:
        """Create error result when analysis fails.
        
        Args:
            text: Original text
            
        Returns:
            AnalysisResult with error indicators
        """
        return AnalysisResult(
            metrics=self._create_default_metrics(),
            raw_text=text,
            processed_text=None,
            metadata={'error': True, 'timestamp': datetime.now().isoformat()},
            source_type='earnings_call',
            analysis_type='earnings'
        )
        
    def _create_default_metrics(self) -> QualitativeMetrics:
        """Create default metrics for error cases.
        
        Returns:
            QualitativeMetrics with neutral/empty values
        """
        return QualitativeMetrics(
            sentiment_score=0.0,
            confidence_score=0.0,
            key_points=[],
            risks=[],
            opportunities=[],
            timestamp=datetime.now()
        )
