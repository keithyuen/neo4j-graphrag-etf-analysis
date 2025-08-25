"""
ETL Service for downloading and processing real ETF holdings data.

This service handles:
- Downloading ETF data from official sources (XLSX for SPY, CSV for others)
- Data parsing and normalization
- Sector classification and mapping
- Loading into Neo4j graph database
"""

import asyncio
import logging
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import os

import httpx
import pandas as pd
import structlog
from neo4j import AsyncSession

from app.services.neo4j_service import Neo4jService

logger = structlog.get_logger()

class ETLService:
    """Service for ETL operations on ETF holdings data."""
    
    # Official ETF data source URLs
    DATA_SOURCES = {
        'SPY': {
            'url': 'https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx',
            'format': 'xlsx',
            'fund_family': 'State Street'
        },
        'QQQ': {
            'url': 'https://www.invesco.com/us/financial-products/etfs/holdings/main/holdings/0?action=download&audienceType=Investor&ticker=QQQ',
            'format': 'csv',
            'fund_family': 'Invesco'
        },
        'IWM': {
            'url': 'https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax?fileType=csv&fileName=IWM_holdings&dataType=fund',
            'format': 'csv',
            'fund_family': 'iShares'
        },
        'IJH': {
            'url': 'https://www.ishares.com/us/products/239763/ishares-core-sp-midcap-etf/1467271812596.ajax?fileType=csv&fileName=IJH_holdings&dataType=fund',
            'format': 'csv',
            'fund_family': 'iShares'
        },
        'IVE': {
            'url': 'https://www.ishares.com/us/products/239728/ishares-sp-500-value-etf/1467271812596.ajax?fileType=csv&fileName=IVE_holdings&dataType=fund',
            'format': 'csv',
            'fund_family': 'iShares'
        },
        'IVW': {
            'url': 'https://www.ishares.com/us/products/239725/ishares-sp-500-growth-etf/1467271812596.ajax?fileType=csv&fileName=IVW_holdings&dataType=fund',
            'format': 'csv',
            'fund_family': 'iShares'
        }
    }
    
    # Basic sector mapping (can be enhanced with external data sources)
    SECTOR_KEYWORDS = {
        'Technology': ['software', 'tech', 'computer', 'internet', 'semiconductor', 'electronics', 'digital', 'cloud'],
        'Health Care': ['health', 'medical', 'pharma', 'biotech', 'drug', 'hospital', 'therapeutic'],
        'Financials': ['bank', 'insurance', 'financial', 'credit', 'investment', 'capital', 'securities'],
        'Consumer Discretionary': ['retail', 'restaurant', 'automotive', 'entertainment', 'media', 'hotel', 'apparel'],
        'Communication Services': ['telecom', 'communication', 'wireless', 'media', 'broadcasting', 'cable'],
        'Industrials': ['industrial', 'manufacturing', 'aerospace', 'defense', 'transportation', 'logistics'],
        'Consumer Staples': ['food', 'beverage', 'household', 'personal care', 'tobacco', 'grocery'],
        'Energy': ['oil', 'gas', 'energy', 'petroleum', 'renewable', 'solar', 'wind'],
        'Utilities': ['utility', 'electric', 'power', 'water', 'gas utility'],
        'Materials': ['chemical', 'mining', 'steel', 'aluminum', 'paper', 'construction material'],
        'Real Estate': ['real estate', 'reit', 'property', 'mortgage', 'commercial real estate']
    }

    def __init__(self, neo4j_service: Neo4jService, cache_dir: str = "/tmp/etf_cache", local_data_dir: str = "/app/etl"):
        self.neo4j_service = neo4j_service
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.local_data_dir = Path(local_data_dir)
        self.cache_ttl_hours = 24  # Cache for 24 hours
        self.external_refresh_days = 7  # Refresh from external sources weekly
        
    async def refresh_all_etfs(self, force: bool = False) -> Dict:
        """Refresh all ETF holdings data with improved error handling."""
        logger.info("Starting ETF data refresh", force=force)
        
        results = {
            'success': True,
            'tickers_processed': [],
            'tickers_failed': [],
            'tickers_cached_fallback': [],
            'failure_details': {},
            'total_companies': 0,
            'cache_stats': {'hits': 0, 'misses': 0}
        }
        
        for ticker in self.DATA_SOURCES.keys():
            try:
                company_count, used_cache = await self.refresh_etf_data(ticker, force)
                results['tickers_processed'].append(ticker)
                results['total_companies'] += company_count
                
                if used_cache:
                    results['cache_stats']['hits'] += 1
                else:
                    results['cache_stats']['misses'] += 1
                    
                logger.info(f"Successfully processed {ticker}", 
                           companies=company_count, 
                           used_cache=used_cache)
                
            except Exception as e:
                logger.error(f"Failed to process {ticker}", error=str(e))
                results['tickers_failed'].append(ticker)
                results['failure_details'][ticker] = str(e)
                
        # Determine overall success - partial success is still considered success
        if len(results['tickers_processed']) > 0:
            results['success'] = True
            if len(results['tickers_failed']) > 0:
                logger.warning(f"Partial success: {len(results['tickers_processed'])}/{len(self.DATA_SOURCES)} ETFs processed successfully")
        else:
            results['success'] = False
            logger.error("Complete failure: No ETFs were processed successfully")
                
        logger.info("ETF data refresh completed", 
                   processed=len(results['tickers_processed']),
                   failed=len(results['tickers_failed']),
                   cached_fallback=len(results['tickers_cached_fallback']),
                   total_companies=results['total_companies'])
        
        return results
    
    async def refresh_etf_data(self, ticker: str, force: bool = False) -> tuple[int, bool]:
        """Refresh data for a specific ETF with priority: local files -> cache -> external download.
        
        Data source priority:
        1. Local files (if fresh enough or force=False)
        2. Cached data (if valid)
        3. External download (with cache fallback on failure)
        
        Returns:
            tuple[int, bool]: (company_count, used_local_or_cache)
        """
        if ticker not in self.DATA_SOURCES:
            raise ValueError(f"Unsupported ticker: {ticker}")
            
        source_config = self.DATA_SOURCES[ticker]
        used_local_or_cache = False
        
        # 1. Try local file first (highest priority)
        if self._has_local_file(ticker) and (not force or not self._should_refresh_from_external(ticker)):
            logger.info(f"Using local file for {ticker}")
            holdings_data = self._parse_local_file(ticker)
            used_local_or_cache = True
            
        # 2. Try cache if no local file or if local file processing fails
        elif not force and self._is_cache_valid(ticker):
            logger.info(f"Using valid cached data for {ticker}")
            holdings_data = self._load_from_cache(ticker)
            used_local_or_cache = True
            
        # 3. Try external download as last resort
        else:
            try:
                logger.info(f"Downloading fresh data from external source for {ticker}")
                holdings_data = await self._download_and_parse(ticker, source_config)
                self._save_to_cache(ticker, holdings_data)
                used_local_or_cache = False
                
            except Exception as download_error:
                logger.warning(f"External download failed for {ticker}: {str(download_error)}")
                
                # Fallback hierarchy: cache -> local file -> error
                if self._has_cached_data(ticker):
                    logger.info(f"Falling back to cached data for {ticker}")
                    holdings_data = self._load_from_cache(ticker)
                    used_local_or_cache = True
                elif self._has_local_file(ticker):
                    logger.info(f"Falling back to local file for {ticker}")
                    holdings_data = self._parse_local_file(ticker)
                    used_local_or_cache = True
                else:
                    logger.error(f"No data source available for {ticker}")
                    raise Exception(f"External download failed and no local/cached data available: {str(download_error)}")
            
        # Load into Neo4j
        company_count = await self._load_to_neo4j(ticker, holdings_data)
        data_source = "local/cached" if used_local_or_cache else "external"
        logger.info(f"Loaded {company_count} companies for {ticker} (source: {data_source})")
        
        return company_count, used_local_or_cache
    
    async def _download_and_parse(self, ticker: str, source_config: Dict) -> List[Dict]:
        """Download and parse ETF holdings data."""
        url = source_config['url']
        file_format = source_config['format']
        
        # Download data with proper SSL configuration
        # Configure client to handle SSL issues in Docker containers
        client_config = {
            'timeout': 60.0,
            'verify': True,  # Default to secure SSL verification
            'headers': {
                'User-Agent': 'Mozilla/5.0 (ETF-GraphRAG-Bot/1.0) ETF Holdings Downloader'
            }
        }
        
        async with httpx.AsyncClient(**client_config) as client:
            logger.info(f"Downloading {ticker} data from {url}")
            
            try:
                response = await client.get(url, follow_redirects=False)
                
                # Handle authentication redirects (like QQQ)
                if response.status_code == 302 and 'login' in response.headers.get('location', '').lower():
                    raise Exception(f"Authentication required - {ticker} data source now requires login")
                    
                response.raise_for_status()
                
            except (httpx.ConnectError, httpx.SSLError) as e:
                # If SSL verification fails, try with relaxed SSL (for development)
                if "SSL" in str(e) or "certificate" in str(e).lower():
                    logger.warning(f"SSL verification failed for {ticker}, retrying with relaxed SSL")
                    async with httpx.AsyncClient(timeout=60.0, verify=False, headers=client_config['headers']) as insecure_client:
                        response = await insecure_client.get(url, follow_redirects=False)
                        
                        # Handle authentication redirects with insecure client
                        if response.status_code == 302 and 'login' in response.headers.get('location', '').lower():
                            raise Exception(f"Authentication required - {ticker} data source now requires login")
                            
                        response.raise_for_status()
                else:
                    raise
            
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=f'.{file_format}', delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
            
        try:
            # Parse based on format
            if file_format == 'xlsx':
                holdings_data = self._parse_xlsx(tmp_path, ticker)
            else:  # csv
                holdings_data = self._parse_csv(tmp_path, ticker)
                
            logger.info(f"Parsed {len(holdings_data)} holdings for {ticker}")
            return holdings_data
            
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
    
    def _parse_xlsx(self, file_path: str, ticker: str) -> List[Dict]:
        """Parse XLSX format (SPY)."""
        try:
            # SPY XLSX has metadata in first 4 rows, headers at row 4, data starts at row 5
            # Read with proper header row
            df = pd.read_excel(file_path, engine='openpyxl', header=4)
            
            logger.info(f"XLSX loaded for {ticker}: {len(df)} rows, columns: {list(df.columns)}")
            
            holdings = []
            
            for _, row in df.iterrows():
                # Skip non-data rows (NaN, summary text, etc.)
                if pd.isna(row.iloc[0]) or str(row.iloc[0]).startswith(('Total', 'Fund', 'Date', 'Past performance', 'Portfolio holdings', 'Before investing')):
                    continue
                    
                # Try to extract standard fields
                holding = self._extract_holding_data(row, ticker, 'xlsx')
                if holding:
                    holdings.append(holding)
                    
            return holdings
            
        except Exception as e:
            logger.error(f"Failed to parse XLSX for {ticker}", error=str(e))
            raise
    
    def _parse_csv(self, file_path: str, ticker: str) -> List[Dict]:
        """Parse CSV format (QQQ, IWM, IJH, IVE, IVW)."""
        try:
            # Handle different CSV formats based on fund family
            source_config = self.DATA_SOURCES[ticker]
            fund_family = source_config['fund_family']
            
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    if fund_family == 'iShares':
                        # iShares files have metadata in first 9 rows, skip them
                        # Also use sep=None to auto-detect separator and handle quoted fields
                        df = pd.read_csv(file_path, encoding=encoding, skiprows=9, sep=None, engine='python')
                    else:
                        # QQQ/Invesco and other formats
                        df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    # If skiprows doesn't work, try different approach
                    if fund_family == 'iShares':
                        try:
                            # Try reading all lines and manually parse
                            with open(file_path, 'r', encoding=encoding) as f:
                                lines = f.readlines()
                            
                            # Skip metadata and get header + data lines  
                            if len(lines) > 10:
                                header_line = lines[9].strip()  # Line 10 (0-indexed)
                                data_lines = lines[10:]        # Data starts from line 11
                                
                                # Create a StringIO object with header + data
                                from io import StringIO
                                csv_content = header_line + '\n' + ''.join(data_lines)
                                df = pd.read_csv(StringIO(csv_content), encoding=encoding)
                                break
                        except:
                            continue
                    else:
                        continue
                    
            if df is None:
                raise ValueError(f"Could not read CSV with any encoding")
                
            logger.info(f"CSV loaded for {ticker}: {len(df)} rows, columns: {list(df.columns)}")
            
            holdings = []
            
            for _, row in df.iterrows():
                # Skip non-data rows
                if pd.isna(row.iloc[0]) or str(row.iloc[0]).startswith(('Total', 'Fund', 'Date', '#')):
                    continue
                    
                holding = self._extract_holding_data(row, ticker, 'csv')
                if holding:
                    holdings.append(holding)
                    
            return holdings
            
        except Exception as e:
            logger.error(f"Failed to parse CSV for {ticker}", error=str(e))
            raise
    
    def _extract_holding_data(self, row: pd.Series, ticker: str, file_format: str) -> Optional[Dict]:
        """Extract standardized holding data from a row."""
        try:
            # Convert row to dict for easier access
            row_dict = row.to_dict()
            
            # Initialize default values
            symbol = None
            name = None
            weight = 0.0
            sector = 'Industrials'  # Default sector
            
            # Handle format-specific parsing
            if file_format == 'invesco_csv' or (ticker == 'QQQ' and 'Holding Ticker' in row_dict):
                # QQQ format: Holding Ticker, Name, Weight (as percentage), Sector
                symbol = str(row_dict.get('Holding Ticker', '')).strip()
                name = str(row_dict.get('Name', '')).strip()
                weight_val = row_dict.get('Weight')
                sector = str(row_dict.get('Sector', '')).strip()
                
                # Parse weight - QQQ weights are percentages, convert to decimals
                weight = self._normalize_weight(weight_val, expected_format='percentage')
                    
            elif file_format == 'ishares_csv' or (ticker in ['IWM', 'IJH', 'IVE', 'IVW'] and 'Ticker' in row_dict):
                # iShares format: Ticker, Name, Sector, Weight (%) etc.
                symbol = str(row_dict.get('Ticker', '')).strip().replace('"', '')
                name = str(row_dict.get('Name', '')).strip().replace('"', '')
                sector = str(row_dict.get('Sector', '')).strip()
                
                # Parse weight - look for Weight (%) column
                weight_val = row_dict.get('Weight (%)', row_dict.get('Weight', row_dict.get('weight', 0)))
                weight = self._normalize_weight(weight_val, expected_format='percentage')
                    
            # Handle State Street/SPY specific format (XLSX) - existing logic
            elif ticker == 'SPY' and 'Ticker' in row_dict and 'Name' in row_dict:
                symbol = str(row_dict.get('Ticker', '')).strip()
                name = str(row_dict.get('Name', '')).strip()
                weight_val = row_dict.get('Weight')
                sector = str(row_dict.get('Sector', '')).strip()
                
                # Parse weight - SPY weights are percentages, convert to decimals
                weight = self._normalize_weight(weight_val, expected_format='percentage')
                    
            else:
                # Generic parsing for other formats
                symbol = None
                name = None
                weight = None
                sector = None
                
                # Find symbol/ticker column
                for col in row_dict.keys():
                    col_lower = str(col).lower()
                    if any(x in col_lower for x in ['symbol', 'ticker', 'identifier']) and 'fund' not in col_lower:
                        symbol = str(row_dict[col]).strip()
                        break
                        
                # Find name column
                for col in row_dict.keys():
                    col_lower = str(col).lower()
                    if any(x in col_lower for x in ['name', 'holding', 'description', 'company']):
                        name = str(row_dict[col]).strip()
                        break
                        
                # Find weight column (as percentage or decimal)
                for col in row_dict.keys():
                    col_lower = str(col).lower()
                    if any(x in col_lower for x in ['weight', 'allocation', 'percent', '%']):
                        weight_val = row_dict[col]
                        weight = self._normalize_weight(weight_val, expected_format='auto')
                        if weight is not None:
                            break
                            
                # Find sector column
                for col in row_dict.keys():
                    col_lower = str(col).lower()
                    if any(x in col_lower for x in ['sector', 'industry', 'classification', 'gics']):
                        sector = str(row_dict[col]).strip()
                        break
            
            # Basic validation
            if not symbol or not name or symbol in ['nan', 'NaN', '']:
                return None
                
            # Clean and validate symbol
            symbol = symbol.upper().replace(' ', '').replace('"', '')
            if len(symbol) > 10 or any(char in symbol for char in ['/', '\\', '(', ')']):
                return None
                
            # Infer sector if not provided or if it's a placeholder
            if not sector or sector in ['nan', 'NaN', '', '-']:
                sector = self._infer_sector(name)
                
            return {
                'symbol': symbol,
                'name': name,
                'weight': weight if weight is not None else 0.0,
                'sector': sector,
                'etf_ticker': ticker
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract holding data", error=str(e), row=str(row)[:100])
            return None
    
    def _infer_sector(self, company_name: str) -> str:
        """Infer sector from company name using keyword matching."""
        name_lower = company_name.lower()
        
        # Score each sector based on keyword matches
        sector_scores = {}
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in name_lower)
            if score > 0:
                sector_scores[sector] = score
                
        # Return the sector with highest score, or default
        if sector_scores:
            return max(sector_scores, key=sector_scores.get)
        else:
            return 'Industrials'  # Default sector for unclassifiable companies
    
    def _normalize_weight(self, weight_val, expected_format: str = 'auto') -> float:
        """
        Normalize weight values to decimal format (0.0 to 1.0).
        
        Args:
            weight_val: Raw weight value from data source
            expected_format: 'percentage', 'decimal', or 'auto' for auto-detection
            
        Returns:
            float: Weight as decimal (0.0 to 1.0), or 0.0 if parsing fails
        """
        try:
            if pd.isna(weight_val) or weight_val in ['', None, '-', 'nan', 'NaN']:
                return 0.0
                
            # Clean and convert to float
            weight_str = str(weight_val).replace('%', '').replace(',', '').strip()
            if not weight_str:
                return 0.0
                
            weight = float(weight_str)
            
            # Handle negative weights (shouldn't happen but be safe)
            if weight < 0:
                logger.warning(f"Negative weight found: {weight_val}, setting to 0")
                return 0.0
            
            # Auto-detect format if not specified
            if expected_format == 'auto':
                # If weight > 1, assume it's a percentage
                # If weight <= 1, assume it's already decimal
                if weight > 1:
                    expected_format = 'percentage'
                else:
                    expected_format = 'decimal'
            
            # Convert based on expected format
            if expected_format == 'percentage':
                # Convert percentage to decimal (e.g., 9.910 -> 0.0991)
                weight = weight / 100
            elif expected_format == 'decimal':
                # Already in decimal format, no conversion needed
                pass
            else:
                raise ValueError(f"Unknown expected_format: {expected_format}")
            
            # Validation: ETF weights should be reasonable (0% to 50% max)
            if weight > 0.5:  # > 50%
                logger.warning(f"Unusually high weight detected: {weight:.4f} ({weight*100:.2f}%), "
                             f"original value: {weight_val}")
                # Don't cap the weight, just log the warning for investigation
                
            return weight
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to normalize weight: {weight_val}, error: {str(e)}")
            return 0.0
    
    async def _load_to_neo4j(self, ticker: str, holdings_data: List[Dict]) -> int:
        """Load holdings data into Neo4j graph."""
        logger.info(f"Loading {len(holdings_data)} holdings for {ticker} into Neo4j")
        
        # Create/update ETF node first
        etf_names = {
            'SPY': 'SPDR S&P 500 ETF',
            'QQQ': 'Invesco QQQ Trust',
            'IWM': 'iShares Russell 2000 ETF',
            'IJH': 'iShares Core S&P Mid-Cap ETF',
            'IVE': 'iShares S&P 500 Value ETF',
            'IVW': 'iShares S&P 500 Growth ETF'
        }
        
        await self.neo4j_service.execute_query(
            """
            MERGE (e:ETF {ticker: $ticker})
            SET e.name = $name,
                e.last_updated = datetime()
            """,
            {
                'ticker': ticker,
                'name': etf_names.get(ticker, f'{ticker} ETF')
            }
        )
        logger.info(f"Created/updated ETF node for {ticker}")
        
        # Clear existing HOLDS relationships for this ETF to prevent duplicates
        await self.neo4j_service.execute_query(
            """
            MATCH (e:ETF {ticker: $ticker})-[h:HOLDS]->()
            DELETE h
            """,
            {'ticker': ticker}
        )
        logger.info(f"Cleared existing HOLDS relationships for {ticker}")
        
        # Create companies and sectors
        companies_created = 0
        sectors_created = set()
        
        for holding in holdings_data:
            try:
                # Create/update company
                await self.neo4j_service.execute_query(
                    """
                    MERGE (c:Company {symbol: $symbol})
                    SET c.name = $name,
                        c.last_updated = datetime()
                    """,
                    {
                        'symbol': holding['symbol'],
                        'name': holding['name']
                    }
                )
                companies_created += 1
                
                # Create/update sector
                sector_name = holding['sector']
                if sector_name not in sectors_created:
                    await self.neo4j_service.execute_query(
                        """
                        MERGE (s:Sector {name: $sector_name})
                        SET s.last_updated = datetime()
                        """,
                        {'sector_name': sector_name}
                    )
                    sectors_created.add(sector_name)
                
                # Create company-sector relationship (replace any existing)
                await self.neo4j_service.execute_query(
                    """
                    MATCH (c:Company {symbol: $symbol})
                    OPTIONAL MATCH (c)-[old_rel:IN_SECTOR]->()
                    DELETE old_rel
                    WITH c
                    MATCH (s:Sector {name: $sector_name})
                    MERGE (c)-[:IN_SECTOR]->(s)
                    """,
                    {
                        'symbol': holding['symbol'],
                        'sector_name': sector_name
                    }
                )
                
                # Create ETF-company holding relationship
                await self.neo4j_service.execute_query(
                    """
                    MATCH (e:ETF {ticker: $ticker})
                    MATCH (c:Company {symbol: $symbol})
                    MERGE (e)-[h:HOLDS]->(c)
                    SET h.weight = $weight,
                        h.last_updated = datetime()
                    """,
                    {
                        'ticker': ticker,
                        'symbol': holding['symbol'],
                        'weight': holding['weight']
                    }
                )
                
            except Exception as e:
                logger.warning(f"Failed to load holding {holding['symbol']}", error=str(e))
                continue
                
        logger.info(f"Loaded {companies_created} companies, {len(sectors_created)} sectors for {ticker}")
        
        # Data integrity check - verify total weights are reasonable
        result = await self.neo4j_service.execute_query(
            """
            MATCH (e:ETF {ticker: $ticker})-[h:HOLDS]->()
            RETURN sum(h.weight) as total_weight, count(h) as total_holdings
            """,
            {'ticker': ticker}
        )
        
        if result and len(result) > 0:
            total_weight = result[0].get('total_weight', 0)
            total_holdings = result[0].get('total_holdings', 0)
            total_percent = total_weight * 100
            
            logger.info(f"Data integrity check for {ticker}: {total_holdings} holdings, "
                       f"total weight: {total_weight:.4f} ({total_percent:.2f}%)")
            
            # Warn if total weights are unreasonable
            if total_percent < 95 or total_percent > 105:
                logger.warning(f"ETF {ticker} total weight is {total_percent:.2f}% - "
                             f"expected ~100%. This may indicate data quality issues.")
        
        return companies_created
    
    def _is_cache_valid(self, ticker: str) -> bool:
        """Check if cached data is still valid."""
        cache_file = self.cache_dir / f"{ticker}_holdings.json"
        if not cache_file.exists():
            return False
            
        # Check timestamp
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        expiry_time = datetime.now() - timedelta(hours=self.cache_ttl_hours)
        
        return file_time > expiry_time
    
    def _has_cached_data(self, ticker: str) -> bool:
        """Check if cached data exists (regardless of TTL)."""
        cache_file = self.cache_dir / f"{ticker}_holdings.json"
        return cache_file.exists()
    
    def _load_from_cache(self, ticker: str) -> List[Dict]:
        """Load holdings data from cache."""
        cache_file = self.cache_dir / f"{ticker}_holdings.json"
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    def _save_to_cache(self, ticker: str, holdings_data: List[Dict]) -> None:
        """Save holdings data to cache."""
        cache_file = self.cache_dir / f"{ticker}_holdings.json"
        with open(cache_file, 'w') as f:
            json.dump(holdings_data, f, indent=2)
        
        logger.info(f"Cached {len(holdings_data)} holdings for {ticker}")
    
    def _has_local_file(self, ticker: str) -> bool:
        """Check if local ETF file exists."""
        excel_file = self.local_data_dir / f"{ticker}.xlsx"
        csv_file = self.local_data_dir / f"{ticker}.csv"
        return excel_file.exists() or csv_file.exists()
    
    def _should_refresh_from_external(self, ticker: str) -> bool:
        """Check if local file is old enough to warrant external refresh (weekly)."""
        excel_file = self.local_data_dir / f"{ticker}.xlsx"
        csv_file = self.local_data_dir / f"{ticker}.csv"
        
        local_file = excel_file if excel_file.exists() else csv_file
        if not local_file.exists():
            return True
            
        # Check if file is older than weekly refresh threshold
        file_age = datetime.now() - datetime.fromtimestamp(local_file.stat().st_mtime)
        return file_age.days >= self.external_refresh_days
    
    def _parse_local_file(self, ticker: str) -> List[Dict]:
        """Parse local ETF file (Excel or CSV)."""
        excel_file = self.local_data_dir / f"{ticker}.xlsx"
        csv_file = self.local_data_dir / f"{ticker}.csv"
        
        if excel_file.exists():
            logger.info(f"Parsing local Excel file for {ticker}")
            return self._parse_xlsx(str(excel_file), ticker)
        elif csv_file.exists():
            logger.info(f"Parsing local CSV file for {ticker}")
            return self._parse_csv(str(csv_file), ticker)
        else:
            raise FileNotFoundError(f"No local file found for {ticker}")
    
    def _parse_csv(self, file_path: str, ticker: str) -> List[Dict]:
        """Parse CSV file with ticker-specific format handling."""
        holdings = []
        
        # Handle special cases first (iShares files with complex headers)
        if ticker in ['IWM', 'IJH', 'IVE', 'IVW']:
            return self._parse_ishares_csv(file_path, ticker)
        
        try:
            df = pd.read_csv(file_path)
            
            # Handle different CSV formats per ETF
            if ticker == 'QQQ':
                # QQQ format: Fund Ticker,Security Identifier,Holding Ticker,Shares/Par Value,MarketValue,Weight,Name,Class of Shares,Sector,Date
                for _, row in df.iterrows():
                    holding_data = self._extract_holding_data(row, ticker, 'invesco_csv')
                    if holding_data:
                        holdings.append(holding_data)
                        
            else:
                # Generic CSV format
                for _, row in df.iterrows():
                    holding_data = self._extract_holding_data(row, ticker, 'generic_csv')
                    if holding_data:
                        holdings.append(holding_data)
            
            logger.info(f"Parsed {len(holdings)} holdings from {ticker} CSV file")
            return holdings
            
        except Exception as e:
            logger.error(f"Failed to parse CSV file for {ticker}: {str(e)}")
            raise
    
    def _parse_ishares_csv(self, file_path: str, ticker: str) -> List[Dict]:
        """Parse iShares CSV files with complex headers and quoted fields."""
        holdings = []
        
        try:
            # Try robust pandas parsing first
            df = pd.read_csv(
                file_path, 
                skiprows=9,  # Skip header info
                encoding='utf-8-sig',  # Handle BOM
                quotechar='"',  # Handle quoted fields
                skipinitialspace=True,  # Handle spaces after commas
                on_bad_lines='skip'  # Skip problematic lines
            )
            logger.info(f"Standard pandas parsing succeeded for {ticker}: {len(df)} rows")
            
            for _, row in df.iterrows():
                holding_data = self._extract_holding_data(row, ticker, 'ishares_csv')
                if holding_data:
                    holdings.append(holding_data)
                    
        except Exception as e:
            logger.warning(f"Standard CSV parsing failed for {ticker}: {str(e)}, trying manual parsing")
            
            # Manual parsing fallback for problematic iShares files
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            # Skip header lines (first 10 lines)
            data_lines = lines[10:]  # Line 0-9 are headers, line 10+ are data
            
            for line_num, line in enumerate(data_lines, start=11):
                if line.strip():  # Skip empty lines
                    try:
                        # Manual CSV parsing for quoted fields
                        fields = []
                        current_field = ""
                        in_quotes = False
                        
                        for char in line:
                            if char == '"':
                                in_quotes = not in_quotes
                            elif char == ',' and not in_quotes:
                                fields.append(current_field.strip())
                                current_field = ""
                            else:
                                current_field += char
                                
                        # Add the last field
                        if current_field:
                            fields.append(current_field.strip())
                        
                        # Create a mock row for processing
                        if len(fields) >= 6:  # Minimum required fields
                            row_data = {
                                'Ticker': fields[0].replace('"', ''),
                                'Name': fields[1].replace('"', ''),
                                'Sector': fields[2].replace('"', ''),
                                'Asset Class': fields[3].replace('"', '') if len(fields) > 3 else '',
                                'Market Value': fields[4].replace('"', '') if len(fields) > 4 else '',
                                'Weight (%)': fields[5].replace('"', '') if len(fields) > 5 else '0'
                            }
                            
                            # Convert to pandas Series for compatibility
                            row_series = pd.Series(row_data)
                            holding_data = self._extract_holding_data(row_series, ticker, 'ishares_csv')
                            if holding_data:
                                holdings.append(holding_data)
                                
                    except Exception as line_error:
                        logger.debug(f"Skipped problematic line {line_num} in {ticker}: {str(line_error)}")
                        continue
            
            logger.info(f"Manual parsing completed for {ticker}: {len(holdings)} holdings extracted")
        
        return holdings