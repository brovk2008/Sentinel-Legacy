import functools
import inspect
from typing import Any, Callable, Dict, Optional
from .client import SentinelClient


def governed_tool(
    client: SentinelClient,
    action: str,
    resource_type: str,
    tool_name: Optional[str] = None,
    resource_id_param: str = "id",
):
    """
    Decorator that intercepts an autonomous agent's Python tool function
    and enforces Sentinel Legacy Cedar policy gating, token verification,
    and audit logging before letting the underlying function execute.

    Example:
        @governed_tool(client=sentinel, action="process_refund", resource_type="Transaction")
        async def refund_order(customer_id: str, amount: float, currency: str = "INR"):
            # Real tool logic (e.g. Stripe API call)
            return {"status": "refunded", "amount": amount}
    """

    def decorator(fn: Callable):
        tname = tool_name or fn.__name__

        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                # Map parameters
                sig = inspect.signature(fn)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                params = dict(bound.arguments)
                res_id = str(params.get(resource_id_param, params.get("customer_id", "res_default")))

                # First route proposal through Sentinel
                execution = await client.execute_tool(
                    action=action,
                    resource_type=resource_type,
                    resource_id=res_id,
                    tool_name=tname,
                    parameters=params,
                )

                # If permitted or approved by human, invoke real tool function
                return await fn(*args, **kwargs)

            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                import asyncio
                sig = inspect.signature(fn)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                params = dict(bound.arguments)
                res_id = str(params.get(resource_id_param, params.get("customer_id", "res_default")))

                async def _run():
                    return await client.execute_tool(
                        action=action,
                        resource_type=resource_type,
                        resource_id=res_id,
                        tool_name=tname,
                        parameters=params,
                    )

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                loop.run_until_complete(_run())

                return fn(*args, **kwargs)

            return sync_wrapper

    return decorator
