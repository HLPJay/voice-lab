from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.database import get_session
from app.core.errors import VoiceLabError
from app.core.logging import get_logger
from app.domain.schemas import StreamRenderRequest
from app.services.stream_render_service import StreamRenderService
from app.utils.id_generator import new_id

router = APIRouter()
logger = get_logger("ws_render")


@router.websocket("/ws/render")
async def ws_render(websocket: WebSocket):
    await websocket.accept()
    request_id = new_id("ws")
    logger.info("ws_connected request_id=%s", request_id)

    try:
        # 1. Receive first message (must be start)
        start_msg = await websocket.receive_json()

        if start_msg.get("event") != "start":
            await websocket.send_json({
                "event": "error",
                "code": "INVALID_EVENT",
                "message": "First message must have event='start'",
            })
            await websocket.close(code=1008)
            return

        # 2. Validate required fields
        text = start_msg.get("text", "").strip()
        if not text:
            await websocket.send_json({
                "event": "error",
                "code": "INVALID_REQUEST",
                "message": "text is required and must not be empty",
            })
            await websocket.close(code=1008)
            return

        if len(text) > 10000:
            await websocket.send_json({
                "event": "error",
                "code": "INVALID_REQUEST",
                "message": "text must be <= 10000 characters",
            })
            await websocket.close(code=1008)
            return

        # 3. Send connected acknowledgment
        await websocket.send_json({
            "event": "connected",
            "request_id": request_id,
        })

        # 4. Build StreamRenderRequest
        request = StreamRenderRequest(
            text=text,
            profile_id=start_msg.get("profile_id", "deep_night_programmer"),
            provider=start_msg.get("provider"),
            output_format=start_msg.get("output_format", "mp3"),
            need_subtitle=start_msg.get("need_subtitle", False),
            speed=start_msg.get("speed"),
            vol=start_msg.get("vol"),
            pitch=start_msg.get("pitch"),
            emotion=start_msg.get("emotion"),
        )

        # 5. Call Service streaming render
        service = StreamRenderService()
        session = next(get_session())
        try:
            async for msg in service.render_stream(session, request):
                await websocket.send_json(msg)
        finally:
            session.close()

    except WebSocketDisconnect:
        logger.info("ws_disconnected request_id=%s", request_id)
    except VoiceLabError as exc:
        logger.error("ws_error request_id=%s error=%s detail=%s", request_id, exc.message, getattr(exc, 'detail', None))
        try:
            error_code = getattr(exc, 'code', None) or getattr(exc, 'error_code', None) or "PROVIDER_ERROR"
            detail = getattr(exc, 'detail', None)
            full_message = f"{exc.message}: {detail}" if detail else exc.message
            await websocket.send_json({
                "event": "error",
                "code": error_code,
                "message": full_message,
            })
        except Exception:
            pass
    except Exception as exc:
        logger.error("ws_error request_id=%s error=%s", request_id, str(exc))
        try:
            await websocket.send_json({
                "event": "error",
                "code": "INTERNAL_ERROR",
                "message": str(exc)[:200],
            })
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
