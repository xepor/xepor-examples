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

import json
import random
import re
import socket
import struct
from collections import defaultdict
from typing import List, Optional, Tuple, Union

from mitmproxy.http import HTTPFlow, Response

from xepor import InterceptedAPI, RouteType
# reference:
# https://github.com/mitmproxy/mitmproxy/blob/ed68e0a1ba/examples/contrib/dns_spoofing.py


HOST_API = "api.krisp.ai"
HOST_ANALYTICS = "analytics.krisp.ai"


class Krisp(InterceptedAPI):
    def __init__(self,
            default_host: Optional[str]=None,
            host_mapping: List[Tuple[Union[str, re.Pattern], str]]={},
            request_passthrough: bool=True,
            response_passthrough=True):

        self.account_fakeip = defaultdict(Krisp.generate_ip)
        super().__init__(default_host=default_host, host_mapping=host_mapping, request_passthrough=request_passthrough, response_passthrough=response_passthrough)

    def request(self, flow: HTTPFlow):
        flow.request.scheme = "https"
        flow.request.port = 443
        # Get Source IP And FAKE it
        ip = flow.client_conn.address[0]
        client_ip = ip[7:] if ip.startswith("::ffff:") else ip

        flow.request.headers["X-Forwarded-For"] = self.account_fakeip[client_ip]

        return super().request(flow)

    @staticmethod
    def generate_ip() -> str:
        return socket.inet_ntoa(
            struct.pack(">I", random.randint(0x01000000, 0xFFFFFFFF)))


api = Krisp(host_mapping=[
    (re.compile(r"krisp.api\."), HOST_API),
    (re.compile(r"krisp.analytics\."), HOST_ANALYTICS),
])


@api.route("/v2/user/profile/2/1", HOST_API, RouteType.RESPONSE)
def fake_profile(flow: HTTPFlow):
    """emulate an "unlimited" license."""
    respdata = json.loads(flow.response.get_content())

    mockdata = {
        "mode": {"name": "unlimited"},
        "settings": {
            "nc_out": {
                "available": True,
                "krisp_mic_as_default": {},
                "room_echo": {"available": True},
                "performance": {"max_level": "high"},
            },
            "nc_in": {"available": True},
            "video_out": {
                "available": True,
                "virtual_background": {
                    "available": True,
                    "krisp_branding": {"available": True, "state": "on"},
                },
            },
            "update": {"available": True},
        },
    }

    respdata["data"].update(mockdata)
    flow.response.set_text(json.dumps(respdata))


# Wildcard route at the end!!
@api.route("{}", HOST_ANALYTICS)
def fake_analytics(flow: HTTPFlow, _):
    reqdata = json.loads(flow.request.get_content())
    respdata = {
        "data": {"app": reqdata},
        "code": 0,
        "message": "Success",
        "http_code": 200,
    }
    flow.response = Response.make(
        content=json.dumps(respdata), headers={"Content-Type": "application/json"},
    )


addons = [api]
