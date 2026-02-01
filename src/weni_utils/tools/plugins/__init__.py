"""
Plugins para o Weni VTEX Concierge

Plugins são extensões opcionais que adicionam funcionalidades específicas.
Cada cliente pode escolher quais plugins utilizar.

Uso:
    from weni_utils.tools.plugins import Regionalization, Wholesale, Carousel, CAPI

    concierge = ProductConcierge(
        base_url="...",
        store_url="...",
        plugins=[
            Regionalization(),
            Wholesale(fixed_price_url="..."),
        ]
    )
"""

from .base import PluginBase
from .capi import CAPI
from .carousel import Carousel
from .cart_simulation import CartSimulation
from .regionalization import Regionalization
from .utils import (
    check_stock_availability,
    get_product_price,
    get_region,
    get_sellers_by_region,
    get_wholesale_price,
    send_capi_event,
    simulate_cart,
    simulate_cart_batch,
    trigger_weni_flow,
)
from .weni_flow import WeniFlowTrigger
from .wholesale import Wholesale
from .send_message import SendMessage

__all__ = [
    # Plugin classes
    "PluginBase",
    "Regionalization",
    "Wholesale",
    "Carousel",
    "CAPI",
    "WeniFlowTrigger",
    "SendMessage",
    "CartSimulation",
    # Utility functions
    "simulate_cart",
    "simulate_cart_batch",
    "check_stock_availability",
    "get_product_price",
    "get_region",
    "get_sellers_by_region",
    "get_wholesale_price",
    "send_capi_event",
    "trigger_weni_flow",
]
