"""
Usage:
    mitmproxy
        -p 8081
        -s krisp.py
        # Used as the target location if neither SNI nor host header are present.
        --mode reverse:http://localhost/
        # To avoid auto rewriting of host header by the reverse proxy target.
        --set keep_host_header

    mitmdump -p 8081 -s krisp.py --mode reverse:http://localhost --set keep_host_header
"""

from dataclasses import dataclass
import json
from flask import request

from mitmproxy.http import HTTPFlow, Response, Headers

from xepor import InterceptedAPI, RouteType

# reference:
# https://github.com/mitmproxy/mitmproxy/blob/ed68e0a1ba/examples/contrib/dns_spoofing.py


HOST = "mp.weixin.qq.com"


@dataclass
class Ctx:
    headers: Headers = None
    url = ""
    cached = False


ctx = Ctx()

api = InterceptedAPI(HOST)


def cache_headers(flow: HTTPFlow, _=None):
    print("Route hit..")
    headers = flow.request.headers
    if "MicroMessenger" in headers["User-Agent"]:
        from_weixin = True
    else:
        from_weixin = False
    print(f"From weixin={from_weixin}")

    common_headers = [
        "content-length",
        "origin",
        "content-type",
        "accept",
        "accept-encoding",
        "accept-language",
        "referer",
    ]

    if from_weixin:
        ctx.headers = Headers(headers.fields)
        ctx.url = flow.request.url
        ctx.cached = True
        for h in common_headers:
            if h in headers:
                del ctx.headers[h]
        print(
            f"Cache {len(ctx.headers)} HTTP Headers from Weixin Client,\n"
            f"visit the following page in your browser:\n\n"
            f"{ctx.url}\n"
        )
    elif ctx.cached:
        new_headers = Headers(ctx.headers.fields)
        for h in common_headers:
            if h in headers:
                new_headers[h] = headers[h]

        flow.request.headers = new_headers
        print(
            "Replaying headers from cached ones, original:",
            len(headers),
            "=> new:",
            len(new_headers),
        )


# https://mp.weixin.qq.com/s?__biz=Mzxxxxxxx&mid=2xxxxxx7&idx=1&sn=7xxxxe4c4c6&chksm=fx48&xxxxxx
api.route("/s")(cache_headers)
# https://mp.weixin.qq.com/s/tx9xxxxxxxx
api.route("/s/{}")(cache_headers)


addons = [api]
