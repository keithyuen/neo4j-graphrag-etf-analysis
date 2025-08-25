import re
import structlog
from typing import Dict, List, Tuple, Any
from app.models.entities import PreprocessedText

logger = structlog.get_logger()

class Preprocessor:
    def __init__(self):
        self.number_patterns = {
            'percentage': re.compile(r'(\d+(?:\.\d+)?)\s*%'),
            'decimal': re.compile(r'0\.\d+'),
            'count': re.compile(r'\b(top|first|best)\s+(\d+)\b', re.IGNORECASE),
            'threshold': re.compile(r'(?:>=|≥|at least|minimum of|more than)\s*(\d+(?:\.\d+)?)\s*%?')
        }
        
        self.ticker_pattern = re.compile(r'\b[A-Z]{2,5}\b')
        
    async def process(self, text: str) -> PreprocessedText:
        """
        Preprocess user input text.
        Returns PreprocessedText model with all extracted information.
        """
        # Normalize text
        normalized = self._normalize_text(text)
        
        # Extract numbers and percentages
        numbers = self._extract_numbers(text)
        
        # Extract potential tickers
        tickers = self._extract_tickers(text)
        
        # Tokenize
        tokens = self._tokenize(normalized)
        
        result = PreprocessedText(
            normalized_text=normalized,
            extracted_numbers=numbers,
            potential_tickers=tickers,
            tokens=tokens,
            original_text=text
        )
        
        logger.info("Text preprocessed", 
                   text_length=len(text),
                   numbers_found=len(numbers.get('percentages', [])) + len(numbers.get('counts', [])),
                   tickers_found=len(tickers),
                   tokens_count=len(tokens))
        
        return result
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text case and remove extra whitespace."""
        # Convert to lowercase
        normalized = text.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _extract_numbers(self, text: str) -> Dict[str, List[float]]:
        """Extract numbers, percentages, and thresholds."""
        numbers = {
            'percentages': [],
            'decimals': [],
            'counts': [],
            'thresholds': []
        }
        
        # Extract percentages
        for match in self.number_patterns['percentage'].finditer(text):
            numbers['percentages'].append(float(match.group(1)) / 100)
        
        # Extract decimal values
        for match in self.number_patterns['decimal'].finditer(text):
            numbers['decimals'].append(float(match.group(0)))
            
        # Extract counts (top N, first N)
        for match in self.number_patterns['count'].finditer(text):
            numbers['counts'].append(int(match.group(2)))
            
        # Extract thresholds (>= X%, at least X%)
        for match in self.number_patterns['threshold'].finditer(text):
            value = float(match.group(1))
            # Convert to decimal if it looks like percentage
            if value > 1:
                value /= 100
            numbers['thresholds'].append(value)
        
        return numbers
    
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract potential ticker symbols."""
        matches = self.ticker_pattern.findall(text.upper())
        # Filter out common English words that might match pattern
        excluded = {
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 
            'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BUT', 'HIS', 
            'HAS', 'WHO', 'WITH', 'FROM', 'THEY', 'KNOW', 'WANT', 
            'BEEN', 'GOOD', 'MUCH', 'SOME', 'TIME', 'VERY', 'WHEN', 
            'COME', 'HERE', 'HOW', 'JUST', 'LIKE', 'LONG', 'MAKE', 
            'MANY', 'OVER', 'SUCH', 'TAKE', 'THAN', 'THEM', 'WELL', 
            'WHAT', 'WHERE'
        }
        return [ticker for ticker in matches if ticker not in excluded]
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Remove punctuation and split
        cleaned = re.sub(r'[^\w\s]', ' ', text)
        tokens = cleaned.split()
        return [token for token in tokens if len(token) > 1]