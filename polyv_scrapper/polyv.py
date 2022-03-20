import base64
from dataclasses import dataclass, field
import hashlib
import json
import re
from mitmproxy.http import HTTPFlow
from pathlib import Path
from typing import Dict
from xepor import InterceptedAPI, RouteType
try:
    from Cryptodome.Cipher import AES
except ImportError:
    pass

# mitmweb analysis filter: ! (~a | ~u "(woff|ttf)$" | ~m "OPTION")

REDACTED_CONSTANT = """
This script is used to bypass a video DRM system, to decrypt and download online coursewares,
which is *clearly* against its ToS. So the core implementation of decryption algorithm is
removed from this example. Other sensitive information is replaced with `REDACTED_CONSTANT`.

The script is only for demostration of Xepor's (unlimited) capability.
"""
print(REDACTED_CONSTANT)


HOST_DRM_VICTIM = REDACTED_CONSTANT
HOST_POLYV_INFO = "player.polyv.net"
HOST_POLYV_LICENSE = "hls.videocc.net"

VIDEO_DIR = Path("./videos")
KEYS_DIR = VIDEO_DIR / "keys"

KEYS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Lesson:
    vid: str
    title: str
    category: str
    uid: int
    order: int
    content_m3u8: bytes = None
    content_key: bytes = None
    content_info: bytes = None

    def good(self):
        return (
            self.content_m3u8 is not None
            and self.content_key is not None
            and self.content_info is not None
        )


@dataclass
class Ctx:
    lessons: Dict[str, Lesson] = field(default_factory=dict)
    title: str = ""
    root_folder: str = "CISSP"


ctx = Ctx()
api = InterceptedAPI(HOST_DRM_VICTIM)


@api.route(
    "/{REDACTED_CONSTANT}/",
    HOST_DRM_VICTIM,
    rtype=RouteType.RESPONSE,
)
def lessons_list(flow: HTTPFlow):
    "Get metadata from original server, optional, but output files hierarchy would be cleaner"
    if flow.request.method == "OPTIONS":
        # Skip preflight
        return
    payload = flow.response.json()
    review_video_list = payload["data"]["reviewVideoList"]

    def get_lessons(children, category):
        "Find video items and dive into categories recursively, save everything into ctx.lessons"
        count_vid = 0
        count_cat = 0
        for kid in children:
            if kid.get("isPlay") is True:
                count_vid += 1
                lesson = Lesson(
                    kid["vid"][:-2],
                    kid["title"],
                    category,
                    kid["id"],
                    count_vid,
                )
                ctx.lessons[lesson.vid] = lesson
            else:
                count_cat += 1
                get_lessons(kid["children"], f"{category}/{count_cat}_{kid['title']}")

    get_lessons(review_video_list, ctx.root_folder)

    print(
        f"Got {len(ctx.lessons)} lessons"
    )


@api.route("/videojson/{vid}_c.json", HOST_POLYV_INFO, rtype=RouteType.RESPONSE)
def parse_videojson(flow: HTTPFlow, vid):
    "Step 1, get video information from DRM provider, contain links to the video"
    lesson = ctx.lessons[vid]

    key1 = REDACTED_CONSTANT
    key2 = REDACTED_CONSTANT

    # json <body> key include encrypted payload
    payload = bytes.fromhex(flow.response.json()["body"])

    lesson.content_info = json.loads(base64.b64decode(decrypt(key1, key2, payload)))
    print(
        f"Decrypted videojson for {lesson.title}, seed={lesson.content_info[REDACTED_CONSTANT]}"
    )


@api.route("/{}/{}/{vid}_{}.m3u8", HOST_POLYV_LICENSE, rtype=RouteType.RESPONSE)
def lesson_m3u8(flow: HTTPFlow, *_, vid):
    """
    Step 2, get video from DRM provider,
    this is a m3u8 playlist containing links to .ts decryption key (but encrypted)
    and .ts files (also encrypted).
    .ts files are served from CDN, ffmpeg could directly access their contents.
    No need to download inside our script.
    """
    lesson = ctx.lessons[vid]
    lesson.content_m3u8 = flow.response.get_content()
    print("Found playlist for", lesson.uid, lesson.title)


@api.route(
    "/playsafe/{}/{}/{vid}_{}.key", HOST_POLYV_LICENSE, rtype=RouteType.RESPONSE
)
def lesson_key(flow: HTTPFlow, *_, vid):
    """
    Step 3, get key from DRM provider.
    We'll decrypt that key later.
    """
    lesson = ctx.lessons[vid]
    lesson.content_key = flow.response.get_content()
    print("Found key for", lesson.uid, lesson.title)
    # Everything needed is done. Good to go!
    process_lesson(lesson)


def decrypt(_: bytes, __: bytes, ___: bytes):
    return REDACTED_CONSTANT


def process_lesson(lesson: Lesson):
    if not lesson.good():
        print("Not enough info to decrypt the video:", lesson)
        return False

    decrypted_key = REDACTED_CONSTANT
    print("Decrypted key:", decrypted_key.hex())

    # Write video encryption keys
    key_path = KEYS_DIR / f"{lesson.uid}_{lesson.vid}.key"
    with key_path.open("wb") as f:
        f.write(decrypted_key[:REDACTED_CONSTANT])

    # Replace key URL with our decrypted ones (later served by python -m http.server)
    m3u8_content = re.sub(
        rb'(METHOD=AES-128,URI=")([^\"]+)',
        rb"\1http://localhost:8000/keys/" + key_path.name.encode(),
        lesson.content_m3u8,
    )

    # Write m3u8
    m3u8_path = (
        VIDEO_DIR / ctx.title / lesson.category / f"{lesson.order}_{lesson.title}.m3u8"
    )
    m3u8_path.parent.mkdir(parents=True, exist_ok=True)
    with m3u8_path.open("wb") as f:
        f.write(m3u8_content)

    print("Saved m3u8 to", str(m3u8_path))

    # Done! simply use ffmpeg to convert m3u8 to mp4.
    return True


addons = [api]

print(__name__, "is loaded!")
