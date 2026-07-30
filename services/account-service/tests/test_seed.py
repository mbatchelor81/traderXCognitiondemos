"""Seeding tests — seeds only accounts and account users for this tenant."""

from unittest.mock import patch

from app import seed
from app.models.account import Account, AccountUser
from tests.conftest import TEST_TENANT_ID, TestingSessionLocal


def test_seed_populates_accounts_and_users(db_session):
    with patch.object(seed, "SessionLocal", TestingSessionLocal):
        assert seed.seed_database() is True

    accounts = db_session.query(Account).all()
    assert {(a.id, a.display_name, a.tenant_id) for a in accounts} == {
        (22214, "Test Account 20", TEST_TENANT_ID),
        (11413, "Private Clients Fund TTXX", TEST_TENANT_ID),
    }

    users = db_session.query(AccountUser).all()
    assert {(u.account_id, u.username, u.tenant_id) for u in users} == {
        (22214, "jsmith", TEST_TENANT_ID),
        (22214, "jdoe", TEST_TENANT_ID),
        (11413, "mwilliams", TEST_TENANT_ID),
    }


def test_seed_skips_when_database_is_not_empty(db_session):
    with patch.object(seed, "SessionLocal", TestingSessionLocal):
        assert seed.seed_database() is True
        assert seed.seed_database() is False

    assert db_session.query(Account).count() == 2
