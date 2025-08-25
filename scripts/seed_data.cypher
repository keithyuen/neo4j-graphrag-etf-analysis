// ETF GraphRAG Seed Data
// This file creates the initial seed data for the ETF GraphRAG system

// =============================================================================
// CORE SECTORS (Primary Categories)
// =============================================================================

MERGE (tech:Sector {name: "Technology", classification: "GICS"})
SET tech.description = "Information Technology sector including software, hardware, and tech services"

MERGE (finance:Sector {name: "Financials", classification: "GICS"})
SET finance.description = "Financial services including banks, insurance, and investment companies"

MERGE (healthcare:Sector {name: "Health Care", classification: "GICS"})
SET healthcare.description = "Healthcare equipment, services, pharmaceuticals, and biotechnology"

MERGE (consumer_disc:Sector {name: "Consumer Discretionary", classification: "GICS"})
SET consumer_disc.description = "Non-essential consumer goods and services"

MERGE (comm_services:Sector {name: "Communication Services", classification: "GICS"})
SET comm_services.description = "Telecommunications and media companies"

MERGE (industrials:Sector {name: "Industrials", classification: "GICS"})
SET industrials.description = "Manufacturing, transportation, and infrastructure companies"

MERGE (consumer_staples:Sector {name: "Consumer Staples", classification: "GICS"})
SET consumer_staples.description = "Essential consumer goods and services"

MERGE (energy:Sector {name: "Energy", classification: "GICS"})
SET energy.description = "Oil, gas, and renewable energy companies"

MERGE (utilities:Sector {name: "Utilities", classification: "GICS"})
SET utilities.description = "Electric, gas, and water utilities"

MERGE (materials:Sector {name: "Materials", classification: "GICS"})
SET materials.description = "Basic materials and chemical companies"

MERGE (real_estate:Sector {name: "Real Estate", classification: "GICS"})
SET real_estate.description = "Real estate investment trusts and real estate companies";

// =============================================================================
// MAJOR ETFs (Target ETFs for Analysis)
// =============================================================================

MERGE (spy:ETF {ticker: "SPY"})
SET spy.name = "SPDR S&P 500 ETF Trust",
    spy.description = "Tracks the S&P 500 Index",
    spy.expense_ratio = 0.0945,
    spy.inception_date = date("1993-01-22"),
    spy.fund_family = "State Street",
    spy.total_assets = 400000000000.0,
    spy.data_source = "spdr.com"

MERGE (qqq:ETF {ticker: "QQQ"})
SET qqq.name = "Invesco QQQ Trust",
    qqq.description = "Tracks the Nasdaq-100 Index",
    qqq.expense_ratio = 0.20,
    qqq.inception_date = date("1999-03-10"),
    qqq.fund_family = "Invesco",
    qqq.total_assets = 180000000000.0,
    qqq.data_source = "invesco.com"

MERGE (iwm:ETF {ticker: "IWM"})
SET iwm.name = "iShares Russell 2000 ETF",
    iwm.description = "Tracks the Russell 2000 Index",
    iwm.expense_ratio = 0.19,
    iwm.inception_date = date("2000-05-22"),
    iwm.fund_family = "iShares",
    iwm.total_assets = 60000000000.0,
    iwm.data_source = "ishares.com"

MERGE (ijh:ETF {ticker: "IJH"})
SET ijh.name = "iShares Core S&P Mid-Cap ETF",
    ijh.description = "Tracks the S&P MidCap 400 Index",
    ijh.expense_ratio = 0.05,
    ijh.inception_date = date("2000-05-22"),
    ijh.fund_family = "iShares",
    ijh.total_assets = 70000000000.0,
    ijh.data_source = "ishares.com"

MERGE (ive:ETF {ticker: "IVE"})
SET ive.name = "iShares S&P 500 Value ETF",
    ive.description = "Tracks the S&P 500 Value Index",
    ive.expense_ratio = 0.18,
    ive.inception_date = date("2000-05-22"),
    ive.fund_family = "iShares",
    ive.total_assets = 20000000000.0,
    ive.data_source = "ishares.com"

MERGE (ivw:ETF {ticker: "IVW"})
SET ivw.name = "iShares S&P 500 Growth ETF",
    ivw.description = "Tracks the S&P 500 Growth Index",
    ivw.expense_ratio = 0.18,
    ivw.inception_date = date("2000-05-22"),
    ivw.fund_family = "iShares",
    ivw.total_assets = 30000000000.0,
    ivw.data_source = "ishares.com";

// =============================================================================
// SAMPLE COMPANIES (Major Holdings)
// =============================================================================

MERGE (aapl:Company {symbol: "AAPL"})
SET aapl.name = "Apple Inc.",
    aapl.industry = "Technology Hardware & Equipment",
    aapl.market_cap = 3000000000000.0,
    aapl.country = "United States"

MERGE (msft:Company {symbol: "MSFT"})
SET msft.name = "Microsoft Corporation",
    msft.industry = "Software & Services",
    msft.market_cap = 2800000000000.0,
    msft.country = "United States"

MERGE (googl:Company {symbol: "GOOGL"})
SET googl.name = "Alphabet Inc.",
    googl.industry = "Software & Services",
    googl.market_cap = 1700000000000.0,
    googl.country = "United States"

MERGE (amzn:Company {symbol: "AMZN"})
SET amzn.name = "Amazon.com Inc.",
    amzn.industry = "Retailing",
    amzn.market_cap = 1500000000000.0,
    amzn.country = "United States"

MERGE (nvda:Company {symbol: "NVDA"})
SET nvda.name = "NVIDIA Corporation",
    nvda.industry = "Semiconductors & Semiconductor Equipment",
    nvda.market_cap = 1800000000000.0,
    nvda.country = "United States"

MERGE (tsla:Company {symbol: "TSLA"})
SET tsla.name = "Tesla Inc.",
    tsla.industry = "Automobiles & Components",
    tsla.market_cap = 800000000000.0,
    tsla.country = "United States"

MERGE (meta:Company {symbol: "META"})
SET meta.name = "Meta Platforms Inc.",
    meta.industry = "Software & Services",
    meta.market_cap = 900000000000.0,
    meta.country = "United States"

MERGE (brk_b:Company {symbol: "BRK.B"})
SET brk_b.name = "Berkshire Hathaway Inc.",
    brk_b.industry = "Insurance",
    brk_b.market_cap = 800000000000.0,
    brk_b.country = "United States"

MERGE (jpm:Company {symbol: "JPM"})
SET jpm.name = "JPMorgan Chase & Co.",
    jpm.industry = "Banks",
    jpm.market_cap = 500000000000.0,
    jpm.country = "United States"

MERGE (jnj:Company {symbol: "JNJ"})
SET jnj.name = "Johnson & Johnson",
    jnj.industry = "Pharmaceuticals, Biotechnology & Life Sciences",
    jnj.market_cap = 450000000000.0,
    jnj.country = "United States";

// =============================================================================
// COMPANY-SECTOR RELATIONSHIPS
// =============================================================================

MATCH (aapl:Company {symbol: "AAPL"}), (tech:Sector {name: "Technology"})
MERGE (aapl)-[:IN_SECTOR]->(tech)

MATCH (msft:Company {symbol: "MSFT"}), (tech:Sector {name: "Technology"})
MERGE (msft)-[:IN_SECTOR]->(tech)

MATCH (googl:Company {symbol: "GOOGL"}), (comm:Sector {name: "Communication Services"})
MERGE (googl)-[:IN_SECTOR]->(comm)

MATCH (amzn:Company {symbol: "AMZN"}), (disc:Sector {name: "Consumer Discretionary"})
MERGE (amzn)-[:IN_SECTOR]->(disc)

MATCH (nvda:Company {symbol: "NVDA"}), (tech:Sector {name: "Technology"})
MERGE (nvda)-[:IN_SECTOR]->(tech)

MATCH (tsla:Company {symbol: "TSLA"}), (disc:Sector {name: "Consumer Discretionary"})
MERGE (tsla)-[:IN_SECTOR]->(disc)

MATCH (meta:Company {symbol: "META"}), (comm:Sector {name: "Communication Services"})
MERGE (meta)-[:IN_SECTOR]->(comm)

MATCH (brk_b:Company {symbol: "BRK.B"}), (fin:Sector {name: "Financials"})
MERGE (brk_b)-[:IN_SECTOR]->(fin)

MATCH (jpm:Company {symbol: "JPM"}), (fin:Sector {name: "Financials"})
MERGE (jpm)-[:IN_SECTOR]->(fin)

MATCH (jnj:Company {symbol: "JNJ"}), (health:Sector {name: "Health Care"})
MERGE (jnj)-[:IN_SECTOR]->(health);

// =============================================================================
// SAMPLE ETF HOLDINGS (Representative Data)
// =============================================================================

// SPY Holdings (top holdings)
MATCH (spy:ETF {ticker: "SPY"}), (aapl:Company {symbol: "AAPL"})
MERGE (spy)-[:HOLDS {weight: 0.072, shares: 165000000, value: 28800000000.0}]->(aapl)

MATCH (spy:ETF {ticker: "SPY"}), (msft:Company {symbol: "MSFT"})
MERGE (spy)-[:HOLDS {weight: 0.065, shares: 75000000, value: 26000000000.0}]->(msft)

MATCH (spy:ETF {ticker: "SPY"}), (googl:Company {symbol: "GOOGL"})
MERGE (spy)-[:HOLDS {weight: 0.042, shares: 12000000, value: 16800000000.0}]->(googl)

MATCH (spy:ETF {ticker: "SPY"}), (amzn:Company {symbol: "AMZN"})
MERGE (spy)-[:HOLDS {weight: 0.038, shares: 10000000, value: 15200000000.0}]->(amzn)

MATCH (spy:ETF {ticker: "SPY"}), (nvda:Company {symbol: "NVDA"})
MERGE (spy)-[:HOLDS {weight: 0.035, shares: 15000000, value: 14000000000.0}]->(nvda)

// QQQ Holdings (tech-heavy)
MATCH (qqq:ETF {ticker: "QQQ"}), (aapl:Company {symbol: "AAPL"})
MERGE (qqq)-[:HOLDS {weight: 0.135, shares: 85000000, value: 24300000000.0}]->(aapl)

MATCH (qqq:ETF {ticker: "QQQ"}), (msft:Company {symbol: "MSFT"})
MERGE (qqq)-[:HOLDS {weight: 0.120, shares: 42000000, value: 21600000000.0}]->(msft)

MATCH (qqq:ETF {ticker: "QQQ"}), (googl:Company {symbol: "GOOGL"})
MERGE (qqq)-[:HOLDS {weight: 0.075, shares: 8000000, value: 13500000000.0}]->(googl)

MATCH (qqq:ETF {ticker: "QQQ"}), (amzn:Company {symbol: "AMZN"})
MERGE (qqq)-[:HOLDS {weight: 0.055, shares: 6000000, value: 9900000000.0}]->(amzn)

MATCH (qqq:ETF {ticker: "QQQ"}), (nvda:Company {symbol: "NVDA"})
MERGE (qqq)-[:HOLDS {weight: 0.065, shares: 9000000, value: 11700000000.0}]->(nvda)

MATCH (qqq:ETF {ticker: "QQQ"}), (meta:Company {symbol: "META"})
MERGE (qqq)-[:HOLDS {weight: 0.045, shares: 5000000, value: 8100000000.0}]->(meta);

// =============================================================================
// GRAPHRAG SYSTEM INTENTS
// =============================================================================

MERGE (etf_exposure:Intent {key: "etf_exposure_to_company"})
SET etf_exposure.type = "analysis",
    etf_exposure.description = "Find specific ETF's exposure to a particular company",
    etf_exposure.example_query = "What is SPY's exposure to AAPL?",
    etf_exposure.confidence_threshold = 0.8

MERGE (company_in_etfs:Intent {key: "company_in_which_etfs"})
SET company_in_etfs.type = "analysis",
    company_in_etfs.description = "Find which ETFs hold a specific company",
    company_in_etfs.example_query = "Which ETFs hold Apple?",
    company_in_etfs.confidence_threshold = 0.8

MERGE (etf_overlap:Intent {key: "etf_overlap_analysis"})
SET etf_overlap.type = "comparison",
    etf_overlap.description = "Compare overlap between two ETFs",
    etf_overlap.example_query = "What is the overlap between SPY and QQQ?",
    etf_overlap.confidence_threshold = 0.75

MERGE (sector_exposure:Intent {key: "etf_sector_exposure"})
SET sector_exposure.type = "analysis",
    sector_exposure.description = "Analyze ETF's exposure to specific sectors",
    sector_exposure.example_query = "What is QQQ's technology sector exposure?",
    sector_exposure.confidence_threshold = 0.8

MERGE (top_holdings:Intent {key: "etf_top_holdings"})
SET top_holdings.type = "listing",
    top_holdings.description = "List top holdings of an ETF",
    top_holdings.example_query = "What are SPY's top 10 holdings?",
    top_holdings.confidence_threshold = 0.85

MERGE (sector_companies:Intent {key: "sector_companies_in_etf"})
SET sector_companies.type = "listing",
    sector_companies.description = "List companies in a specific sector within an ETF",
    sector_companies.example_query = "Which technology companies are in SPY?",
    sector_companies.confidence_threshold = 0.8

MERGE (general_query:Intent {key: "general_etf_query"})
SET general_query.type = "general",
    general_query.description = "General ETF-related queries that don't fit specific patterns",
    general_query.example_query = "Tell me about ETF diversification",
    general_query.confidence_threshold = 0.6;

// =============================================================================
// GRAPHRAG ENTITIES (ETF and Company Entities)
// =============================================================================

// ETF Entities
MERGE (spy_entity:Entity {id: "etf_spy", type: "ETF", symbol: "SPY"})
SET spy_entity.name = "SPY",
    spy_entity.description = "SPDR S&P 500 ETF Trust"

MERGE (qqq_entity:Entity {id: "etf_qqq", type: "ETF", symbol: "QQQ"})
SET qqq_entity.name = "QQQ", 
    qqq_entity.description = "Invesco QQQ Trust"

MERGE (iwm_entity:Entity {id: "etf_iwm", type: "ETF", symbol: "IWM"})
SET iwm_entity.name = "IWM",
    iwm_entity.description = "iShares Russell 2000 ETF"

MERGE (ijh_entity:Entity {id: "etf_ijh", type: "ETF", symbol: "IJH"})
SET ijh_entity.name = "IJH",
    ijh_entity.description = "iShares Core S&P Mid-Cap ETF"

MERGE (ive_entity:Entity {id: "etf_ive", type: "ETF", symbol: "IVE"})
SET ive_entity.name = "IVE",
    ive_entity.description = "iShares S&P 500 Value ETF"

MERGE (ivw_entity:Entity {id: "etf_ivw", type: "ETF", symbol: "IVW"})
SET ivw_entity.name = "IVW",
    ivw_entity.description = "iShares S&P 500 Growth ETF"

// Company Entities
MERGE (aapl_entity:Entity {id: "company_aapl", type: "Company", symbol: "AAPL"})
SET aapl_entity.name = "AAPL",
    aapl_entity.description = "Apple Inc."

MERGE (msft_entity:Entity {id: "company_msft", type: "Company", symbol: "MSFT"})
SET msft_entity.name = "MSFT",
    msft_entity.description = "Microsoft Corporation"

MERGE (googl_entity:Entity {id: "company_googl", type: "Company", symbol: "GOOGL"})
SET googl_entity.name = "GOOGL",
    googl_entity.description = "Alphabet Inc."

MERGE (amzn_entity:Entity {id: "company_amzn", type: "Company", symbol: "AMZN"})
SET amzn_entity.name = "AMZN",
    amzn_entity.description = "Amazon.com Inc."

MERGE (nvda_entity:Entity {id: "company_nvda", type: "Company", symbol: "NVDA"})
SET nvda_entity.name = "NVDA",
    nvda_entity.description = "NVIDIA Corporation"

// Sector Entities
MERGE (tech_entity:Entity {id: "sector_technology", type: "Sector", symbol: "TECH"})
SET tech_entity.name = "Technology",
    tech_entity.description = "Information Technology sector"

MERGE (finance_entity:Entity {id: "sector_financials", type: "Sector", symbol: "FIN"})
SET finance_entity.name = "Financials",
    finance_entity.description = "Financial services sector"

MERGE (health_entity:Entity {id: "sector_healthcare", type: "Sector", symbol: "HEALTH"})
SET health_entity.name = "Health Care",
    health_entity.description = "Healthcare sector";

// =============================================================================
// GRAPHRAG TERMS (Synonyms and Aliases)
// =============================================================================

// ETF Terms
MERGE (spy_term1:Term {text: "SPY", norm: "spy"})
MERGE (spy_term2:Term {text: "S&P 500 ETF", norm: "s&p 500 etf"})
MERGE (spy_term3:Term {text: "SPDR", norm: "spdr"})

MERGE (qqq_term1:Term {text: "QQQ", norm: "qqq"})
MERGE (qqq_term2:Term {text: "Nasdaq 100 ETF", norm: "nasdaq 100 etf"})
MERGE (qqq_term3:Term {text: "Invesco QQQ", norm: "invesco qqq"})

// Company Terms
MERGE (aapl_term1:Term {text: "AAPL", norm: "aapl"})
MERGE (aapl_term2:Term {text: "Apple", norm: "apple"})
MERGE (aapl_term3:Term {text: "Apple Inc", norm: "apple inc"})

MERGE (msft_term1:Term {text: "MSFT", norm: "msft"})
MERGE (msft_term2:Term {text: "Microsoft", norm: "microsoft"})
MERGE (msft_term3:Term {text: "Microsoft Corporation", norm: "microsoft corporation"})

MERGE (googl_term1:Term {text: "GOOGL", norm: "googl"})
MERGE (googl_term2:Term {text: "Google", norm: "google"})
MERGE (googl_term3:Term {text: "Alphabet", norm: "alphabet"})

// Sector Terms
MERGE (tech_term1:Term {text: "Technology", norm: "technology"})
MERGE (tech_term2:Term {text: "Tech", norm: "tech"})
MERGE (tech_term3:Term {text: "IT", norm: "it"})

MERGE (finance_term1:Term {text: "Financials", norm: "financials"})
MERGE (finance_term2:Term {text: "Finance", norm: "finance"})
MERGE (finance_term3:Term {text: "Financial Services", norm: "financial services"});

// =============================================================================
// GRAPHRAG TERM-ENTITY RELATIONSHIPS
// =============================================================================

// SPY synonyms
MATCH (spy_term1:Term {norm: "spy"}), (spy_entity:Entity {id: "etf_spy"})
MERGE (spy_term1)-[:SYNONYMOUS_WITH {confidence: 1.0}]->(spy_entity)

MATCH (spy_term2:Term {norm: "s&p 500 etf"}), (spy_entity:Entity {id: "etf_spy"})
MERGE (spy_term2)-[:SYNONYMOUS_WITH {confidence: 0.95}]->(spy_entity)

MATCH (spy_term3:Term {norm: "spdr"}), (spy_entity:Entity {id: "etf_spy"})
MERGE (spy_term3)-[:SYNONYMOUS_WITH {confidence: 0.9}]->(spy_entity)

// QQQ synonyms
MATCH (qqq_term1:Term {norm: "qqq"}), (qqq_entity:Entity {id: "etf_qqq"})
MERGE (qqq_term1)-[:SYNONYMOUS_WITH {confidence: 1.0}]->(qqq_entity)

MATCH (qqq_term2:Term {norm: "nasdaq 100 etf"}), (qqq_entity:Entity {id: "etf_qqq"})
MERGE (qqq_term2)-[:SYNONYMOUS_WITH {confidence: 0.95}]->(qqq_entity)

// Apple synonyms
MATCH (aapl_term1:Term {norm: "aapl"}), (aapl_entity:Entity {id: "company_aapl"})
MERGE (aapl_term1)-[:SYNONYMOUS_WITH {confidence: 1.0}]->(aapl_entity)

MATCH (aapl_term2:Term {norm: "apple"}), (aapl_entity:Entity {id: "company_aapl"})
MERGE (aapl_term2)-[:SYNONYMOUS_WITH {confidence: 0.98}]->(aapl_entity)

// Microsoft synonyms
MATCH (msft_term1:Term {norm: "msft"}), (msft_entity:Entity {id: "company_msft"})
MERGE (msft_term1)-[:SYNONYMOUS_WITH {confidence: 1.0}]->(msft_entity)

MATCH (msft_term2:Term {norm: "microsoft"}), (msft_entity:Entity {id: "company_msft"})
MERGE (msft_term2)-[:SYNONYMOUS_WITH {confidence: 0.98}]->(msft_entity)

// Technology sector synonyms
MATCH (tech_term1:Term {norm: "technology"}), (tech_entity:Entity {id: "sector_technology"})
MERGE (tech_term1)-[:SYNONYMOUS_WITH {confidence: 1.0}]->(tech_entity)

MATCH (tech_term2:Term {norm: "tech"}), (tech_entity:Entity {id: "sector_technology"})
MERGE (tech_term2)-[:SYNONYMOUS_WITH {confidence: 0.95}]->(tech_entity);

// =============================================================================
// INTENT-ENTITY REQUIREMENTS
// =============================================================================

// ETF exposure to company requires ETF and Company entities
MATCH (etf_exposure:Intent {key: "etf_exposure_to_company"})
MATCH (etf_entity:Entity {type: "ETF"})
MERGE (etf_exposure)-[:REQUIRES {param_name: "ticker", entity_type: "ETF"}]->(etf_entity)

MATCH (etf_exposure:Intent {key: "etf_exposure_to_company"})
MATCH (company_entity:Entity {type: "Company"})
MERGE (etf_exposure)-[:REQUIRES {param_name: "symbol", entity_type: "Company"}]->(company_entity)

// Company in ETFs requires Company entity
MATCH (company_in_etfs:Intent {key: "company_in_which_etfs"})
MATCH (company_entity:Entity {type: "Company"})
MERGE (company_in_etfs)-[:REQUIRES {param_name: "symbol", entity_type: "Company"}]->(company_entity)

// ETF overlap requires two ETF entities
MATCH (etf_overlap:Intent {key: "etf_overlap_analysis"})
MATCH (etf_entity:Entity {type: "ETF"})
MERGE (etf_overlap)-[:REQUIRES {param_name: "ticker1", entity_type: "ETF"}]->(etf_entity)
MERGE (etf_overlap)-[:REQUIRES {param_name: "ticker2", entity_type: "ETF"}]->(etf_entity)

// Sector exposure requires ETF and Sector entities
MATCH (sector_exposure:Intent {key: "etf_sector_exposure"})
MATCH (etf_entity:Entity {type: "ETF"})
MERGE (sector_exposure)-[:REQUIRES {param_name: "ticker", entity_type: "ETF"}]->(etf_entity)

MATCH (sector_exposure:Intent {key: "etf_sector_exposure"})
MATCH (sector_entity:Entity {type: "Sector"})
MERGE (sector_exposure)-[:REQUIRES {param_name: "sector", entity_type: "Sector"}]->(sector_entity);

// =============================================================================
// SAMPLE DOCCHUNKS (Knowledge Base)
// =============================================================================

MERGE (doc1:DocChunk {
  id: "etf_basics_001",
  type: "educational",
  title: "ETF Basics",
  content: "An Exchange-Traded Fund (ETF) is an investment fund that tracks an index, commodity, bonds, or basket of assets. ETFs trade on stock exchanges like individual stocks and offer diversification benefits with lower costs than mutual funds."
})

MERGE (doc2:DocChunk {
  id: "spy_overview_001", 
  type: "fund_info",
  title: "SPY ETF Overview",
  content: "The SPDR S&P 500 ETF Trust (SPY) is one of the largest and most liquid ETFs, tracking the S&P 500 Index. It provides exposure to 500 large-cap U.S. companies across all sectors with expense ratio of 0.0945%."
})

MERGE (doc3:DocChunk {
  id: "qqq_overview_001",
  type: "fund_info", 
  title: "QQQ ETF Overview",
  content: "The Invesco QQQ Trust (QQQ) tracks the Nasdaq-100 Index, focusing on the 100 largest non-financial companies listed on Nasdaq. It's heavily weighted in technology stocks with companies like Apple, Microsoft, and Google."
})

MERGE (doc4:DocChunk {
  id: "etf_overlap_001",
  type: "educational",
  title: "ETF Overlap Analysis",
  content: "ETF overlap occurs when multiple ETFs hold the same underlying securities. Understanding overlap is crucial for portfolio diversification. High overlap between ETFs can lead to concentration risk rather than diversification benefits."
})

MERGE (doc5:DocChunk {
  id: "sector_allocation_001",
  type: "educational", 
  title: "Sector Allocation in ETFs",
  content: "Sector allocation shows how an ETF's holdings are distributed across different industry sectors. Technology, Financials, and Healthcare are typically the largest sectors in broad market ETFs like SPY."
});

// =============================================================================
// SAMPLE DATA VERIFICATION
// =============================================================================

// Verify schema is created properly
CALL apoc.meta.graph() YIELD nodes, relationships
RETURN 
  size(nodes) as node_labels_count,
  size(relationships) as relationship_types_count;

// Count entities by type
MATCH (n) 
RETURN labels(n) as label, count(n) as count 
ORDER BY count DESC;

// Verify GraphRAG relationships exist
MATCH (i:Intent)-[r:REQUIRES]->(e:Entity)
RETURN i.key as intent, r.param_name as parameter, e.type as entity_type, count(*) as count;

// Verify term mappings exist  
MATCH (t:Term)-[r:SYNONYMOUS_WITH]->(e:Entity)
RETURN e.type as entity_type, count(t) as term_count;

// Final status
RETURN "✅ Seed data initialization completed successfully" as status;