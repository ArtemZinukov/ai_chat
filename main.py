from contextlib import asynccontextmanager, suppress

import aiofiles
from environs import Env
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from starlette.websockets import WebSocketDisconnect

env = Env()
env.read_env()

GIGA_CREDS = env.str("GIGACHAT_CREDENTIALS")
GIGA_SCOPE = env.str("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGA_MODEL = env.str("GIGACHAT_MODEL", "GigaChat")

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with GigaChat(
        credentials=GIGA_CREDS,
        scope=GIGA_SCOPE,
        verify_ssl_certs=False
    ) as giga:
        app.state.giga_client = giga
        yield

app = FastAPI(lifespan=lifespan)


async def ask_giga_stream(client: GigaChat, prompt: str):
    payload = Chat(
        messages=[Messages(role=MessagesRole.USER, content=prompt)],
        model=GIGA_MODEL
    )

    async for chunk in client.astream(payload):
        content = chunk.choices[0].delta.content
        if content:
            yield content

async def read_file(file):
    async with aiofiles.open(file, mode="r", encoding="utf-8") as f:
        return await f.read()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return await read_file("index.html")

def get_giga_client():
    return app.state.giga_client

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    giga: GigaChat = get_giga_client()

    with suppress(WebSocketDisconnect):
        try:
            while True:
                data = await websocket.receive_json(mode='text')
                user_prompt = data.get("content")

                if user_prompt:
                    async for partial_text in ask_giga_stream(giga, user_prompt):
                        await websocket.send_json({
                            "type": "ai_response_chunk",
                            "content": partial_text
                        })

        finally:
            with suppress(RuntimeError):
                await websocket.close()
