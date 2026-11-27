"""
Idempotent seed data for local development and E2E testing.
"""
import json
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.app_user import AppUser
from app.models.audit_log import AuditLog
from app.models.balance_breakdown import BalanceBreakdown
from app.models.balance_category import BalanceCategory
from app.models.balance_transfer import BalanceTransfer
from app.models.credit_card import CreditCard
from app.models.credit_card_account import CreditCardAccount
from app.models.customer import Customer
from app.models.direct_debit_mandate import DirectDebitMandate
from app.models.instalment_plan import InstalmentPlan
from app.models.money_transfer import MoneyTransfer
from app.models.offer import Offer
from app.models.payee import Payee
from app.models.payment import Payment
from app.models.rewards_programme import RewardsProgramme
from app.models.tracking_event import TrackingEvent
from app.models.transaction import Transaction


def seed_data():
    """Seed initial data for development and testing."""
    db = SessionLocal()

    try:
        # Seed admin user
        existing_admin = db.query(AppUser).filter(AppUser.email == "admin@example.com").first()

        if not existing_admin:
            admin_user = AppUser(
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            db.commit()
            print("✓ Seeded admin user: admin@example.com / admin123")
        else:
            print("✓ Admin user already exists")

        # Seed support user
        existing_support = db.query(AppUser).filter(AppUser.email == "support@example.com").first()

        if not existing_support:
            support_user = AppUser(
                email="support@example.com",
                hashed_password=hash_password("support123"),
                is_active=True,
                is_superuser=False
            )
            db.add(support_user)
            db.commit()
            print("✓ Seeded support user: support@example.com / support123")
        else:
            print("✓ Support user already exists")

        # Seed demo customer
        existing_customer = db.query(Customer).filter(Customer.external_customer_id == "CUST-001").first()

        if not existing_customer:
            customer = Customer(
                external_customer_id="CUST-001",
                masked_name="John D***",
                email="admin@example.com",
                phone_last_four="5678"
            )
            db.add(customer)
            db.flush()
            customer_id = customer.id
            print("✓ Seeded demo customer: CUST-001")
        else:
            customer_id = existing_customer.id
            print("✓ Demo customer already exists")

        # Seed demo accounts
        accounts_data = [
            {
                "account_number_masked": "****1001",
                "sort_code_masked": "12-34-56",
                "account_status": "Active",
                "credit_limit": Decimal("5000.00"),
                "available_credit": Decimal("3200.50"),
                "current_balance": Decimal("1799.50"),
                "minimum_payment_due": Decimal("89.98"),
                "payment_due_date": datetime.now() + timedelta(days=15),
            },
            {
                "account_number_masked": "****1002",
                "sort_code_masked": "12-34-56",
                "account_status": "Active",
                "credit_limit": Decimal("10000.00"),
                "available_credit": Decimal("7850.00"),
                "current_balance": Decimal("2150.00"),
                "minimum_payment_due": Decimal("107.50"),
                "payment_due_date": datetime.now() + timedelta(days=20),
            },
            {
                "account_number_masked": "****1003",
                "sort_code_masked": "12-34-56",
                "account_status": "Active",
                "credit_limit": Decimal("3000.00"),
                "available_credit": Decimal("2500.00"),
                "current_balance": Decimal("500.00"),
                "minimum_payment_due": Decimal("25.00"),
                "payment_due_date": datetime.now() + timedelta(days=10),
            },
        ]

        for i, account_data in enumerate(accounts_data, start=1):
            account_num = account_data["account_number_masked"]
            existing_account = db.query(CreditCardAccount).filter(
                CreditCardAccount.account_number_masked == account_num,
                CreditCardAccount.customer_id == customer_id
            ).first()

            if not existing_account:
                account = CreditCardAccount(
                    customer_id=customer_id,
                    **account_data
                )
                db.add(account)
                db.flush()

                # Add a card for each account
                card = CreditCard(
                    account_id=account.id,
                    card_number_masked=f"****-****-****-{1000 + i}",
                    card_type="Visa" if i % 2 == 1 else "Mastercard",
                    card_status="Active",
                    expiry_month=12,
                    expiry_year=2026
                )
                db.add(card)

                print(f"✓ Seeded account: ACC-100{i} ({account_num})")
            else:
                print(f"✓ Account ACC-100{i} already exists")

        # Seed demo balance transfers and instalment plans for account 1001
        acc_1001 = db.query(CreditCardAccount).filter(
            CreditCardAccount.account_number_masked == "****1001",
            CreditCardAccount.customer_id == customer_id
        ).first()

        if acc_1001:
            # Seed a balance transfer
            existing_bt = db.query(BalanceTransfer).filter(
                BalanceTransfer.external_transfer_id == "BT-2024-001"
            ).first()
            if not existing_bt:
                bt = BalanceTransfer(
                    account_id=acc_1001.id,
                    external_transfer_id="BT-2024-001",
                    idempotency_key=None,
                    transfer_amount=Decimal("500.00"),
                    promotional_rate=Decimal("0.00"),
                    promotional_period_months=12,
                    status="Completed",
                    processed_at=datetime.now() - timedelta(days=30),
                )
                db.add(bt)
                db.flush()
                bt_id = bt.id
                print("✓ Seeded balance transfer: BT-2024-001")
            else:
                bt_id = existing_bt.id
                print("✓ Balance transfer already exists")

            # Seed demo instalment plans (IP-1 to IP-3)
            instalment_plans_data = [
                {
                    "plan_reference": "IP-1",
                    "original_amount": Decimal("1200.00"),
                    "remaining_balance": Decimal("800.00"),
                    "instalment_count": 12,
                    "monthly_payment": Decimal("100.00"),
                    "apr": Decimal("9.90"),
                    "status": "Active",
                },
                {
                    "plan_reference": "IP-2",
                    "original_amount": Decimal("2400.00"),
                    "remaining_balance": Decimal("1800.00"),
                    "instalment_count": 24,
                    "monthly_payment": Decimal("100.00"),
                    "apr": Decimal("7.90"),
                    "status": "Active",
                },
                {
                    "plan_reference": "IP-3",
                    "original_amount": Decimal("600.00"),
                    "remaining_balance": Decimal("300.00"),
                    "instalment_count": 6,
                    "monthly_payment": Decimal("100.00"),
                    "apr": Decimal("0.00"),
                    "status": "Active",
                },
            ]

            ip_id = None
            for ip_data in instalment_plans_data:
                existing_ip = db.query(InstalmentPlan).filter(
                    InstalmentPlan.plan_reference == ip_data["plan_reference"]
                ).first()
                if not existing_ip:
                    ip = InstalmentPlan(account_id=acc_1001.id, **ip_data)
                    db.add(ip)
                    db.flush()
                    if ip_data["plan_reference"] == "IP-1":
                        ip_id = ip.id
                    print(f"✓ Seeded instalment plan: {ip_data['plan_reference']}")
                else:
                    if ip_data["plan_reference"] == "IP-1":
                        ip_id = existing_ip.id
                    print(f"✓ Instalment plan {ip_data['plan_reference']} already exists")

            # Seed balance breakdown for account 1001
            existing_breakdown = db.query(BalanceBreakdown).filter(
                BalanceBreakdown.account_id == acc_1001.id
            ).first()
            if not existing_breakdown:
                breakdown = BalanceBreakdown(
                    account_id=acc_1001.id,
                    total_balance=Decimal("1799.50"),
                    snapshot_date=datetime.now(),
                )
                db.add(breakdown)
                db.flush()

                # Add categories with display_rank, promo details, and source linkage
                categories = [
                    {
                        "category_name": "StandardPurchase",
                        "category_amount": Decimal("299.50"),
                        "apr": Decimal("19.90"),
                        "display_rank": 1,
                        "promo_rate": None,
                        "promo_end_date": None,
                        "source_balance_transfer_id": None,
                        "source_instalment_plan_id": None,
                    },
                    {
                        "category_name": "PromotionalPurchase",
                        "category_amount": Decimal("200.00"),
                        "apr": Decimal("0.00"),
                        "display_rank": 2,
                        "promo_rate": Decimal("0.00"),
                        "promo_end_date": datetime.now() + timedelta(days=90),
                        "source_balance_transfer_id": None,
                        "source_instalment_plan_id": None,
                    },
                    {
                        "category_name": "BalanceTransfer",
                        "category_amount": Decimal("500.00"),
                        "apr": Decimal("0.00"),
                        "display_rank": 3,
                        "promo_rate": Decimal("0.00"),
                        "promo_end_date": datetime.now() + timedelta(days=335),
                        "source_balance_transfer_id": bt_id,
                        "source_instalment_plan_id": None,
                    },
                    {
                        "category_name": "Instalment",
                        "category_amount": Decimal("800.00"),
                        "apr": Decimal("9.90"),
                        "display_rank": 4,
                        "promo_rate": None,
                        "promo_end_date": None,
                        "source_balance_transfer_id": None,
                        "source_instalment_plan_id": ip_id if ip_id else None,
                    },
                ]

                for cat_data in categories:
                    cat = BalanceCategory(breakdown_id=breakdown.id, **cat_data)
                    db.add(cat)

                print("✓ Seeded balance breakdown with 4 categories for account ACC-1001")
            else:
                print("✓ Balance breakdown already exists for ACC-1001")

            # Seed offers for account 1001
            offers_data = [
                {
                    "offer_code": "BT-PROMO-2024",
                    "offer_title": "0% Balance Transfer for 12 months",
                    "offer_description": "Transfer your balance and pay 0% interest for 12 months",
                    "offer_type": "BalanceTransfer",
                    "status": "Available",
                    "valid_from": datetime.now() - timedelta(days=10),
                    "valid_until": datetime.now() + timedelta(days=80),
                },
                {
                    "offer_code": "BT-EXTENDED-2024",
                    "offer_title": "0% Balance Transfer for 18 months",
                    "offer_description": "Extended offer: 0% interest for 18 months on balance transfers",
                    "offer_type": "BalanceTransfer",
                    "status": "Available",
                    "valid_from": datetime.now() - timedelta(days=5),
                    "valid_until": datetime.now() + timedelta(days=85),
                },
                {
                    "offer_code": "BT-STANDARD-2024",
                    "offer_title": "3.9% Balance Transfer for 24 months",
                    "offer_description": "Low rate balance transfer for 24 months",
                    "offer_type": "BalanceTransfer",
                    "status": "Active",
                    "valid_from": datetime.now() - timedelta(days=20),
                    "valid_until": datetime.now() + timedelta(days=70),
                },
                {
                    "offer_code": "RWD-DOUBLE-2024",
                    "offer_title": "Double Rewards Points",
                    "offer_description": "Earn 2x rewards points on all purchases",
                    "offer_type": "Rewards",
                    "status": "Available",
                    "valid_from": datetime.now() - timedelta(days=15),
                    "valid_until": datetime.now() + timedelta(days=75),
                },
                {
                    "offer_code": "RWD-CASHBACK-2024",
                    "offer_title": "5% Cashback on Groceries",
                    "offer_description": "Get 5% cashback on grocery purchases",
                    "offer_type": "Rewards",
                    "status": "Available",
                    "valid_from": datetime.now() - timedelta(days=8),
                    "valid_until": datetime.now() + timedelta(days=82),
                },
                {
                    "offer_code": "INS-FLEXI-2024",
                    "offer_title": "Flexible Instalment Plan",
                    "offer_description": "Convert purchases to instalments with low monthly payments",
                    "offer_type": "Instalment",
                    "status": "Available",
                    "valid_from": datetime.now() - timedelta(days=12),
                    "valid_until": datetime.now() + timedelta(days=78),
                },
            ]

            for offer_data in offers_data:
                existing_offer = db.query(Offer).filter(
                    Offer.offer_code == offer_data["offer_code"]
                ).first()
                if not existing_offer:
                    offer = Offer(account_id=acc_1001.id, **offer_data)
                    db.add(offer)

            print("✓ Seeded 6 offers for account ACC-1001")

            # Seed demo transactions for account 1001 (20 transactions with Pending and Posted status)
            existing_txn_count = db.query(Transaction).filter(
                Transaction.account_id == acc_1001.id
            ).count()

            if existing_txn_count == 0:
                transactions_data = [
                    # Posted transactions
                    {"external_transaction_id": "TXN-001", "transaction_date": datetime.now() - timedelta(days=5), "posting_date": datetime.now() - timedelta(days=3), "merchant_name": "Grocery Store", "transaction_type": "Purchase", "amount": Decimal("45.67"), "currency": "GBP", "status": "Posted", "description": "Weekly groceries"},
                    {"external_transaction_id": "TXN-002", "transaction_date": datetime.now() - timedelta(days=6), "posting_date": datetime.now() - timedelta(days=4), "merchant_name": "Coffee Shop", "transaction_type": "Purchase", "amount": Decimal("4.50"), "currency": "GBP", "status": "Posted", "description": "Morning coffee"},
                    {"external_transaction_id": "TXN-003", "transaction_date": datetime.now() - timedelta(days=7), "posting_date": datetime.now() - timedelta(days=5), "merchant_name": "Gas Station", "transaction_type": "Purchase", "amount": Decimal("52.00"), "currency": "GBP", "status": "Posted", "description": "Fuel purchase"},
                    {"external_transaction_id": "TXN-004", "transaction_date": datetime.now() - timedelta(days=8), "posting_date": datetime.now() - timedelta(days=6), "merchant_name": "Restaurant", "transaction_type": "Purchase", "amount": Decimal("38.90"), "currency": "GBP", "status": "Posted", "description": "Dinner"},
                    {"external_transaction_id": "TXN-005", "transaction_date": datetime.now() - timedelta(days=9), "posting_date": datetime.now() - timedelta(days=7), "merchant_name": "Online Retailer", "transaction_type": "Purchase", "amount": Decimal("79.99"), "currency": "GBP", "status": "Posted", "description": "Online shopping"},
                    {"external_transaction_id": "TXN-006", "transaction_date": datetime.now() - timedelta(days=10), "posting_date": datetime.now() - timedelta(days=8), "merchant_name": "Pharmacy", "transaction_type": "Purchase", "amount": Decimal("12.50"), "currency": "GBP", "status": "Posted", "description": "Medicine"},
                    {"external_transaction_id": "TXN-007", "transaction_date": datetime.now() - timedelta(days=11), "posting_date": datetime.now() - timedelta(days=9), "merchant_name": "Cinema", "transaction_type": "Purchase", "amount": Decimal("22.00"), "currency": "GBP", "status": "Posted", "description": "Movie tickets"},
                    {"external_transaction_id": "TXN-008", "transaction_date": datetime.now() - timedelta(days=12), "posting_date": datetime.now() - timedelta(days=10), "merchant_name": "Bookstore", "transaction_type": "Purchase", "amount": Decimal("34.99"), "currency": "GBP", "status": "Posted", "description": "Books"},
                    {"external_transaction_id": "TXN-009", "transaction_date": datetime.now() - timedelta(days=13), "posting_date": datetime.now() - timedelta(days=11), "merchant_name": "Utility Company", "transaction_type": "Purchase", "amount": Decimal("95.00"), "currency": "GBP", "status": "Posted", "description": "Electricity bill"},
                    {"external_transaction_id": "TXN-010", "transaction_date": datetime.now() - timedelta(days=14), "posting_date": datetime.now() - timedelta(days=12), "merchant_name": "Gym", "transaction_type": "Purchase", "amount": Decimal("45.00"), "currency": "GBP", "status": "Posted", "description": "Monthly membership"},
                    {"external_transaction_id": "TXN-011", "transaction_date": datetime.now() - timedelta(days=15), "posting_date": datetime.now() - timedelta(days=13), "merchant_name": "Streaming Service", "transaction_type": "Purchase", "amount": Decimal("12.99"), "currency": "GBP", "status": "Posted", "description": "Subscription"},
                    {"external_transaction_id": "TXN-012", "transaction_date": datetime.now() - timedelta(days=16), "posting_date": datetime.now() - timedelta(days=14), "merchant_name": "Hardware Store", "transaction_type": "Purchase", "amount": Decimal("67.50"), "currency": "GBP", "status": "Posted", "description": "DIY supplies"},
                    {"external_transaction_id": "TXN-013", "transaction_date": datetime.now() - timedelta(days=17), "posting_date": datetime.now() - timedelta(days=15), "merchant_name": "Pet Store", "transaction_type": "Purchase", "amount": Decimal("28.00"), "currency": "GBP", "status": "Posted", "description": "Pet food"},
                    {"external_transaction_id": "TXN-014", "transaction_date": datetime.now() - timedelta(days=18), "posting_date": datetime.now() - timedelta(days=16), "merchant_name": "Department Store", "transaction_type": "Purchase", "amount": Decimal("156.00"), "currency": "GBP", "status": "Posted", "description": "Clothing"},
                    # Pending transactions (no posting_date)
                    {"external_transaction_id": "TXN-015", "transaction_date": datetime.now() - timedelta(days=1), "posting_date": None, "merchant_name": "Coffee Shop", "transaction_type": "Purchase", "amount": Decimal("4.80"), "currency": "GBP", "status": "Pending", "description": "Coffee"},
                    {"external_transaction_id": "TXN-016", "transaction_date": datetime.now() - timedelta(days=1), "posting_date": None, "merchant_name": "Grocery Store", "transaction_type": "Purchase", "amount": Decimal("32.45"), "currency": "GBP", "status": "Pending", "description": "Groceries"},
                    {"external_transaction_id": "TXN-017", "transaction_date": datetime.now() - timedelta(hours=18), "posting_date": None, "merchant_name": "Restaurant", "transaction_type": "Purchase", "amount": Decimal("42.00"), "currency": "GBP", "status": "Pending", "description": "Lunch"},
                    {"external_transaction_id": "TXN-018", "transaction_date": datetime.now() - timedelta(hours=12), "posting_date": None, "merchant_name": "Gas Station", "transaction_type": "Purchase", "amount": Decimal("48.00"), "currency": "GBP", "status": "Pending", "description": "Fuel"},
                    {"external_transaction_id": "TXN-019", "transaction_date": datetime.now() - timedelta(hours=6), "posting_date": None, "merchant_name": "Online Store", "transaction_type": "Purchase", "amount": Decimal("89.99"), "currency": "GBP", "status": "Pending", "description": "Online purchase"},
                    {"external_transaction_id": "TXN-020", "transaction_date": datetime.now() - timedelta(hours=2), "posting_date": None, "merchant_name": "Pharmacy", "transaction_type": "Purchase", "amount": Decimal("15.50"), "currency": "GBP", "status": "Pending", "description": "Medicine"},
                ]

                for txn_data in transactions_data:
                    txn = Transaction(account_id=acc_1001.id, **txn_data)
                    db.add(txn)

                print("✓ Seeded 20 transactions (14 Posted, 6 Pending) for account ACC-1001")
            else:
                print("✓ Transactions already exist for ACC-1001")

            # Seed demo payments for account 1001 (PMT-1 to PMT-7)
            payments_data = [
                # PMT-1: Completed OneOff
                {"external_payment_id": "PMT-1", "idempotency_key": None, "payment_method": "BankTransfer", "amount": Decimal("100.00"), "currency": "GBP", "status": "Completed", "scheduled_date": None, "processed_at": datetime.now() - timedelta(days=10)},
                # PMT-2: Processing Scheduled
                {"external_payment_id": "PMT-2", "idempotency_key": None, "payment_method": "BankTransfer", "amount": Decimal("150.00"), "currency": "GBP", "status": "Processing", "scheduled_date": datetime.now() + timedelta(days=5), "processed_at": None},
                # PMT-3: Failed OneOff
                {"external_payment_id": "PMT-3", "idempotency_key": None, "payment_method": "DebitCard", "amount": Decimal("200.00"), "currency": "GBP", "status": "Failed", "scheduled_date": None, "processed_at": datetime.now() - timedelta(days=3)},
                # PMT-4: Submitted Scheduled
                {"external_payment_id": "PMT-4", "idempotency_key": None, "payment_method": "BankTransfer", "amount": Decimal("250.00"), "currency": "GBP", "status": "Submitted", "scheduled_date": datetime.now() + timedelta(days=10), "processed_at": None},
                # PMT-5: Cancelled Scheduled
                {"external_payment_id": "PMT-5", "idempotency_key": None, "payment_method": "BankTransfer", "amount": Decimal("180.00"), "currency": "GBP", "status": "Cancelled", "scheduled_date": datetime.now() + timedelta(days=15), "processed_at": None},
                # PMT-6: Completed DirectDebitCollection
                {"external_payment_id": "PMT-6", "idempotency_key": None, "payment_method": "DirectDebit", "amount": Decimal("89.98"), "currency": "GBP", "status": "Completed", "scheduled_date": datetime.now() - timedelta(days=5), "processed_at": datetime.now() - timedelta(days=5)},
                # PMT-7: Restricted Scheduled
                {"external_payment_id": "PMT-7", "idempotency_key": None, "payment_method": "BankTransfer", "amount": Decimal("500.00"), "currency": "GBP", "status": "Restricted", "scheduled_date": datetime.now() + timedelta(days=20), "processed_at": None},
            ]

            for pmt_data in payments_data:
                existing_payment = db.query(Payment).filter(
                    Payment.external_payment_id == pmt_data["external_payment_id"]
                ).first()
                if not existing_payment:
                    pmt = Payment(account_id=acc_1001.id, **pmt_data)
                    db.add(pmt)
                    db.flush()

                    # Add tracking events for each payment
                    if pmt_data["status"] == "Completed":
                        events = [
                            {"event_type": "submitted", "status": "Submitted", "occurred_at": pmt_data["processed_at"] - timedelta(hours=24)},
                            {"event_type": "processing", "status": "Processing", "occurred_at": pmt_data["processed_at"] - timedelta(hours=12)},
                            {"event_type": "completed", "status": "Completed", "occurred_at": pmt_data["processed_at"]},
                        ]
                    elif pmt_data["status"] == "Processing":
                        events = [
                            {"event_type": "submitted", "status": "Submitted", "occurred_at": datetime.now() - timedelta(hours=6)},
                            {"event_type": "processing", "status": "Processing", "occurred_at": datetime.now() - timedelta(hours=3)},
                        ]
                    elif pmt_data["status"] == "Failed":
                        events = [
                            {"event_type": "submitted", "status": "Submitted", "occurred_at": pmt_data["processed_at"] - timedelta(hours=12)},
                            {"event_type": "failed", "status": "Failed", "occurred_at": pmt_data["processed_at"]},
                        ]
                    elif pmt_data["status"] == "Submitted":
                        events = [
                            {"event_type": "submitted", "status": "Submitted", "occurred_at": datetime.now() - timedelta(hours=2)},
                        ]
                    elif pmt_data["status"] == "Cancelled":
                        events = [
                            {"event_type": "submitted", "status": "Submitted", "occurred_at": datetime.now() - timedelta(days=1)},
                            {"event_type": "cancelled", "status": "Cancelled", "occurred_at": datetime.now() - timedelta(hours=12)},
                        ]
                    elif pmt_data["status"] == "Restricted":
                        events = [
                            {"event_type": "submitted", "status": "Submitted", "occurred_at": datetime.now() - timedelta(hours=4)},
                            {"event_type": "restricted", "status": "Restricted", "occurred_at": datetime.now() - timedelta(hours=2)},
                        ]
                    else:
                        events = []

                    for evt_data in events:
                        tracking_event = TrackingEvent(
                            entity_type="Payment",
                            entity_id=str(pmt.id),
                            event_type=evt_data["event_type"],
                            status=evt_data["status"],
                            event_data=f"Payment {pmt_data['external_payment_id']} {evt_data['status'].lower()}",
                            correlation_id=None,
                            occurred_at=evt_data["occurred_at"]
                        )
                        db.add(tracking_event)

            print("✓ Seeded 7 payments (PMT-1 to PMT-7) with tracking events for account ACC-1001")

            # Seed demo direct debit mandates
            # ACC-1001: Active MinimumPayment
            # ACC-1002: Pending StatementBalance
            # ACC-1003: Cancelled FixedAmount
            acc_1002 = db.query(CreditCardAccount).filter(
                CreditCardAccount.account_number_masked == "****1002",
                CreditCardAccount.customer_id == customer_id
            ).first()
            acc_1003 = db.query(CreditCardAccount).filter(
                CreditCardAccount.account_number_masked == "****1003",
                CreditCardAccount.customer_id == customer_id
            ).first()

            mandates_data = [
                {"account_id": acc_1001.id, "mandate_reference": "DD-1001-MIN", "mandate_type": "MinimumPayment", "payment_amount": None, "status": "Active", "activated_at": datetime.now() - timedelta(days=60)},
                {"account_id": acc_1002.id if acc_1002 else None, "mandate_reference": "DD-1002-STMT", "mandate_type": "StatementBalance", "payment_amount": None, "status": "Pending", "activated_at": None},
                {"account_id": acc_1003.id if acc_1003 else None, "mandate_reference": "DD-1003-FIXED", "mandate_type": "FixedAmount", "payment_amount": Decimal("50.00"), "status": "Cancelled", "activated_at": datetime.now() - timedelta(days=90)},
            ]

            for mandate_data in mandates_data:
                if mandate_data["account_id"]:
                    existing_mandate = db.query(DirectDebitMandate).filter(
                        DirectDebitMandate.mandate_reference == mandate_data["mandate_reference"]
                    ).first()
                    if not existing_mandate:
                        mandate = DirectDebitMandate(**mandate_data)
                        db.add(mandate)

            print("✓ Seeded 3 direct debit mandates (ACC-1001: Active MinimumPayment, ACC-1002: Pending StatementBalance, ACC-1003: Cancelled FixedAmount)")

            # Seed demo balance transfers (BT-1 to BT-7)
            balance_transfers_data = [
                # BT-1: Submitted
                {"external_transfer_id": "BT-1", "account_id": acc_1001.id, "transfer_amount": Decimal("1000.00"), "promotional_rate": Decimal("0.00"), "promotional_period_months": 12, "status": "Submitted", "processed_at": None},
                # BT-2: ReviewRequired
                {"external_transfer_id": "BT-2", "account_id": acc_1001.id, "transfer_amount": Decimal("1500.00"), "promotional_rate": Decimal("0.00"), "promotional_period_months": 18, "status": "ReviewRequired", "processed_at": None},
                # BT-3: Completed with promo context (linked to category)
                {"external_transfer_id": "BT-3", "account_id": acc_1001.id, "transfer_amount": Decimal("500.00"), "promotional_rate": Decimal("0.00"), "promotional_period_months": 12, "status": "Completed", "processed_at": datetime.now() - timedelta(days=30)},
                # BT-4: Completed with promo context
                {"external_transfer_id": "BT-4", "account_id": acc_1001.id, "transfer_amount": Decimal("800.00"), "promotional_rate": Decimal("3.90"), "promotional_period_months": 24, "status": "Completed", "processed_at": datetime.now() - timedelta(days=60)},
                # BT-5: Rejected with guidance
                {"external_transfer_id": "BT-5", "account_id": acc_1001.id, "transfer_amount": Decimal("2000.00"), "promotional_rate": None, "promotional_period_months": None, "status": "Rejected", "processed_at": datetime.now() - timedelta(days=5)},
                # BT-6: Completed
                {"external_transfer_id": "BT-6", "account_id": acc_1001.id, "transfer_amount": Decimal("600.00"), "promotional_rate": Decimal("0.00"), "promotional_period_months": 12, "status": "Completed", "processed_at": datetime.now() - timedelta(days=45)},
                # BT-7: Submitted
                {"external_transfer_id": "BT-7", "account_id": acc_1001.id, "transfer_amount": Decimal("750.00"), "promotional_rate": Decimal("0.00"), "promotional_period_months": 12, "status": "Submitted", "processed_at": None},
            ]

            for bt_data in balance_transfers_data:
                existing_bt = db.query(BalanceTransfer).filter(
                    BalanceTransfer.external_transfer_id == bt_data["external_transfer_id"]
                ).first()
                if not existing_bt:
                    bt = BalanceTransfer(**bt_data)
                    db.add(bt)
                    db.flush()

                    # Add tracking events
                    bt_id = bt.id
                    bt_ref = bt_data["external_transfer_id"]

                    if bt_data["status"] == "Submitted":
                        events = [
                            {"event_type": "submitted", "status": "Submitted", "occurred_at": datetime.now() - timedelta(hours=2)},
                        ]
                    elif bt_data["status"] == "ReviewRequired":
                        events = [
                            {"event_type": "submitted", "status": "Submitted", "occurred_at": datetime.now() - timedelta(days=1)},
                            {"event_type": "review_required", "status": "ReviewRequired", "occurred_at": datetime.now() - timedelta(hours=12)},
                        ]
                    elif bt_data["status"] == "Completed":
                        events = [
                            {"event_type": "submitted", "status": "Submitted", "occurred_at": bt_data["processed_at"] - timedelta(days=2)},
                            {"event_type": "processing", "status": "Processing", "occurred_at": bt_data["processed_at"] - timedelta(days=1)},
                            {"event_type": "completed", "status": "Completed", "occurred_at": bt_data["processed_at"]},
                        ]
                    elif bt_data["status"] == "Rejected":
                        events = [
                            {"event_type": "submitted", "status": "Submitted", "occurred_at": bt_data["processed_at"] - timedelta(days=1)},
                            {"event_type": "rejected", "status": "Rejected", "occurred_at": bt_data["processed_at"]},
                        ]
                    else:
                        events = []

                    for evt_data in events:
                        tracking_event = TrackingEvent(
                            entity_type="BalanceTransfer",
                            entity_id=str(bt_id),
                            event_type=evt_data["event_type"],
                            status=evt_data["status"],
                            event_data=f"Balance transfer {bt_ref} {evt_data['status'].lower()}",
                            correlation_id=None,
                            occurred_at=evt_data["occurred_at"]
                        )
                        db.add(tracking_event)

            print("✓ Seeded 7 balance transfers (BT-1 to BT-7) with tracking events for account ACC-1001")

            # Seed demo payees for money transfers
            payees_data = [
                {"account_id": acc_1001.id, "payee_name": "John Smith", "account_number_masked": "****1234", "sort_code_masked": "12-34-56", "is_active": True},
                {"account_id": acc_1001.id, "payee_name": "Jane Doe", "account_number_masked": "****5678", "sort_code_masked": "98-76-54", "is_active": True},
                {"account_id": acc_1001.id, "payee_name": "ACME Corp", "account_number_masked": "****9012", "sort_code_masked": "11-22-33", "is_active": True},
            ]

            payee_ids = []
            for payee_data in payees_data:
                existing_payee = db.query(Payee).filter(
                    Payee.payee_name == payee_data["payee_name"],
                    Payee.account_id == payee_data["account_id"]
                ).first()
                if not existing_payee:
                    payee = Payee(**payee_data)
                    db.add(payee)
                    db.flush()
                    payee_ids.append(payee.id)
                else:
                    payee_ids.append(existing_payee.id)

            print("✓ Seeded 3 payees for account ACC-1001")

            # Seed demo money transfers (MT-1 to MT-4)
            if len(payee_ids) >= 3:
                money_transfers_data = [
                    # MT-1: Submitted
                    {"external_transfer_id": "MT-1", "account_id": acc_1001.id, "payee_id": payee_ids[0], "amount": Decimal("100.00"), "currency": "GBP", "status": "Submitted", "processed_at": None},
                    # MT-2: Processing
                    {"external_transfer_id": "MT-2", "account_id": acc_1001.id, "payee_id": payee_ids[1], "amount": Decimal("250.00"), "currency": "GBP", "status": "Processing", "processed_at": None},
                    # MT-3: Completed
                    {"external_transfer_id": "MT-3", "account_id": acc_1001.id, "payee_id": payee_ids[0], "amount": Decimal("150.00"), "currency": "GBP", "status": "Completed", "processed_at": datetime.now() - timedelta(days=3)},
                    # MT-4: Failed with guidance, Blocked with escalation
                    {"external_transfer_id": "MT-4", "account_id": acc_1001.id, "payee_id": payee_ids[2], "amount": Decimal("500.00"), "currency": "GBP", "status": "Blocked", "processed_at": datetime.now() - timedelta(hours=12)},
                ]

                for mt_data in money_transfers_data:
                    existing_mt = db.query(MoneyTransfer).filter(
                        MoneyTransfer.external_transfer_id == mt_data["external_transfer_id"]
                    ).first()
                    if not existing_mt:
                        mt = MoneyTransfer(**mt_data)
                        db.add(mt)
                        db.flush()

                        # Add tracking events
                        mt_id = mt.id
                        mt_ref = mt_data["external_transfer_id"]

                        if mt_data["status"] == "Submitted":
                            events = [
                                {"event_type": "submitted", "status": "Submitted", "occurred_at": datetime.now() - timedelta(hours=1)},
                            ]
                        elif mt_data["status"] == "Processing":
                            events = [
                                {"event_type": "submitted", "status": "Submitted", "occurred_at": datetime.now() - timedelta(hours=6)},
                                {"event_type": "processing", "status": "Processing", "occurred_at": datetime.now() - timedelta(hours=3)},
                            ]
                        elif mt_data["status"] == "Completed":
                            events = [
                                {"event_type": "submitted", "status": "Submitted", "occurred_at": mt_data["processed_at"] - timedelta(days=1)},
                                {"event_type": "processing", "status": "Processing", "occurred_at": mt_data["processed_at"] - timedelta(hours=12)},
                                {"event_type": "completed", "status": "Completed", "occurred_at": mt_data["processed_at"]},
                            ]
                        elif mt_data["status"] == "Blocked":
                            events = [
                                {"event_type": "submitted", "status": "Submitted", "occurred_at": mt_data["processed_at"] - timedelta(hours=6)},
                                {"event_type": "blocked", "status": "Blocked", "occurred_at": mt_data["processed_at"]},
                            ]
                        else:
                            events = []

                        for evt_data in events:
                            tracking_event = TrackingEvent(
                                entity_type="MoneyTransfer",
                                entity_id=str(mt_id),
                                event_type=evt_data["event_type"],
                                status=evt_data["status"],
                                event_data=f"Money transfer {mt_ref} {evt_data['status'].lower()}",
                                correlation_id=None,
                                occurred_at=evt_data["occurred_at"]
                            )
                            db.add(tracking_event)

                print("✓ Seeded 4 money transfers (MT-1 to MT-4) with tracking events for account ACC-1001")

            # Seed demo rewards programmes
            # ACC-1001: Active Rewards Plus programme with 1250 points
            # ACC-1002: null programme (no rewards)
            rewards_programmes_data = [
                {"account_id": acc_1001.id, "programme_name": "Rewards Plus", "points_balance": 1250, "status": "Active"},
            ]

            for rp_data in rewards_programmes_data:
                existing_rp = db.query(RewardsProgramme).filter(
                    RewardsProgramme.account_id == rp_data["account_id"]
                ).first()
                if not existing_rp:
                    rp = RewardsProgramme(**rp_data)
                    db.add(rp)

            print("✓ Seeded rewards programme for ACC-1001 (Rewards Plus, 1250 points)")

            # Seed demo audit events
            audit_events_data = [
                {"user_id": existing_admin.id if existing_admin else 1, "action": "login", "entity_type": "user", "entity_id": str(existing_admin.id if existing_admin else 1), "severity": "info", "details": json.dumps({"retention_class": "access_2y", "ip_address": "192.168.1.1"}), "occurred_at": datetime.now() - timedelta(days=1)},
                {"user_id": existing_admin.id if existing_admin else 1, "action": "logout", "entity_type": "user", "entity_id": str(existing_admin.id if existing_admin else 1), "severity": "info", "details": json.dumps({"retention_class": "access_2y"}), "occurred_at": datetime.now() - timedelta(hours=12)},
                {"user_id": existing_admin.id if existing_admin else 1, "action": "step_up", "entity_type": "user", "entity_id": str(existing_admin.id if existing_admin else 1), "severity": "info", "details": json.dumps({"retention_class": "access_2y", "scope": "payment"}), "occurred_at": datetime.now() - timedelta(hours=6)},
            ]

            for audit_data in audit_events_data:
                audit_log = AuditLog(**audit_data)
                db.add(audit_log)

            print("✓ Seeded demo audit events (login, logout, step-up)")

        db.commit()
        print("✓ Seed data completed successfully")

    except Exception as e:
        db.rollback()
        print(f"✗ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
