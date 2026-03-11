from fastapi import Header


def get_tenant_id(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")) -> str:
    """
    Minimal tenant namespace.

    Missing header falls back to a shared default tenant so older tests and
    local flows do not immediately break.
    """
    if x_tenant_id is None:
        return "default"

    tenant_id = x_tenant_id.strip()
    if not tenant_id:
        return "default"

    return tenant_id