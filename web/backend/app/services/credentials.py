"""Credential CRUD service for PM integrations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.pm_credential import PMCredential
from .auth import decrypt_credentials, encrypt_credentials

VALID_SERVICES = {"linear", "jira", "notion"}


async def save_credential(
    db: AsyncSession,
    user_id,
    service: str,
    creds: dict,
    encryption_key: str,
) -> PMCredential:
    """Upsert a PM credential for user+service. Encrypts if key is set."""
    stored = creds
    if encryption_key:
        stored = {"encrypted": encrypt_credentials(creds, encryption_key)}

    result = await db.execute(
        select(PMCredential).where(
            PMCredential.user_id == user_id,
            PMCredential.service == service,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.credentials = stored
        return existing

    credential = PMCredential(
        user_id=user_id,
        service=service,
        credentials=stored,
    )
    db.add(credential)
    await db.flush()
    await db.refresh(credential)
    return credential


async def get_credential(
    db: AsyncSession,
    user_id,
    service: str,
    encryption_key: str,
) -> dict | None:
    """Fetch and decrypt credentials for user+service. Returns None if not found."""
    result = await db.execute(
        select(PMCredential).where(
            PMCredential.user_id == user_id,
            PMCredential.service == service,
        )
    )
    cred = result.scalar_one_or_none()
    if cred is None:
        return None

    stored = cred.credentials
    if encryption_key and "encrypted" in stored:
        return decrypt_credentials(stored["encrypted"], encryption_key)
    return stored


async def delete_credential(db: AsyncSession, user_id, service: str) -> bool:
    """Delete a PM credential. Returns True if deleted, False if not found."""
    result = await db.execute(
        select(PMCredential).where(
            PMCredential.user_id == user_id,
            PMCredential.service == service,
        )
    )
    cred = result.scalar_one_or_none()
    if cred is None:
        return False
    await db.delete(cred)
    return True


async def list_credentials(db: AsyncSession, user_id) -> list[PMCredential]:
    """List all PM credentials for a user (metadata only, no secrets)."""
    result = await db.execute(
        select(PMCredential).where(PMCredential.user_id == user_id)
    )
    return list(result.scalars().all())


async def validate_credential(service: str, creds: dict) -> tuple[bool, str]:
    """Instantiate PM client and test credentials. Returns (valid, message)."""
    try:
        if service == "linear":
            from arcane.core.project_management import LinearClient
            client = LinearClient(api_key=creds["api_key"])
        elif service == "jira":
            from arcane.core.project_management import JiraClient
            client = JiraClient(
                domain=creds["domain"],
                email=creds["email"],
                api_token=creds["api_token"],
            )
        elif service == "notion":
            from arcane.core.project_management import NotionClient
            client = NotionClient(api_key=creds["api_key"])
        else:
            return False, f"Unknown service: {service}"

        valid = await client.validate_credentials()
        if valid:
            return True, f"{service.capitalize()} credentials are valid"
        return False, f"{service.capitalize()} credentials are invalid"
    except KeyError as e:
        return False, f"Missing required credential field: {e}"
    except Exception as e:
        return False, f"Validation failed: {e}"
