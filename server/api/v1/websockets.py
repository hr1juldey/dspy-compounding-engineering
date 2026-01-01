"""
WebSocket endpoints for real-time progress streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from server.infrastructure.redis.pubsub import subscribe_to_task

router = APIRouter(tags=["websockets"])


@router.websocket("/ws/task/{task_id}")
async def task_progress_stream(websocket: WebSocket, task_id: str):
    """
    Stream real-time progress updates for a task.

    Args:
        task_id: Celery task ID to subscribe to

    WebSocket receives JSON messages:
        {
            "task_id": "...",
            "percent": 0-100,
            "message": "Status message",
            "timestamp": "ISO timestamp"
        }
    """
    await websocket.accept()

    try:
        # Subscribe to task progress channel
        async for progress_update in subscribe_to_task(task_id):
            # Send progress to client
            await websocket.send_json(progress_update)

            # Close connection if task is complete (100%)
            if progress_update.get("percent") == 100:
                break

    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Send error and close
        await websocket.send_json({"error": str(e), "percent": -1})
    finally:
        await websocket.close()
