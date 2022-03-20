from mitmproxy.http import HTTPFlow
from xepor import InterceptedAPI, RouteType


HOST_HTTPBIN = "httpbin.org"

api = InterceptedAPI(HOST_HTTPBIN)


@api.route("/get")
def change_your_request(flow: HTTPFlow):
    """
    Modify URL query param.
    Test at:
    http://httpbin.org/#/HTTP_Methods/get_get
    """
    flow.request.query["payload"] = "evil_param"


@api.route("/basic-auth/{usr}/{pwd}", rtype=RouteType.RESPONSE)
def capture_auth(flow: HTTPFlow, usr=None, pwd=None):
    """
    Sniffing password.
    Test at:
    http://httpbin.org/#/Auth/get_basic_auth__user___passwd_
    """
    print(
        f"auth @ {usr} + {pwd}:",
        f"Captured {'successful' if flow.response.status_code < 300 else 'unsuccessful'} login:",
        flow.request.headers.get("Authorization", ""),
    )


addons = [api]
