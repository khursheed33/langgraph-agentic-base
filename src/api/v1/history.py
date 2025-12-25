"""History router for retrieving conversation history."""

from fastapi import APIRouter, HTTPException

from src.api.schemas.responses import HistoryResponse
from src.api.utils import get_workflow_state
from src.utils.logger import logger

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/", response_model=HistoryResponse)
async def get_history(thread_id: str | None = None, limit: int = 50) -> HistoryResponse:
    """Get conversation history for a thread.
    
    Args:
        thread_id: Optional thread ID to filter history.
        limit: Maximum number of entries to return (default: 50, max: 1000).
        
    Returns:
        History response with conversation entries.
    """
    try:
        if limit < 1 or limit > 1000:
            limit = 50
        
        if thread_id:
            # Get history for specific thread
            workflow_state = get_workflow_state(thread_id)
            if not workflow_state:
                raise HTTPException(
                    status_code=404, detail=f"Thread {thread_id} not found"
                )
            
            conversation_history = workflow_state.get("conversation_history", [])
            # Limit results
            conversation_history = conversation_history[-limit:]
            
            return HistoryResponse(
                thread_id=thread_id,
                conversation_history=conversation_history,
                total_entries=len(conversation_history),
            )
        else:
            # Get all threads - this would require listing all checkpoints
            # For now, return empty history if no thread_id provided
            logger.warning("History requested without thread_id - returning empty")
            return HistoryResponse(
                thread_id="",
                conversation_history=[],
                total_entries=0,
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

