"""Tests for schema migrations.

An existing data/control.db must survive an upgrade with its data intact -
that is the whole reason migrations exist rather than editing SCHEMA.
"""

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from assistant.control.store import MIGRATIONS, ControlStore
from assistant.control.models import Device, Task


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="vave-migration-test-")
        self.path = Path(self.tempdir) / "control.db"

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_a_fresh_database_records_every_migration(self):
        store = ControlStore(self.path)
        self.addCleanup(store.close)

        self.assertEqual([name for name, _ in MIGRATIONS], store.schema_versions())

    def test_migrations_are_not_applied_twice(self):
        first = ControlStore(self.path)
        first.close()

        second = ControlStore(self.path)
        self.addCleanup(second.close)

        self.assertEqual(len(MIGRATIONS), len(second.schema_versions()))

    def test_an_older_database_is_upgraded_without_losing_data(self):
        # A database as it looked before device pairing existed.
        legacy = sqlite3.connect(str(self.path))
        legacy.executescript("""
            CREATE TABLE devices (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL,
                platform TEXT, status TEXT NOT NULL, last_seen REAL NOT NULL);
            INSERT INTO devices VALUES ('d1', 'Old laptop', 'computer',
                                        'linux', 'online', 1.0);
        """)
        legacy.commit()
        legacy.close()

        store = ControlStore(self.path)
        self.addCleanup(store.close)

        device = store.get_device("d1")
        self.assertEqual("Old laptop", device.name)
        self.assertEqual("", device.token_hash)
        self.assertIn("0002_device_pairing", store.schema_versions())

    def test_tasks_survive_a_reopen(self):
        store = ControlStore(self.path)
        store.save_task(Task(id="t1", goal="Keep me"))
        store.close()

        reopened = ControlStore(self.path)
        self.addCleanup(reopened.close)

        self.assertEqual("Keep me", reopened.get_task("t1").goal)

    def test_a_device_can_be_found_by_its_token_hash(self):
        store = ControlStore(self.path)
        self.addCleanup(store.close)
        store.save_device(Device(id="d1", name="Phone", token_hash="abc123"))

        self.assertEqual("d1", store.get_device_by_token("abc123").id)
        self.assertIsNone(store.get_device_by_token("nothing"))
        self.assertIsNone(store.get_device_by_token(""))


if __name__ == "__main__":
    unittest.main()
