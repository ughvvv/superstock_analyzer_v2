# Superstock Analyzer

A sophisticated stock screening program that identifies potential "Superstocks" using Jesse Stine's comprehensive methodology. The program implements a detailed scoring and weighting system, combining quantitative and qualitative factors to identify exceptional investment opportunities.

## Features

- Comprehensive scoring system based on fundamental, technical, and qualitative factors
- Multi-stage filtering process to optimize analysis efficiency
- Integration with OpenAI API (using gpt-4o-mini) for qualitative analysis
- Enhanced financial data collection:
  - Multi-year data support for more complete analysis
  - Intelligent retry mechanism with exponential backoff
  - Automatic fallback to individual API calls when bulk data is incomplete
  - Rate limiting handling and request optimization
- Real-time data collection from multiple sources including Financial Modeling Prep API
- Detailed reporting and visualization
- Configurable screening criteria
- Management execution tracking
- Narrative evolution analysis
- Email notifications for qualifying stocks
- Proxy support for corporate environments
- Comprehensive logging system

## Installation

### Install from source
1. Clone the repository:
```bash
git clone https://github.com/blakecole/superstock-analyzer.git
cd superstock-analyzer
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Edit .env with your credentials:
- Required:
  - OPENAI_API_KEY: For qualitative analysis using gpt-4o-mini
  - FMP_API_KEY: Financial Modeling Prep API for market data and earnings transcripts
- Optional APIs (more data sources = better analysis):
  - ALPHA_VANTAGE_API_KEY: Additional market data
  - SEEKING_ALPHA_API_KEY: Additional earnings call transcripts
  - FINNHUB_API_KEY: Real-time market data
- Optional Database (for data persistence):
  - DB_HOST: Database host
  - DB_PORT: Database port
  - DB_NAME: Database name
  - DB_USER: Database username
  - DB_PASSWORD: Database password
- Optional Email Notifications:
  - SMTP_SERVER: Email server (e.g., smtp.gmail.com)
  - SMTP_PORT: Email port (e.g., 587)
  - EMAIL_ADDRESS: Your email address
  - EMAIL_PASSWORD: Your email password/app password
- Optional Proxy Settings:
  - HTTP_PROXY: HTTP proxy URL
  - HTTPS_PROXY: HTTPS proxy URL
- Optional Rate Limiting:
  - MAX_REQUESTS_PER_MINUTE: API request rate limit
  - REQUEST_TIMEOUT_SECONDS: API request timeout
- Optional Logging:
  - LOG_LEVEL: Logging level (INFO, DEBUG, etc.)
  - LOG_FILE_PATH: Log file location

## Usage

### Python API
```python
from superstock_analyzer.main import SuperstockAnalyzer

# Basic usage
analyzer = SuperstockAnalyzer()
results = analyzer.analyze_market()

# Custom configuration
config = {
    'output_dir': 'reports',
    'min_market_cap': 5e6,     # $5M minimum
    'max_market_cap': 250e6,   # $250M maximum
    'min_price': 1.0,          # $1 minimum price
    'min_volume_base': 100000,  # Base minimum volume
    'min_volume_factor': 500000, # Factor for dynamic volume calculation
    'min_fundamental_score_for_qualitative': 35,  # 77.8% minimum
    'min_technical_score_for_qualitative': 20,    # 80% minimum
    'min_earnings_growth': 0.15,                  # 15% minimum
    'max_debt_to_equity': 0.75,                   # 75% maximum
    'min_relative_strength_rank': 80              # Top 20%
}

analyzer = SuperstockAnalyzer(config)
results = analyzer.analyze_market()
```

### Direct Execution
```bash
python main.py
```

### Jupyter Notebook
See `Superstock_Analyzer_Demo.ipynb` for interactive examples and visualizations.

## Data Collection Architecture

The program implements a sophisticated data collection and processing pipeline designed for efficiency and reliability:

### 1. Data Collection Funnel

#### Stage 1: Market Symbol Collection
- Fetches symbols from multiple exchanges (NASDAQ, NYSE, Russell 3000)
- Filters out special securities (units, warrants, preferred stock)
- Implements pattern-based filtering for valid symbols
- Caches results to minimize API calls

#### Stage 2: Initial Quote Collection
- Processes symbols in batches of 25 for optimal API usage
- Implements parallel processing with thread pooling
- Applies basic filtering criteria:
  - Minimum volume threshold
  - Market cap range
  - Basic price requirements
- Caches filtered quotes for future use

#### Stage 3: Data Enhancement
- Processes quotes in configurable batch sizes (default 50)
- Collects multiple data types per symbol:
  - Technical data (price history, indicators)
  - Financial data (statements, metrics)
  - Ownership data (institutional, float)
  - Insider trading data
  - News and earnings transcripts
- Implements fault-tolerant batch processing:
  - Individual stock failures don't affect batch
  - Failed stocks marked as inactive
  - Automatic retries with exponential backoff

### 2. Batch Processing Architecture

#### Technical Data Collection
- Processes symbols in sub-batches of 25
- Parallel processing with 5 worker threads
- Features:
  - Historical data validation
  - Recent data verification
  - Price data resampling
  - Technical indicator calculation
  - Pattern analysis

#### Financial Data Collection
- Implements smart batching based on API limits
- Caches responses to minimize API calls
- Collects:
  - Income statements
  - Balance sheets
  - Cash flow statements
  - Key metrics
  - Growth rates

#### Market Data Collection
- Real-time quote aggregation
- Volume profile analysis
- Market context calculation
- Relative strength computation

### 3. Error Handling and Recovery

#### Validation Layers
- Symbol validation
- Data freshness checks
- Required field verification
- Data consistency checks

#### Failure Management
- Individual stock failure isolation
- Batch continuation on partial failures
- Automatic retry mechanism
- Exponential backoff for rate limits

#### Caching Strategy
- Multi-level caching system
- Cache invalidation based on data type
- Persistent storage for inactive symbols
- Memory-efficient cache management

### 4. Performance Optimization

#### API Usage
- Rate limit management
- Request batching
- Response caching
- Parallel processing

#### Resource Management
- Memory-efficient data structures
- Garbage collection optimization
- Connection pooling
- Thread pool management

## Filtering Process

The program uses a multi-stage filtering process to efficiently identify potential Superstocks:

### 1. Initial Filter (Market/Price Based)
- Market cap: $5M-$250M
- Price: >= $1.0
- Dynamic volume threshold based on price

### 2. Quantitative Thresholds
Before proceeding to resource-intensive qualitative analysis:
- Fundamental score must be ≥ 35/45 (77.8%)
- Technical score must be ≥ 20/25 (80%)
- Earnings growth must be ≥ 15%
- Debt/Equity must be ≤ 75%
- Relative strength must be in top 20%

### 3. Qualitative Analysis
Only stocks passing the above thresholds proceed to:
- Management quality assessment through earnings call transcripts
- Industry analysis
- Narrative evaluation
- Risk factor analysis

## Data Sources

The program collects data from multiple sources:

### 1. Financial Modeling Prep API
- Market data (prices, volumes, etc.)
- Financial statements
- Key metrics
- Earnings call transcripts
- Insider trading data

### 2. OpenAI API (gpt-4o-mini)
- Qualitative analysis of earnings calls
- Management communication assessment
- Industry trend analysis
- Risk evaluation

### 3. Additional Sources
- Alpha Vantage: Technical indicators
- Seeking Alpha: Additional earnings insights
- Finnhub: Real-time market data

## Scoring System

The program uses a 100-point scoring system divided into three main categories:

### 1. Fundamental Factors (45 Points)

#### Earnings Quality (18 points)
- Sequential quarterly earnings growth (6 points)
- Evidence of sustainable earnings growth (6 points)
- Easy upcoming comparisons (4 points)
- Operating leverage metrics (2 points)

#### Financial Health (17 points)
- P/E ratio under 10 (4 points)
- Low debt levels (3 points)
- Strong debt service coverage (3 points)
- Improving working capital (3 points)
- Strong cash flow (2 points)
- Growing backlog (2 points)

#### Company Structure (10 points)
- Low float (4-8M shares) (4 points)
- Market cap under $250M (3 points)
- Conservative management style (3 points)

### 2. Technical Factors (25 Points)

#### Base Formation (10 points)
- Strong base development (4 points)
- Low volume during base formation (3 points)
- Tight price range in base (3 points)

#### Breakout Quality (8 points)
- Volume expansion on breakout (3 points)
- Break above 30-week moving average (3 points)
- ~45-degree angle of price movement (2 points)

#### Relative Strength & Risk Metrics (7 points)
- Top 10% relative strength (3 points)
- Strong industry rank (2 points)
- Strong accumulation patterns (2 points)

### 3. Qualitative Factors (30 Points)

#### Super Theme (12 points)
- Unique/emerging industry theme (5 points)
- Limited competition in niche (4 points)
- Market under-appreciation of story (3 points)

#### Insider Activity (10 points)
- Multiple C-level executives buying (4 points)
- Size of purchases relative to salary (3 points)
- Timing of purchases (3 points)

#### Management Quality (8 points)
- Track record of execution (3 points)
- Conservative communication style (3 points)
- Limited stock dilution history (2 points)

### Bonus/Penalty Points (±10 Points)

#### Bonus Points
- No analyst coverage (+2)
- No options listed (+2)
- Game-changing catalyst identified (+3)
- "Magic line" support established (+2)
- Exceptional accumulation patterns (+1)

#### Penalty Points
- Recent secondary offering (-5)
- Excessive media coverage (-3)
- Overcrowded trade (-2)

## Output

The analyzer generates comprehensive reports in multiple formats:

### 1. Individual Stock Reports
- Detailed scoring breakdown
- Technical analysis charts
- Fundamental metrics
- Sequential earnings call analysis
- Management execution tracking
- Qualitative insights
- Risk factors

### 2. Summary Report
- Ranked list of qualifying stocks
- Score distributions
- Key metrics comparison
- Market environment analysis
- Sector trends
- Filtering statistics

## Configuration Options

The analyzer can be configured with various options to customize its behavior:

```python
config = {
    # Output and Cache
    'output_dir': 'reports',
    'cache_dir': 'cache',
    'state_file': 'analysis_state.json',
    
    # Market Cap Thresholds
    'min_market_cap': 25e6,     # $25M minimum
    'max_market_cap': 10e9,     # $10B maximum
    
    # Price and Volume Thresholds
    'min_price': 1.0,           # $1 minimum price
    'min_volume': 25000,        # Minimum daily volume
    'min_percent_change': 0.5,   # Minimum daily % change
    
    # API Configuration
    'max_requests_per_minute': 3000,
    'request_timeout': 60,       # seconds
    'batch_size': 25,
    'max_symbols': 2000,
    'max_workers': 10,
    
    # Retry Configuration
    'max_retries': 3,
    'retry_delay': 1,
    'max_delay': 10,
    
    # Scoring Thresholds
    'min_fundamental_score_for_qualitative': 15,
    'min_technical_score_for_qualitative': 3,
    'min_earnings_growth': 0.01,
    'max_debt_to_equity': 5.0,
    'min_relative_strength_rank': 15
}
```

## Recent Updates

### v2.1.0 (2024-12-16)
- Enhanced financial data collection system:
  - Added multi-year data support for more comprehensive analysis
  - Implemented intelligent retry mechanism with exponential backoff
  - Added automatic fallback to individual API calls when bulk data is incomplete
  - Improved rate limiting handling and request optimization
  - Enhanced data validation and deduplication
- Improved error handling and logging:
  - More detailed error messages and logging
  - Better tracking of data completeness
  - Enhanced debugging capabilities
- Configuration updates:
  - Added new retry and timeout configurations
  - Updated default thresholds for better stock filtering
  - Improved proxy handling

## Dependencies

Required packages are listed in requirements.txt:
- yfinance (≥0.2.3): Yahoo Finance data retrieval (no API key required)
- pandas (≥1.5.0): Data manipulation and analysis
- numpy (≥1.21.0): Numerical computations
- openai (≥0.27.0): GPT integration for qualitative analysis
- ta-lib (≥0.4.24): Technical analysis indicators
- matplotlib (≥3.5.0): Charting and visualization
- seaborn (≥0.11.0): Statistical visualizations
- scipy (≥1.7.0): Scientific computing
- python-dotenv (≥0.19.0): Environment variable management
- beautifulsoup4 (≥4.9.3): Web scraping
- requests (≥2.28.0): HTTP requests
- schedule (≥1.1.0): Task scheduling

## Development

### Setting up development environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running tests
```bash
pytest tests/
```

### Code style
The project follows PEP 8 guidelines. Use flake8 for linting:
```bash
flake8 .
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Areas of particular interest:
- Additional data source integrations
- Enhanced qualitative analysis features
- New technical indicators
- Improved visualization options
- CLI interface implementation

### Development Process
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Always conduct your own research and due diligence before making investment decisions. The program's analysis should not be considered as financial advice.
