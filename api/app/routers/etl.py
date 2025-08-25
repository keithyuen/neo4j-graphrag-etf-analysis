from fastapi import APIRouter, HTTPException, Depends
import structlog
from app.models.requests import ETLRefreshRequest
from app.models.responses import ETLResponse
from app.utils.validators import validate_etl_params
from app.utils.security import security
from app.services.etl_service import ETLService
from app.services.neo4j_service import Neo4jService
from config import settings

logger = structlog.get_logger()
router = APIRouter()

# Dependency to get ETL service
async def get_etl_service() -> ETLService:
    neo4j_service = Neo4jService(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
        database=settings.neo4j_database
    )
    return ETLService(neo4j_service)

@router.post("/refresh", response_model=ETLResponse)
async def refresh_etl_data(
    request: ETLRefreshRequest = None,
    etl_service: ETLService = Depends(get_etl_service)
):
    """
    Refresh ETF data with TTL-aware caching.
    Downloads real ETF holdings data from official sources.
    
    This endpoint:
    - Downloads live ETF holdings data (SPY: XLSX, others: CSV)
    - Processes hundreds of companies per ETF
    - Maps companies to GICS sectors
    - Updates Neo4j graph with real data
    - Returns processing summary and cache statistics
    """
    try:
        # Handle empty request body
        if request is None:
            request = ETLRefreshRequest()
        
        # Validate parameters
        params = validate_etl_params(request.tickers, request.force)
        
        logger.info("Processing ETL refresh request",
                   tickers=params['tickers'],
                   force=params['force'])
        
        # Process specific tickers or all tickers
        tickers_to_process = params['tickers'] or ["SPY", "QQQ", "IWM", "IJH", "IVE", "IVW"]
        
        if len(tickers_to_process) == 6:  # All tickers
            # Process all ETFs at once
            results = await etl_service.refresh_all_etfs(force=params['force'])
            
            # Generate detailed message based on results
            total_etfs = len(results['tickers_processed']) + len(results['tickers_failed'])
            success_msg = f"Processed {len(results['tickers_processed'])}/{total_etfs} ETFs successfully"
            
            if results['tickers_failed']:
                failed_list = ", ".join(results['tickers_failed'])
                success_msg += f". Failed: {failed_list}"
                
            if results.get('tickers_cached_fallback'):
                cached_list = ", ".join(results['tickers_cached_fallback'])
                success_msg += f". Used cached fallback: {cached_list}"
            
            success_msg += f". Total companies: {results['total_companies']}"
            
            response = ETLResponse(
                success=results['success'],
                message=success_msg,
                tickers_processed=results['tickers_processed'],
                cache_stats={
                    "cache_hits": results['cache_stats']['hits'],
                    "cache_misses": results['cache_stats']['misses'],
                    "total_processed": len(results['tickers_processed']),
                    "force_refresh": params['force'],
                    "failure_details": results.get('failure_details', {})
                }
            )
        else:
            # Process individual tickers
            processed_tickers = []
            failed_tickers = []
            total_companies = 0
            
            for ticker in tickers_to_process:
                try:
                    company_count, used_cache = await etl_service.refresh_etf_data(ticker, force=params['force'])
                    processed_tickers.append(ticker)
                    total_companies += company_count
                    cache_status = "cached" if used_cache else "fresh"
                    logger.info(f"Successfully processed {ticker}", companies=company_count, cache_status=cache_status)
                except Exception as e:
                    logger.error(f"Failed to process {ticker}", error=str(e))
                    failed_tickers.append(ticker)
                    
            response = ETLResponse(
                success=len(failed_tickers) == 0,
                message=f"ETL refresh completed. Processed {len(processed_tickers)} ETFs with {total_companies} total companies. Failed: {len(failed_tickers)}",
                tickers_processed=processed_tickers,
                cache_stats={
                    "cache_hits": 0,  # Real implementation tracks cache hits
                    "cache_misses": len(processed_tickers),
                    "total_processed": len(processed_tickers),
                    "force_refresh": params['force']
                }
            )
        
        logger.info("ETL refresh completed",
                   tickers_processed=len(response.tickers_processed),
                   success=response.success)
        
        return response
        
    except ValueError as e:
        logger.warning("ETL refresh validation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error("ETL refresh failed", error=str(e))
        return ETLResponse(
            success=False,
            message=f"ETL refresh failed: {str(e)}",
            tickers_processed=[],
            cache_stats={}
        )

@router.post("/refresh/force", response_model=ETLResponse)
async def force_refresh_etl_data(etl_service: ETLService = Depends(get_etl_service)):
    """
    Force refresh all ETF data ignoring cache TTL.
    Downloads fresh data for all supported ETFs.
    """
    try:
        logger.info("Processing force ETL refresh request")
        
        # Force refresh all tickers
        request = ETLRefreshRequest(tickers=None, force=True)
        return await refresh_etl_data(request, etl_service)
        
    except Exception as e:
        logger.error("Force ETL refresh failed", error=str(e))
        return ETLResponse(
            success=False,
            message=f"Force refresh failed: {str(e)}",
            tickers_processed=[],
            cache_stats={}
        )

@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get current cache statistics and data freshness information.
    Returns cache hit rates, TTL status, and last refresh times.
    """
    try:
        # TODO: Implement actual cache statistics
        # This is a placeholder
        
        stats = {
            "cache_enabled": True,
            "default_ttl_days": 30,
            "total_cached_files": 6,
            "cache_hit_rate_24h": 0.85,
            "cache_size_mb": 12.5,
            "last_refresh": {
                "SPY": "2024-01-15T10:30:00Z",
                "QQQ": "2024-01-15T10:30:00Z",
                "IWM": "2024-01-15T10:30:00Z",
                "IJH": "2024-01-15T10:30:00Z",
                "IVE": "2024-01-15T10:30:00Z",
                "IVW": "2024-01-15T10:30:00Z"
            },
            "cache_status": {
                "SPY": "fresh",
                "QQQ": "fresh", 
                "IWM": "fresh",
                "IJH": "fresh",
                "IVE": "fresh",
                "IVW": "fresh"
            }
        }
        
        logger.info("Cache stats requested")
        return stats
        
    except Exception as e:
        logger.error("Failed to get cache stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")

@router.post("/cache/clear")
async def clear_response_cache():
    """
    Clear the GraphRAG response cache for testing and debugging.
    This clears cached query responses to force fresh processing.
    """
    try:
        # Access the pipeline instance from the ask router
        from app.routers.ask import pipeline
        
        if pipeline:
            pipeline.clear_response_cache()
            return {"success": True, "message": "Response cache cleared successfully"}
        else:
            return {"success": False, "message": "GraphRAG pipeline not initialized"}
            
    except Exception as e:
        logger.error("Failed to clear response cache", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to clear response cache")