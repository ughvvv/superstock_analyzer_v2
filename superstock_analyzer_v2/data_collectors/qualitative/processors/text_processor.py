import logging
import re
from typing import List, Dict, Optional, Tuple
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

logger = logging.getLogger(__name__)

class TextProcessor:
    """Processor for text preprocessing and analysis."""
    
    def __init__(self):
        """Initialize the text processor."""
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
            
        except Exception as e:
            logger.error(f"Error initializing text processor: {str(e)}")
            raise
            
    def clean_text(self, text: str) -> str:
        """Clean and normalize text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        try:
            if not text:
                return ""
                
            # Convert to lowercase
            text = text.lower()
            
            # Remove special characters and extra whitespace
            text = re.sub(r'[^\w\s\.]', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            
            # Fix common OCR errors
            text = self._fix_ocr_errors(text)
            
            # Remove boilerplate text
            text = self._remove_boilerplate(text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            return text
            
    def segment_text(self, text: str, max_length: int = 2000) -> List[str]:
        """Split text into segments while preserving context.
        
        Args:
            text: Text to segment
            max_length: Maximum segment length
            
        Returns:
            List of text segments
        """
        try:
            if not text:
                return []
                
            # Split into sentences
            sentences = sent_tokenize(text)
            
            segments = []
            current_segment = []
            current_length = 0
            
            for sentence in sentences:
                sentence_length = len(sentence)
                
                if current_length + sentence_length > max_length:
                    # Save current segment
                    if current_segment:
                        segments.append(' '.join(current_segment))
                    current_segment = [sentence]
                    current_length = sentence_length
                else:
                    current_segment.append(sentence)
                    current_length += sentence_length
                    
            # Add final segment
            if current_segment:
                segments.append(' '.join(current_segment))
                
            return segments
            
        except Exception as e:
            logger.error(f"Error segmenting text: {str(e)}")
            return [text]
            
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """Extract key phrases from text.
        
        Args:
            text: Text to analyze
            max_phrases: Maximum number of phrases to extract
            
        Returns:
            List of key phrases
        """
        try:
            # Tokenize and lemmatize
            words = word_tokenize(text.lower())
            words = [
                self.lemmatizer.lemmatize(word)
                for word in words
                if word not in self.stop_words and word.isalnum()
            ]
            
            # Find frequent phrases
            phrases = []
            for i in range(len(words) - 2):
                phrase = ' '.join(words[i:i+3])
                if self._is_valid_phrase(phrase):
                    phrases.append(phrase)
                    
            # Count phrase frequencies
            phrase_counts = {}
            for phrase in phrases:
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
                
            # Sort by frequency
            sorted_phrases = sorted(
                phrase_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return [phrase for phrase, _ in sorted_phrases[:max_phrases]]
            
        except Exception as e:
            logger.error(f"Error extracting key phrases: {str(e)}")
            return []
            
    def find_context_window(
        self,
        text: str,
        target: str,
        window_size: int = 100
    ) -> Optional[str]:
        """Find context window around a target phrase.
        
        Args:
            text: Full text to search
            target: Target phrase to find context for
            window_size: Number of characters before/after target
            
        Returns:
            Context window containing target, or None if not found
        """
        try:
            target = target.lower()
            text = text.lower()
            
            start = text.find(target)
            if start == -1:
                return None
                
            # Find window boundaries
            window_start = max(0, start - window_size)
            window_end = min(len(text), start + len(target) + window_size)
            
            # Expand to sentence boundaries
            while window_start > 0 and text[window_start] != '.':
                window_start -= 1
            while window_end < len(text) and text[window_end] != '.':
                window_end += 1
                
            return text[window_start:window_end].strip()
            
        except Exception as e:
            logger.error(f"Error finding context window: {str(e)}")
            return None
            
    def extract_sections(self, text: str) -> Dict[str, str]:
        """Extract common sections from text.
        
        Args:
            text: Text to process
            
        Returns:
            Dictionary mapping section names to content
        """
        try:
            sections = {}
            
            # Find prepared remarks
            if 'prepared remarks' in text.lower():
                remarks = self._extract_section(
                    text,
                    start='prepared remarks',
                    end='question'
                )
                if remarks:
                    sections['prepared_remarks'] = remarks
                    
            # Find Q&A section
            if 'question' in text.lower() and 'answer' in text.lower():
                qa = self._extract_section(
                    text,
                    start='question and answer',
                    end='conference call'
                )
                if qa:
                    sections['qa'] = qa
                    
            # Find forward-looking statements
            if 'forward' in text.lower() and 'statement' in text.lower():
                forward = self._extract_section(
                    text,
                    start='forward-looking statements',
                    end='prepared remarks'
                )
                if forward:
                    sections['forward_looking'] = forward
                    
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting sections: {str(e)}")
            return {}
            
    def _fix_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors in text."""
        fixes = {
            r'([0-9])l': r'\1i',  # Fix 1l -> 1i
            r'([0-9])I': r'\1l',  # Fix 1I -> 1l
            r'\bI([^a-zA-Z])': r'1\1',  # Fix I -> 1 at word start
            r'\b0([^.,0-9])': r'O\1',  # Fix 0 -> O at word start
            r'([^.,0-9])0\b': r'\1O'  # Fix 0 -> O at word end
        }
        
        for pattern, replacement in fixes.items():
            text = re.sub(pattern, replacement, text)
            
        return text
        
    def _remove_boilerplate(self, text: str) -> str:
        """Remove common boilerplate text."""
        boilerplate = [
            r'this transcript is produced by \w+',
            r'this conference call contains forward-looking statements',
            r'forward-looking statements are subject to risks',
            r'actual results may differ materially',
            r'please see our sec filings',
            r'with that, (let me|i will) turn (it|the call) over to'
        ]
        
        for pattern in boilerplate:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
        return text
        
    def _is_valid_phrase(self, phrase: str) -> bool:
        """Check if a phrase is valid for extraction."""
        # Ignore phrases with only stopwords
        words = phrase.split()
        if all(word in self.stop_words for word in words):
            return False
            
        # Ignore phrases with numbers only
        if all(word.isdigit() for word in words):
            return False
            
        # Require at least one content word
        return any(
            word not in self.stop_words and not word.isdigit()
            for word in words
        )
        
    def _extract_section(
        self,
        text: str,
        start: str,
        end: str
    ) -> Optional[str]:
        """Extract section between start and end markers."""
        try:
            # Find start
            start_idx = text.lower().find(start.lower())
            if start_idx == -1:
                return None
                
            # Find end
            end_idx = text.lower().find(end.lower(), start_idx)
            if end_idx == -1:
                end_idx = len(text)
                
            # Extract and clean section
            section = text[start_idx:end_idx].strip()
            return self.clean_text(section)
            
        except Exception as e:
            logger.error(f"Error extracting section: {str(e)}")
            return None
