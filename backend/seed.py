"""
One-off script to seed the initial superadmin account and the four
built-in BOQ items (fibre, rack, router, bandwidth) with sane default
rates, so you have something to log in with and working defaults on day
one. Admin can edit every rate (and, if needed, attach a custom formula)
from there.

Run with: uv run python seed.py
"""

from sqlmodel import Session, select

from app.core.config import DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD
from app.core.database import engine, init_db
from app.core.security import hash_password
from app.features.auth.model import AdminUser
from app.features.boq_items.model import BOQItem, ChargeType, ComputationMode

# key -> (name, rate, unit, charge_type, computation_mode)
DEFAULT_BOQ_ITEMS = {
    "fibre": (
        "Fibre cable run",
        2500.0,  # NGN per meter
        "m",
        ChargeType.ONE_OFF,
        ComputationMode.QUANTITY,  # amount = rate * distance_m
    ),
    "rack": (
        "12U rack",
        150000.0,  # flat NGN
        "each",
        ChargeType.ONE_OFF,
        ComputationMode.FLAT,
    ),
    "router": (
        "Router lease",
        25000.0,  # flat NGN, recurring
        "each",
        ChargeType.RECURRING,
        ComputationMode.FLAT,
    ),
    "bandwidth": (
        "Bandwidth",
        3500.0,  # NGN per Mbps, recurring
        "Mbps",
        ChargeType.RECURRING,
        ComputationMode.QUANTITY,  # amount = rate * bandwidth_mbps
    ),
}


def run():
    init_db()
    with Session(engine) as session:
        if not session.exec(
            select(AdminUser).where(AdminUser.email == DEFAULT_ADMIN_EMAIL)
        ).first():
            session.add(
                AdminUser(
                    email=DEFAULT_ADMIN_EMAIL,
                    full_name="Default Superadmin",
                    hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
                    is_superadmin=True,
                )
            )
            print(
                f"Created superadmin: {DEFAULT_ADMIN_EMAIL} / {DEFAULT_ADMIN_PASSWORD} "
                "(change this password, and set DEFAULT_ADMIN_EMAIL/PASSWORD in .env "
                "before running this in production!)"
            )

        for key, (name, rate, unit, charge_type, computation_mode) in DEFAULT_BOQ_ITEMS.items():
            if not session.exec(select(BOQItem).where(BOQItem.key == key)).first():
                session.add(
                    BOQItem(
                        key=key,
                        name=name,
                        rate=rate,
                        unit=unit,
                        charge_type=charge_type,
                        computation_mode=computation_mode,
                        is_custom=False,
                    )
                )
                print(f"Seeded BOQ item: {key} ({name}) = {rate}/{unit}")

        session.commit()


if __name__ == "__main__":
    run()