"""
Device discovery for Kospel C.MI modules.

Probes devices via GET /api/dev (no device_id required) and
fetches per-device info via GET /api/dev/{id}/info.
"""

import asyncio
import ipaddress
import logging
from typing import Optional
from urllib.parse import urlparse

import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Model ID to name mapping (from Kospel web UI)
MODEL_NAMES: dict[int, str] = {
    18: "EKD.M3",   # Kocioł dwufunkcyjny elektryczny
    19: "EKCO.M3",  # Kocioł elektryczny (do fotowoltaiki)
    65: "C.MG3",    # Moduł rozszerzający (obiegi grzewcze)
    81: "C.MW3",    # Moduł (pompa ciepła)
}


def _model_name(model_id: int) -> str:
    """Return model name for given model_id, or 'Unknown' for unknown IDs."""
    return MODEL_NAMES.get(model_id, "Unknown")


class DeviceDetail(BaseModel):
    """Per-device info from /api/dev/{id}/info."""

    device_id: int
    model_id: int
    model_name: str
    module_id: str


class KospelDeviceInfo(BaseModel):
    """Result of probing a Kospel C.MI module at given host."""

    host: str
    device_ids: list[int]
    serial_number: str
    api_base_url: str
    devices: list[DeviceDetail] = []

    @property
    def device_id(self) -> int:
        """First device ID for backward compatibility."""
        return self.device_ids[0] if self.device_ids else 0


def _normalize_host(host: str) -> str:
    """Ensure host has http:// prefix."""
    host = host.strip()
    if not host.startswith(("http://", "https://")):
        return f"http://{host}"
    return host


def _extract_host(host: str) -> str:
    """Extract hostname:port for display from URL or plain host string."""
    normalized = _normalize_host(host)
    parsed = urlparse(normalized)
    return parsed.netloc or parsed.path or host.strip()


async def probe_device(
    session: aiohttp.ClientSession,
    host: str,
    timeout: float = 5.0,
) -> Optional[KospelDeviceInfo]:
    """
    Probe a host to check if it is a Kospel C.MI device.

    Uses GET /api/dev (no device_id required) and fetches per-device info
    via GET /api/dev/{id}/info.

    Args:
        session: aiohttp ClientSession
        host: IP address or hostname (e.g. "192.168.101.49")
        timeout: Request timeout in seconds

    Returns:
        KospelDeviceInfo if host is a C.MI device, None otherwise
    """
    base_url = _normalize_host(host).rstrip("/")
    dev_url = f"{base_url}/api/dev"

    try:
        async with session.get(
            dev_url, timeout=aiohttp.ClientTimeout(total=timeout)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
        logger.debug("Probe %s failed: %s", dev_url, e)
        return None

    status = data.get("status")
    devs = data.get("devs")
    sn = data.get("sn")

    if status != "0" or not devs or not sn:
        logger.debug(
            "Probe %s: invalid response (status=%s, devs=%s, sn=%s)",
            dev_url, status, devs, sn,
        )
        return None

    device_ids: list[int] = []
    for d in devs:
        try:
            device_ids.append(int(d))
        except (ValueError, TypeError):
            logger.debug("Probe %s: invalid dev entry %r", dev_url, d)
            continue

    if not device_ids:
        return None

    api_base_url = f"{base_url}/api/dev/{device_ids[0]}"
    devices: list[DeviceDetail] = []

    for did in device_ids:
        info_url = f"{base_url}/api/dev/{did}/info"
        try:
            async with session.get(
                info_url, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as info_resp:
                info_resp.raise_for_status()
                info_data = await info_resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            logger.debug("Info %s failed: %s", info_url, e)
            devices.append(
                DeviceDetail(
                    device_id=did,
                    model_id=0,
                    model_name="Unknown",
                    module_id=str(did),
                )
            )
            continue

        info_obj = info_data.get("info") or {}
        model_id = info_obj.get("id", 0)
        module_id = info_obj.get("moduleID", str(did))

        devices.append(
            DeviceDetail(
                device_id=did,
                model_id=model_id,
                model_name=_model_name(model_id),
                module_id=str(module_id),
            )
        )

    return KospelDeviceInfo(
        host=_extract_host(host),
        device_ids=device_ids,
        serial_number=str(sn),
        api_base_url=api_base_url,
        devices=devices,
    )


async def discover_devices(
    session: aiohttp.ClientSession,
    subnet: str,
    timeout: float = 3.0,
    concurrency_limit: int = 20,
) -> list[KospelDeviceInfo]:
    """
    Scan a subnet for Kospel C.MI devices.

    Args:
        session: aiohttp ClientSession
        subnet: CIDR notation (e.g. "192.168.101.0/24")
        timeout: Per-host probe timeout in seconds
        concurrency_limit: Max concurrent probes

    Returns:
        List of found KospelDeviceInfo
    """
    try:
        network = ipaddress.IPv4Network(subnet, strict=False)
    except ValueError as e:
        logger.debug("Invalid subnet %s: %s", subnet, e)
        return []

    hosts: list[str] = [str(h) for h in network.hosts()]
    sem = asyncio.Semaphore(concurrency_limit)

    async def probe_with_sem(host: str) -> Optional[KospelDeviceInfo]:
        async with sem:
            return await probe_device(session, host, timeout=timeout)

    results = await asyncio.gather(
        *[probe_with_sem(h) for h in hosts],
        return_exceptions=True,
    )

    found: list[KospelDeviceInfo] = []
    for r in results:
        if isinstance(r, Exception):
            logger.debug("Discover probe failed: %s", r)
        elif r is not None:
            found.append(r)

    return found
