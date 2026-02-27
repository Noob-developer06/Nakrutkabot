#api_requests.py 

import aiohttp
import json

from database.requests import get_api

async def smm_requests(api_id=None, action=None, url=None, key=None, **kwargs):
    # Agar api_id berilgan bo‘lsa bazadan oladi
    if api_id is not None:
        api = await get_api(api_id)
        api_url = api[1]
        api_key = api[2]
    else:
        api_url = url
        api_key = key

    params = {"key": api_key, "action": action}
    params.update(kwargs)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, params=params, timeout=10) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except aiohttp.ContentTypeError:
                        text = await response.text()
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            return {"error": "Invalid JSON response", "raw": text[:200]}
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            return {"error": str(e)}


async def get_api_services(api_id):
    services = await smm_requests(api_id, "services")
    return services


async def get_api_service(api_id: int, service_id: int):
    services = await get_api_services(api_id)

    return next(
        (s for s in services if int(s.get("service")) == service_id),
        None
    )

async def send_order(api_id, service, link, quantity):
    return await smm_requests(api_id, "add", service=service, link=link, quantity=quantity)


async def get_status(api_id, order_id):
    return await smm_requests(api_id, "status", order=order_id)


async def get_balance(api_id=None, url=None, key=None):
    result = await smm_requests(
        api_id=api_id,
        action="balance",
        url=url,
        key=key
    )
    return result

async def get_refill(api_id, order_id):
    return await smm_requests(api_id, "refill", order=order_id)


async def get_cancel(api_id, order_id):
    return await smm_requests(api_id, "cancel", order=order_id)


