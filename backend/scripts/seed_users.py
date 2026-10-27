"""Safe provisioning script for initial SOC accounts in development / staging environments.

Creates baseline demonstration accounts without hardcoding credentials in source control:
- Reads optional passwords from environment variables (e.g. INITIAL_ADMIN_PASSWORD)
- If not provided, generates cryptographically random passwords and displays them safely
- Hashes all passwords using bcrypt (rounds=12)
"""

import os
import secrets
import string
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text

from app.core.security import hash_password
from app.database import SessionLocal, engine
from app.models.base import Base
from app.models.user import User, UserRole, UserStatus


def generate_secure_password(length: int = 16) -> str:
    """Generates an alphanumeric password with special characters satisfying SOC complexity."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        # Ensure at least 1 uppercase, 1 lowercase, 1 digit, 1 special
        if (
            any(c.isupper() for c in pwd)
            and any(c.islower() for c in pwd)
            and any(c.isdigit() for c in pwd)
            and any(c in "!@#$%^&*()_+-=" for c in pwd)
        ):
            return pwd


DEMO_PROFILES = [
    {
        "username": "admin",
        "email": "admin@sentinel.local",
        "full_name": "Chief Security Architect (Admin)",
        "role": UserRole.ADMIN,
        "env_var": "INITIAL_ADMIN_PASSWORD",
    },
    {
        "username": "lead_responder",
        "email": "lead_responder@sentinel.local",
        "full_name": "Alex Vance (Incident Responder)",
        "role": UserRole.INCIDENT_RESPONDER,
        "env_var": "INITIAL_RESPONDER_PASSWORD",
    },
    {
        "username": "det_engineer",
        "email": "det_engineer@sentinel.local",
        "full_name": "Elena Rostova (Detection Engineer)",
        "role": UserRole.DETECTION_ENGINEER,
        "env_var": "INITIAL_ENGINEER_PASSWORD",
    },
    {
        "username": "tier1_analyst",
        "email": "tier1_analyst@sentinel.local",
        "full_name": "Robin Miller (Tier 1 Triage)",
        "role": UserRole.ANALYST_TIER_1,
        "env_var": "INITIAL_ANALYST_PASSWORD",
    },
    {
        "username": "soc_manager",
        "email": "soc_manager@sentinel.local",
        "full_name": "Morgan Chen (SOC Operations Manager)",
        "role": UserRole.SOC_MANAGER,
        "env_var": "INITIAL_MANAGER_PASSWORD",
    },
]


def seed_demo_users():
    print("=" * 70)
    print("  Sentinel SOC Platform — Demonstration User Provisioning")
    print("=" * 70)

    try:
        db = SessionLocal()
        # Verify connectivity and ensure schemas exist
        db.execute(text("SELECT 1"))
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        print("[!] Database connection failed:", str(exc).split("\n")[0])
        print("    Ensure PostgreSQL is active, or configure DATABASE_URL in .env")
        print("    Example SQLite fallback: DATABASE_URL=sqlite:///./sentinel_dev.db")
        return

    try:
        for profile in DEMO_PROFILES:
            username = profile["username"]
            existing = db.query(User).filter(User.username == username).first()

            # Determine password
            env_pwd = os.getenv(profile["env_var"])
            plain_pwd = env_pwd if env_pwd else generate_secure_password()

            if existing:
                print(f"[*] Account '{username}' ({profile['role'].value}) already exists in database.")
                # If explicit environment password provided, update it
                if env_pwd:
                    existing.hashed_password = hash_password(env_pwd)
                    existing.status = UserStatus.ACTIVE
                    db.commit()
                    print(f"    -> Updated password from {profile['env_var']}.")
                continue

            hashed = hash_password(plain_pwd)
            new_user = User(
                username=username,
                email=profile["email"],
                full_name=profile["full_name"],
                hashed_password=hashed,
                role=profile["role"],
                status=UserStatus.ACTIVE,
            )
            db.add(new_user)
            db.commit()

            print(f"[+] Provisioned: {username:<16} | Role: {profile['role'].value:<18}")
            print(f"    Email:    {profile['email']}")
            print(f"    Password: {plain_pwd}")
            print("-" * 70)

        print("\n[!] IMPORTANT: Store these credentials securely. They are not stored in source code.")
        print("    In production, configure INITIAL_*_PASSWORD in .env before first startup.\n")

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_users()
