#!/usr/bin/env python3
"""FastAPI server for the Deep Research Agent web application.

Run with:
    uvicorn web_app.server:app --reload

Then open http://localhost:8000 in your browser.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import agent as research_agent

_STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Deep Research Agent", version="1.0.0")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# In-memory job registry: job_id → asyncio.Queue[dict | None]
# None is the sentinel that signals end-of-stream.
_jobs: dict[str, asyncio.Queue] = {}


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200)
    provider: str = Field(..., pattern="^(openai|anthropic)$")
    api_key: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")


@app.post("/api/research/start")
async def start_research(req: ResearchRequest) -> dict:
    """Start a new research job. Returns a job_id for the SSE stream."""
    job_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _jobs[job_id] = queue
    asyncio.create_task(_research_task(req, queue, job_id))
    return {"job_id": job_id}


@app.get("/api/research/{job_id}/stream")
async def stream_research(job_id: str) -> StreamingResponse:
    """SSE stream for a running research job."""
    queue = _jobs.get(job_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return StreamingResponse(
        _event_generator(queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _research_task(
    req: ResearchRequest,
    queue: asyncio.Queue,
    job_id: str,
) -> None:
    """Background task that runs the research pipeline and feeds the queue."""
    async def emit(event_type: str, **data) -> None:
        await queue.put({"type": event_type, **data})

    try:
        await research_agent.run_research(
            topic=req.topic,
            provider=req.provider,
            api_key=req.api_key,
            model=req.model,
            emit=emit,
        )
    except Exception as exc:
        await queue.put({"type": "error", "message": str(exc)})
    finally:
        await queue.put(None)  # sentinel — closes the SSE stream

    # Clean up job entry after 10 minutes
    await asyncio.sleep(600)
    _jobs.pop(job_id, None)


async def _event_generator(queue: asyncio.Queue):
    """Yield SSE-formatted events from the job queue."""
    while True:
        item = await queue.get()
        if item is None:
            yield 'data: {"type":"stream_end"}\n\n'
            break
        yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
