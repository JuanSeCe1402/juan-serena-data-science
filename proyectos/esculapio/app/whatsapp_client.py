"""Cliente de WhatsApp Cloud API y utilidades de webhook."""
import httpx

from app.config import settings


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }


def _log_outgoing(
    to: str,
    text: str,
    message_type: str,
    external_id: str | None = None,
    delivery_status: str | None = "sent",
    error_detail: str | None = None,
) -> None:
    """Guarda el resultado del envío sin hacer fallar la operación principal."""
    try:
        from app.database import SessionLocal
        from app.models import MessageLog

        db = SessionLocal()
        try:
            if external_id:
                existing = (
                    db.query(MessageLog)
                    .filter(MessageLog.external_id == external_id)
                    .first()
                )
                if existing:
                    if delivery_status:
                        existing.delivery_status = delivery_status
                    if error_detail:
                        existing.error_detail = error_detail[:2000]
                    db.commit()
                    return

            db.add(
                MessageLog(
                    phone=to,
                    direction="outgoing",
                    text=text or "",
                    message_type=message_type,
                    external_id=external_id,
                    source="demo" if settings.DEMO_MODE else "api",
                    delivery_status="simulated" if settings.DEMO_MODE else delivery_status,
                    error_detail=(error_detail or "")[:2000] or None,
                    is_read=True,
                )
            )
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        pass


async def send_text(to: str, body: str) -> bool:
    try:
        if settings.DEMO_MODE:
            _log_outgoing(to,body,'text',delivery_status='simulated')
            return True
        if not settings.INTEGRATIONS_ENABLED:return False
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(settings.WHATSAPP_API_URL, headers=_headers(), json=payload)
            if resp.status_code >= 400:
                detail = f"Proveedor rechazó la solicitud (HTTP {resp.status_code})"
                pass
                _log_outgoing(to, body, "text", delivery_status="failed", error_detail=detail)
                return False
            data = resp.json()
            external_id = ((data.get("messages") or [{}])[0]).get("id")
            _log_outgoing(to, body, "text", external_id, delivery_status="sent")
            return True
    except (httpx.HTTPError,ValueError,TypeError,KeyError,OSError):
        return False


async def send_buttons(to: str, body: str, buttons: list[tuple[str, str]]) -> bool:
    try:
        if settings.DEMO_MODE:
            _log_outgoing(to,body,'text',delivery_status='simulated')
            return True
        if not settings.INTEGRATIONS_ENABLED:return False
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": bid, "title": label[:20]}}
                        for bid, label in buttons[:3]
                    ]
                },
            },
        }
        labels = " / ".join(label for _, label in buttons[:3])
        display_text = f"{body}\\n[{labels}]"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(settings.WHATSAPP_API_URL, headers=_headers(), json=payload)
            if resp.status_code >= 400:
                detail = f"Proveedor rechazó la solicitud (HTTP {resp.status_code})"
                pass
                _log_outgoing(
                    to, display_text, "interactive",
                    delivery_status="failed", error_detail=detail
                )
                return False
            data = resp.json()
            external_id = ((data.get("messages") or [{}])[0]).get("id")
            _log_outgoing(to, display_text, "interactive", external_id, delivery_status="sent")
            return True
    except (httpx.HTTPError,ValueError,TypeError,KeyError,OSError):
        return False


async def send_document(to: str, media_id: str, filename: str, caption: str = "") -> bool:
    try:
        if settings.DEMO_MODE:
            _log_outgoing(to,'Demostración: documento no enviado.','text',delivery_status='simulated')
            return True
        if not settings.INTEGRATIONS_ENABLED:return False
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {"id": media_id, "filename": filename, "caption": caption},
        }
        display_text = caption or filename
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(settings.WHATSAPP_API_URL, headers=_headers(), json=payload)
            if resp.status_code >= 400:
                detail = f"Proveedor rechazó la solicitud (HTTP {resp.status_code})"
                pass
                _log_outgoing(
                    to, display_text, "document",
                    delivery_status="failed", error_detail=detail
                )
                return False
            data = resp.json()
            external_id = ((data.get("messages") or [{}])[0]).get("id")
            _log_outgoing(to, display_text, "document", external_id, delivery_status="sent")
            return True
    except (httpx.HTTPError,ValueError,TypeError,KeyError,OSError):
        return False


async def upload_media(file_path: str, mime_type: str = "application/pdf") -> str | None:
    try:
        if settings.DEMO_MODE:
            return None
        if not settings.INTEGRATIONS_ENABLED:return None
        url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/media"
        headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}

        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f, mime_type)}
            data = {"messaging_product": "whatsapp", "type": mime_type}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, data=data, files=files)

        if resp.status_code >= 400:
            pass
            return None
        return resp.json().get("id")
    except (httpx.HTTPError,ValueError,TypeError,KeyError,OSError):
        return None


async def download_media(
    media_id: str,
    max_bytes: int | None = None,
) -> tuple[bytes, str] | None:
    """
    Descarga un adjunto de WhatsApp con límite de tamaño.
    Regresa (bytes, mime_type) o None si falla o supera el límite.
    """
    try:
        if settings.DEMO_MODE:
            return None
        if not settings.INTEGRATIONS_ENABLED:return None
        if not settings.ALLOW_MEDIA_DOWNLOAD:return None
        meta_url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{media_id}"
        async with httpx.AsyncClient(timeout=30) as client:
            meta_resp = await client.get(meta_url, headers=_headers())
            if meta_resp.status_code >= 400:
                pass
                return None

            meta = meta_resp.json()
            file_url = meta.get("url")
            mime_type = (meta.get("mime_type") or "application/octet-stream").lower()
            file_size = meta.get("file_size")
            if max_bytes and file_size:
                try:
                    if int(file_size) > max_bytes:
                        pass
                        return None
                except (TypeError, ValueError):
                    pass
            from urllib.parse import urlsplit
            parsed=urlsplit(file_url or '')
            if parsed.scheme!='https' or parsed.hostname not in ('lookaside.fbsbx.com','lookaside.facebook.com') or parsed.username or parsed.password or parsed.port not in (None,443):
                return None

            headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}
            async with client.stream("GET", file_url, headers=headers) as file_resp:
                if file_resp.status_code >= 400:
                    body = await file_resp.aread()
                    pass
                    return None

                chunks = []
                total = 0
                async for chunk in file_resp.aiter_bytes():
                    total += len(chunk)
                    if max_bytes and total > max_bytes:
                        pass
                        return None
                    chunks.append(chunk)
                return b"".join(chunks), mime_type
    except (httpx.HTTPError,ValueError,TypeError,KeyError,OSError):
        return None


def _message_text(msg: dict) -> str:
    msg_type = msg.get("type", "")
    if msg_type == "text":
        return (msg.get("text") or {}).get("body", "").strip()
    if msg_type == "interactive":
        interactive = msg.get("interactive") or {}
        if interactive.get("type") == "button_reply":
            return (interactive.get("button_reply") or {}).get("title", "").strip()
        if interactive.get("type") == "list_reply":
            return (interactive.get("list_reply") or {}).get("title", "").strip()
    if msg_type in ("image", "video", "document"):
        caption = (msg.get(msg_type) or {}).get("caption", "")
        return caption.strip() or f"[{msg_type}]"
    return f"[{msg_type or 'mensaje'}]"


def extract_incoming_message(payload: dict) -> dict | None:
    """Extrae un mensaje entrante normal del webhook `messages`."""
    try:
        change = payload["entry"][0]["changes"][0]
        if change.get("field") not in (None, "messages"):
            return None
        value = change["value"]
        messages = value.get("messages")
        if not messages:
            return None

        msg = messages[0]
        from_number = msg["from"]
        button_id = None
        if msg.get("type") == "interactive":
            interactive = msg.get("interactive") or {}
            if interactive.get("type") == "button_reply":
                button_id = (interactive.get("button_reply") or {}).get("id")

        msg_type = msg.get("type", "text")
        media_id = None
        if msg_type in ("image", "document", "audio", "video", "sticker"):
            media_id = (msg.get(msg_type) or {}).get("id")

        return {
            "from": from_number,
            "text": _message_text(msg),
            "button_id": button_id,
            "external_id": msg.get("id"),
            "message_type": msg_type,
            "media_id": media_id,
        }
    except (KeyError, IndexError, TypeError):
        return None


def extract_message_statuses(payload: dict) -> list[dict]:
    """Extrae estados sent/delivered/read/failed reportados por Meta."""
    results = []
    try:
        for entry in payload.get("entry") or []:
            for change in entry.get("changes") or []:
                value = change.get("value") or {}
                for item in value.get("statuses") or []:
                    errors = item.get("errors") or []
                    error_text = None
                    if errors:
                        parts = []
                        for err in errors[:3]:
                            title = err.get("title") or err.get("message") or "Error"
                            code = err.get("code")
                            parts.append(f"{title}" + (f" ({code})" if code is not None else ""))
                        error_text = "; ".join(parts)
                    results.append(
                        {
                            "external_id": item.get("id"),
                            "status": item.get("status"),
                            "timestamp": item.get("timestamp"),
                            "error_detail": error_text,
                        }
                    )
    except (TypeError, ValueError):
        return []
    return [r for r in results if r.get("external_id") and r.get("status")]


def extract_business_app_echo(payload: dict) -> dict | None:
    """Extrae mensajes enviados manualmente desde WhatsApp Business en Coexistence."""
    try:
        change = payload["entry"][0]["changes"][0]
        if change.get("field") != "smb_message_echoes":
            return None
        echoes = (change.get("value") or {}).get("message_echoes") or []
        if not echoes:
            return None
        msg = echoes[0]
        return {
            "to": msg.get("to", ""),
            "text": _message_text(msg),
            "external_id": msg.get("id"),
            "message_type": msg.get("type", "text"),
        }
    except (KeyError, IndexError, TypeError):
        return None
