import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Enable debug logging for all loggers
logging.getLogger('data_collectors').setLevel(logging.DEBUG)

from data_collectors.financial.collector import FinancialDataCollector

logger = logging.getLogger(__name__)

def test_dcf_valuation():
    # Initialize the collector
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        pytest.skip("FMP_API_KEY not set")
    
    collector = FinancialDataCollector(api_key=api_key)
    
    # Test with Apple (AAPL) as it's a well-known stock with reliable data
    symbol = "AAPL"
    
    logger.info(f"Fetching financial data for {symbol}...")
    financial_data = collector.get_financial_data(symbol)
    
    if not financial_data:
        logger.error("Failed to fetch financial data")
        return
    
    dcf_data = financial_data.get('dcf_valuations', {}).get('dcf_valuation', {})
    if not dcf_data:
        logger.error("No DCF valuation data found")
        return
    
    # Print key DCF metrics
    current_metrics = dcf_data.get('current_metrics', {})
    valuation_results = dcf_data.get('valuation_results', {})
    growth_rates = dcf_data.get('growth_rates', {})
    operational_metrics = dcf_data.get('operational_metrics', {})
    valuation_inputs = dcf_data.get('valuation_inputs', {})
    
    logger.info("\nDCF Valuation Results:")
    logger.info(f"Period: {current_metrics.get('period', 'N/A')} {current_metrics.get('year', 'N/A')}")
    logger.info(f"Current Price: ${valuation_results.get('current_price', 0):.2f}")
    logger.info(f"Equity Value per Share: ${current_metrics.get('equity_value_per_share', 0):.2f}")
    logger.info(f"Upside Potential: {valuation_results.get('upside_potential', 0)*100:.1f}%")
    
    logger.info("\nGrowth Rates:")
    logger.info(f"Revenue Growth: {growth_rates.get('revenue_growth', 0)*100:.1f}%")
    logger.info(f"EBITDA Margin: {growth_rates.get('ebitda_margin', 0)*100:.1f}%")
    logger.info(f"Long Term Growth: {growth_rates.get('long_term_growth', 0):.1f}%")
    
    logger.info("\nOperational Metrics (in billions):")
    logger.info(f"Revenue: ${operational_metrics.get('revenue', 0)/1e9:.1f}B")
    logger.info(f"EBITDA: ${operational_metrics.get('ebitda', 0)/1e9:.1f}B")
    logger.info(f"EBIT: ${operational_metrics.get('ebit', 0)/1e9:.1f}B")
    logger.info(f"Free Cash Flow (T1): ${operational_metrics.get('fcf_t1', 0)/1e9:.1f}B")
    
    logger.info("\nValuation Inputs:")
    logger.info(f"WACC: {valuation_inputs.get('wacc', 0):.1f}%")
    logger.info(f"Cost of Equity: {valuation_inputs.get('cost_of_equity', 0):.1f}%")
    logger.info(f"Cost of Debt: {valuation_inputs.get('cost_of_debt', 0):.1f}%")
    logger.info(f"Tax Rate: {valuation_inputs.get('tax_rate', 0):.1f}%")
    logger.info(f"Risk Free Rate: {valuation_inputs.get('risk_free_rate', 0):.1f}%")
    logger.info(f"Market Risk Premium: {valuation_inputs.get('market_risk_premium', 0):.1f}%")

if __name__ == "__main__":
    test_dcf_valuation()
