"""Direcciones de red local del equipo y validación del origen de las conexiones remotas."""

from __future__ import annotations

import ipaddress
import socket

import psutil

# Adaptadores que normalmente no sirven para que un celular llegue al equipo.
_VIRTUAL_HINTS = ("vethernet", "virtualbox", "vmware", "hyper-v", "wsl", "loopback", "docker", "tailscale", "zerotier", "vpn", "bluetooth")


def is_allowed_client(host: str | None, allow_loopback: bool = False) -> bool:
    """Solo se aceptan clientes de redes privadas (LAN, hotspot). Nunca direcciones públicas."""
    if not host:
        return False
    try:
        ip = ipaddress.ip_address(host.split("%", 1)[0])
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    if ip.is_loopback:
        return allow_loopback
    if ip.is_multicast or ip.is_unspecified or ip.is_reserved:
        return False
    return ip.is_private  # 10/8, 172.16/12, 192.168/16, 169.254/16 (enlace local)


def local_addresses() -> list[dict]:
    """IPv4 privadas de los adaptadores activos, con una marca de los que parecen virtuales."""
    stats = psutil.net_if_stats()
    out: list[dict] = []
    for name, addrs in psutil.net_if_addrs().items():
        st = stats.get(name)
        if st is not None and not st.isup:
            continue
        for a in addrs:
            if a.family != socket.AF_INET:
                continue
            try:
                ip = ipaddress.ip_address(a.address)
            except ValueError:
                continue
            if ip.is_loopback or not ip.is_private:
                continue
            virtual = any(h in name.lower() for h in _VIRTUAL_HINTS)
            out.append({"interfaz": name, "ip": a.address, "virtual": virtual, "enlace_local": ip.is_link_local})
    # Primero las físicas y las que no son de enlace local (169.254 indica DHCP fallido).
    out.sort(key=lambda d: (d["virtual"], d["enlace_local"], d["ip"]))
    return out


def device_name() -> str:
    return socket.gethostname() or "PC"
