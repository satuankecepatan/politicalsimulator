"""WebSocket streaming endpoint for live simulation control."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from polsim.api.sessions import manager

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def websocket_simulation_stream(websocket: WebSocket, session_id: str):
    """Live bidirectional WebSocket for streaming tick results and receiving UI run controls."""
    await websocket.accept()
    sim = manager.get(session_id)
    if not sim:
        await websocket.send_json({"type": "error", "message": f"Session '{session_id}' not found"})
        await websocket.close()
        return

    is_running = False
    speed_ms = 250  # milliseconds between ticks in live play mode

    # Send initial status
    await websocket.send_json({
        "type": "init",
        "session_id": session_id,
        "summary": sim.get_status_summary(),
        "compass": sim.get_compass_preview(),
    })

    async def run_loop():
        nonlocal is_running, speed_ms
        while True:
            if is_running:
                new_entries = sim.tick()
                summary = sim.get_status_summary()
                compass = sim.get_compass_preview()
                await websocket.send_json({
                    "type": "tick",
                    "summary": summary,
                    "compass": compass,
                    "entries": [e.to_dict() for e in new_entries],
                })
            await asyncio.sleep(speed_ms / 1000.0)

    loop_task = asyncio.create_task(run_loop())

    try:
        while True:
            data = await websocket.receive_text()
            cmd = json.loads(data)
            action = cmd.get("type")

            if action == "play":
                is_running = True
                if "speed_ms" in cmd:
                    speed_ms = max(20, int(cmd["speed_ms"]))
            elif action == "pause":
                is_running = False
            elif action == "speed":
                speed_ms = max(20, int(cmd.get("speed_ms", 250)))
            elif action == "step":
                is_running = False
                new_entries = sim.tick()
                await websocket.send_json({
                    "type": "tick",
                    "summary": sim.get_status_summary(),
                    "compass": sim.get_compass_preview(),
                    "entries": [e.to_dict() for e in new_entries],
                })
            elif action == "run_years":
                is_running = False
                years = max(1, min(100, int(cmd.get("years", 5))))
                sim.run(years=years)
                await websocket.send_json({
                    "type": "batch_complete",
                    "summary": sim.get_status_summary(),
                    "compass": sim.get_compass_preview(),
                    "recent_entries": [e.to_dict() for e in sim.history.entries[-30:]],
                })

    except WebSocketDisconnect:
        pass
    finally:
        loop_task.cancel()
