from typing import Annotated, Literal

import httpx
import ormsgpack
from pydantic import BaseModel, conint


# 在代码开头添加代理设置
vpn_host = 'http://192.168.1.11:7892'
api = ''

class ServeReferenceAudio(BaseModel):
    audio: bytes
    text: str


class ServeTTSRequest(BaseModel):
    text: str
    chunk_length: Annotated[int, conint(ge=100, le=300, strict=True)] = 200
    # Audio format
    format: Literal["wav", "pcm", "mp3"] = "mp3"
    mp3_bitrate: Literal[64, 128, 192] = 128
    # References audios for in-context learning
    references: list[ServeReferenceAudio] = []
    # Reference id
    # For example, if you want use https://fish.audio/m/7f92f8afb8ec43bf81429cc1c9199cb1/
    # Just pass 7f92f8afb8ec43bf81429cc1c9199cb1
    reference_id: str | None = None
    # Normalize text for en & zh, this increase stability for numbers
    normalize: bool = True
    # Balance mode will reduce latency to 300ms, but may decrease stability
    latency: Literal["normal", "balanced"] = "normal"

def get_voice(context, role_id, sample_sound_path, sample_text, save_path):
    try:
        request = ServeTTSRequest(
            text=context, # 要合成语音的文本
            reference_id= role_id,
            references=[
                ServeReferenceAudio(
                    audio=open(sample_sound_path, "rb").read(),
                    text=sample_text, # 样例音频以及文字
                )
            ],
        )
    except Exception as e:
        print(f'创建请求失败:{e}')

    try:
        with (
            httpx.Client(
                proxy=vpn_host,
                verify=False

            ) as client,
            open(save_path, "wb") as f,
        ):
            with client.stream(
                "POST",
                "https://api.fish.audio/v1/tts",
                content=ormsgpack.packb(request, option=ormsgpack.OPT_SERIALIZE_PYDANTIC),
                headers={
                    "authorization": api,
                    "content-type": "application/msgpack",
                    "model": "speech-1.6",  # Specify which TTS model to use
                },
                timeout=None,
            ) as response:
                for chunk in response.iter_bytes():
                    f.write(chunk)
    except Exception as e:
        print(f'语音合成请求失败:{e}')