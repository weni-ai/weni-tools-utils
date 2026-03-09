import os

from dotenv import load_dotenv
from weni.context import Context

from src.weni_utils.tools.proxy import ProxyRequest

load_dotenv()

context = Context(
    parameters={"document": "11970011408"},
    globals={},
    contact={},
    project={"auth_token": os.getenv("AUTH_TOKEN", "mock-token")},
    constants={},
    credentials={},
)

proxy = ProxyRequest(context)

response = proxy.make_proxy_request(
    path="api/oms/pvt/orders?q=11970011408",
    method="GET",
)

print(response)
