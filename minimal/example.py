"""
Minimal working example for Xepor framework
Run the script with:

mitmweb --web-host=\* --no-web-open-browser --set connection_strategy=lazy -s example.py
"""
from xepor import InterceptedAPI, RouteType
from mitmproxy.http import HTTPFlow


TARGET_HOST = "mitm.it"

api = InterceptedAPI(default_host=TARGET_HOST)


@api.route("/", rtype=RouteType.RESPONSE)
def func1(flow: HTTPFlow):
    flow.response.set_content(
        flow.response.get_content().replace(
            b"Install mitmproxy's Certificate Authority",
            b"Install mitmproxy\xe2\x9d\xa4\xef\xb8\x8fXepor Certificate Authority",
            # mitmproxy❤️Xepor
        )
    )


addons = [api]
print(f"Xepor plugin [{__name__}] is loaded!")
