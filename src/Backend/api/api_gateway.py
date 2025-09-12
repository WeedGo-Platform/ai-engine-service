"""
API Gateway/Proxy Layer
Maps frontend expected endpoints to actual backend endpoints
"""

from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# Base URL for internal routing (since everything is in the same service)
BASE_URL = "http://localhost:5024"


@router.api_route("/identity/auth/login", methods=["POST"])
async def proxy_login(request: Request):
    """Proxy login request to customer auth endpoint"""
    try:
        body = await request.json()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/customer/login",
                json=body,
                headers=dict(request.headers)
            )
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except Exception as e:
        logger.error(f"Login proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/identity/users/register", methods=["POST"])
async def proxy_register(request: Request):
    """Proxy registration request to customer auth endpoint"""
    try:
        body = await request.json()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/customer/register",
                json=body,
                headers=dict(request.headers)
            )
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except Exception as e:
        logger.error(f"Registration proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/identity/users/{user_id}", methods=["GET", "PATCH"])
async def proxy_user_profile(user_id: str, request: Request):
    """Proxy user profile requests"""
    try:
        if request.method == "GET":
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BASE_URL}/api/user/profile/{user_id}",
                    headers=dict(request.headers)
                )
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code
                )
        else:  # PATCH
            body = await request.json()
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{BASE_URL}/api/customers/{user_id}",
                    json=body,
                    headers=dict(request.headers)
                )
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code
                )
    except Exception as e:
        logger.error(f"User profile proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/commerce/cart/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_cart(path: str, request: Request):
    """Proxy cart requests to cart endpoints"""
    try:
        # Map commerce/cart to /api/cart
        url = f"{BASE_URL}/api/cart"
        if path:
            url += f"/{path}"
        
        async with httpx.AsyncClient() as client:
            if request.method == "GET":
                response = await client.get(
                    url,
                    params=dict(request.query_params),
                    headers=dict(request.headers)
                )
            elif request.method == "POST":
                body = await request.body()
                response = await client.post(
                    url,
                    content=body if body else None,
                    headers=dict(request.headers)
                )
            elif request.method == "PUT":
                body = await request.json()
                response = await client.put(
                    url,
                    json=body,
                    headers=dict(request.headers)
                )
            else:  # DELETE
                response = await client.delete(
                    url,
                    headers=dict(request.headers)
                )
            
            return JSONResponse(
                content=response.json() if response.content else {},
                status_code=response.status_code
            )
    except Exception as e:
        logger.error(f"Cart proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/commerce/orders/{path:path}", methods=["GET", "POST", "PATCH"])
async def proxy_orders(path: str = "", request: Request):
    """Proxy order requests to order endpoints"""
    try:
        # Map commerce/orders to /api/orders
        url = f"{BASE_URL}/api/orders"
        if path:
            url += f"/{path}"
        
        async with httpx.AsyncClient() as client:
            if request.method == "GET":
                response = await client.get(
                    url,
                    params=dict(request.query_params),
                    headers=dict(request.headers)
                )
            elif request.method == "POST":
                body = await request.json()
                response = await client.post(
                    url,
                    json=body,
                    headers=dict(request.headers)
                )
            else:  # PATCH
                body = await request.json()
                response = await client.patch(
                    url,
                    json=body,
                    headers=dict(request.headers)
                )
            
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except Exception as e:
        logger.error(f"Orders proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commerce/orders/track")
async def proxy_order_tracking(
    orderNumber: str = Query(...),
    email: str = Query(...),
):
    """Proxy order tracking request"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/orders/track",
                params={"order_number": orderNumber, "email": email}
            )
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except Exception as e:
        logger.error(f"Order tracking proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/pricing/promotions/{path:path}", methods=["GET", "POST"])
async def proxy_promotions(path: str = "", request: Request):
    """Proxy promotion requests"""
    try:
        # Map pricing/promotions to /api/promotions
        url = f"{BASE_URL}/api/promotions"
        if path:
            url += f"/{path}"
        
        async with httpx.AsyncClient() as client:
            if request.method == "GET":
                response = await client.get(
                    url,
                    params=dict(request.query_params),
                    headers=dict(request.headers)
                )
            else:  # POST
                body = await request.json()
                response = await client.post(
                    url,
                    json=body,
                    headers=dict(request.headers)
                )
            
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except Exception as e:
        logger.error(f"Promotions proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/stock/{sku}")
async def proxy_inventory_check(sku: str):
    """Proxy inventory check"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/inventory/status/{sku}"
            )
            data = response.json()
            # Transform response to match frontend expectations
            return {
                "inStock": data.get("in_stock", False),
                "quantity": data.get("available_quantity", 0)
            }
    except Exception as e:
        logger.error(f"Inventory proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inventory/reserve")
async def proxy_inventory_reserve(request: Request):
    """Proxy inventory reservation"""
    try:
        body = await request.json()
        async with httpx.AsyncClient() as client:
            # Transform request format if needed
            response = await client.post(
                f"{BASE_URL}/api/inventory/reserve",
                json=body,
                headers=dict(request.headers)
            )
            return JSONResponse(
                content={"success": response.status_code == 200},
                status_code=response.status_code
            )
    except Exception as e:
        logger.error(f"Inventory reserve proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))