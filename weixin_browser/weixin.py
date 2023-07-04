"""
Usage:
    mitmweb --no-web-open-browser --set connection_strategy=lazy -s weixin.py
"""

from dataclasses import dataclass
import urllib.parse

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
        if "&exportkey=" in ctx.url:
            print(f"New version of sharing URL is detected, origin url:\n{ctx.url}\n")
        parsed = urllib.parse.urlparse(ctx.url)
        qs = urllib.parse.parse_qs(parsed.query)
        # filter with a whitelist of query string parameters to ensure no user identity is leaked through URL
        ctx.url = urllib.parse.urlunparse(
            parsed._replace(
                netloc=flow.request.pretty_host,
                query=urllib.parse.urlencode([(k, qs[k]) for k in ["__biz", "mid", "idx", "sn", "chksm"]], doseq=True))
        )

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
