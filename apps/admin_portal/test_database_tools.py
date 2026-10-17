import hashlib
import json
import logging
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.errors import AccountPermissionDenied
from .services.backup_service import create_database_backup, get_backup_dir, verify_database_backup
from .services.maintenance import DatabaseMaintenanceError, DatabaseMaintenanceMiddleware, database_access, recovery_marker_path
from .services.restore_service import RestoreFailed, restore_confirmation, restore_database_from_backup, validate_backup_filename


DUMP = (b"-- MySQL dump 10.13\n-- Trusted regression fixture\n"
        b"CREATE TABLE `fixture` (`fixture_id` int NOT NULL);\n"
        b"INSERT INTO `fixture` VALUES (1);\n-- Dump completed on 2026-10-16 00:00:00\n")


def publish_fixture(name="source.sql", data=DUMP):
    path = get_backup_dir() / name
    path.write_bytes(data)
    path.with_suffix(".sql.json").write_text(json.dumps({
        "version": 1, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
    }), encoding="utf-8")
    return path


class DatabaseToolsServiceTests(SimpleTestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="crm database tools ")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        config = {"ENGINE": "django.db.backends.mysql", "NAME": "crm_restore_unit_test",
                  "USER": "unit_user", "PASSWORD": "sensitive-unit-password", "HOST": "127.0.0.1", "PORT": "3306"}
        self.settings_override = override_settings(BASE_DIR=self.directory, DATABASES={"default": config})
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        audit_handlers = patch.object(logging.getLogger("apps.admin_portal"), "handlers", [logging.NullHandler()])
        audit_handlers.start()
        self.addCleanup(audit_handlers.stop)
        for executable in ("mysql.exe", "mysqldump.exe"):
            (self.directory / executable).touch()
        environment = patch.dict(os.environ, {"MYSQL_BIN": str(self.directory)})
        environment.start()
        self.addCleanup(environment.stop)
        self.actor = SimpleNamespace(pk=17, is_authenticated=True)
        permission = patch("apps.admin_portal.services.restore_service.require_active_admin", return_value=self.actor)
        self.permission = permission.start()
        self.addCleanup(permission.stop)
        self.source = publish_fixture()

    def restore(self, **kwargs):
        options = {"actor": self.actor, "target_database": "crm_restore_unit_test", "maintenance_ack": True}
        options.update(kwargs)
        return restore_database_from_backup(self.source.name, restore_confirmation(self.source.name, "crm_restore_unit_test"), **options)

    def successful_process(self, argv, **kwargs):
        self.assertNotIn("sensitive-unit-password", " ".join(argv))
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["env"]["MYSQL_PWD"], "sensitive-unit-password")
        if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
            kwargs["stdout"].write(DUMP)
        return SimpleNamespace(returncode=0, stderr=b"")

    @patch("apps.admin_portal.services.backup_service.subprocess.run")
    def test_backup_is_published_only_with_verified_manifest(self, process):
        process.side_effect = self.successful_process
        backup = create_database_backup(actor_id=self.actor.pk)
        self.assertEqual(verify_database_backup(backup)["sha256"], hashlib.sha256(DUMP).hexdigest())
        self.assertFalse(list(get_backup_dir().glob("*.partial")))
        self.assertNotIn("MYSQL_PWD", process.call_args.kwargs["env"])

    @patch("apps.admin_portal.services.backup_service.subprocess.run")
    def test_backup_failure_timeout_and_incomplete_dump_are_not_published(self, process):
        outcomes = [SimpleNamespace(returncode=2, stderr=b"sensitive-unit-password raw SQL"),
                    subprocess.TimeoutExpired("sensitive-unit-password", 300),
                    SimpleNamespace(returncode=0, stderr=b"")]
        for outcome in outcomes:
            with self.subTest(outcome=type(outcome).__name__):
                process.side_effect = outcome if isinstance(outcome, Exception) else None
                process.return_value = outcome
                with self.assertLogs("apps.admin_portal.services.backup_service", level="ERROR") as logs:
                    with self.assertRaises(RuntimeError) as error:
                        create_database_backup()
                self.assertNotIn("sensitive-unit-password", str(error.exception) + " ".join(logs.output))
                self.assertEqual(list(get_backup_dir().glob("*.sql")), [self.source])
                self.assertFalse(list(get_backup_dir().glob("*.partial")))

    @patch("apps.admin_portal.services.backup_service.subprocess.run")
    def test_restore_snapshots_and_verifies_before_import_then_retains_backup(self, process):
        order = []

        def execute(argv, **kwargs):
            order.append("dump" if Path(argv[0]).name == "mysqldump.exe" else "import")
            if order[-1] == "import":
                self.assertTrue(recovery_marker_path().is_file())
                recovery = json.loads(recovery_marker_path().read_text())["recovery_backup"]
                verify_database_backup(get_backup_dir() / recovery)
            return self.successful_process(argv, **kwargs)

        process.side_effect = execute
        with self.assertLogs("apps.admin_portal.services.restore_service", level="INFO") as logs:
            recovery = self.restore()
        self.assertEqual(order, ["dump", "import"])
        self.assertTrue(recovery.is_file())
        self.assertFalse(recovery_marker_path().exists())
        self.assertIn("success", " ".join(logs.output))
        self.assertEqual(self.permission.call_count, 2)

    @patch("apps.admin_portal.services.restore_service.create_database_backup")
    @patch("apps.admin_portal.services.restore_service.subprocess.run")
    def test_pre_restore_backup_failure_or_failed_verification_stops_import(self, process, snapshot):
        for failure in (RuntimeError("private details"), "corrupt"):
            with self.subTest(failure=failure):
                snapshot.side_effect = failure if isinstance(failure, Exception) else None
                snapshot.return_value = get_backup_dir() / "corrupt.sql"
                if failure == "corrupt":
                    snapshot.return_value.write_bytes(b"incomplete")
                with self.assertRaisesRegex(RuntimeError, "Restore was not started"):
                    self.restore()
                process.assert_not_called()
                self.assertFalse(recovery_marker_path().exists())

    @patch("apps.admin_portal.services.restore_service.subprocess.run")
    def test_import_exit_failure_and_timeout_retain_snapshot_and_block_access(self, process):
        for timeout in (False, True):
            with self.subTest(timeout=timeout):
                recovery_marker_path().unlink(missing_ok=True)

                def execute(argv, **kwargs):
                    if Path(argv[0]).name == "mysqldump.exe":
                        return self.successful_process(argv, **kwargs)
                    if timeout:
                        raise subprocess.TimeoutExpired("sensitive-unit-password", 300, stderr=b"secret stderr")
                    return SimpleNamespace(returncode=1, stderr=b"sensitive-unit-password raw SQL")

                process.side_effect = execute
                with self.assertLogs("apps.admin_portal.services.restore_service", level="ERROR") as logs:
                    with self.assertRaises(RestoreFailed) as error:
                        self.restore()
                message = str(error.exception)
                self.assertIn("not rolled back", message)
                self.assertNotIn("sensitive-unit-password", message + " ".join(logs.output))
                state = json.loads(recovery_marker_path().read_text())
                verify_database_backup(get_backup_dir() / state["recovery_backup"])
                with self.assertRaises(DatabaseMaintenanceError):
                    with database_access():
                        self.fail("Recovery marker must block new requests")

    @patch("apps.admin_portal.services.restore_service.subprocess.run")
    def test_invalid_source_confirmation_target_ack_and_permission_do_not_run_tools(self, process):
        for filename in ("../source.sql", "/source.sql", "source.sql:other", "absent.sql"):
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                validate_backup_filename(filename)
        for options in ({"target_database": "other_database"}, {"maintenance_ack": False}):
            with self.assertRaises(ValueError):
                self.restore(**options)
        with self.assertRaises(ValueError):
            restore_database_from_backup(self.source.name, "RESTORE", actor=self.actor,
                                         target_database="crm_restore_unit_test", maintenance_ack=True)
        self.source.write_bytes(DUMP + b"tampered")
        with self.assertRaises(ValueError):
            self.restore()
        self.permission.side_effect = AccountPermissionDenied("denied")
        with self.assertRaises(AccountPermissionDenied):
            self.restore()
        process.assert_not_called()

    def test_requests_use_shared_lock_and_restore_requires_exclusivity(self):
        def attempt(exclusive):
            try:
                with database_access(exclusive=exclusive):
                    return "allowed"
            except DatabaseMaintenanceError:
                return "blocked"

        with ThreadPoolExecutor(max_workers=1) as worker:
            with database_access():
                self.assertEqual(worker.submit(attempt, False).result(), "allowed")
                self.assertEqual(worker.submit(attempt, True).result(), "blocked")
            with database_access(exclusive=True):
                self.assertEqual(worker.submit(attempt, False).result(), "blocked")
                self.assertEqual(worker.submit(attempt, True).result(), "blocked")
        middleware = DatabaseMaintenanceMiddleware(lambda request: HttpResponse("open"))
        recovery_marker_path().write_text("recovery required")
        self.assertEqual(middleware(RequestFactory().get("/")).status_code, 503)
        recovery_marker_path().unlink()

        def failing_view(request):
            raise OSError("view error unrelated to maintenance")

        with self.assertRaisesRegex(OSError, "unrelated"):
            DatabaseMaintenanceMiddleware(failing_view)(RequestFactory().get("/"))

    def test_missing_and_malformed_manifests_are_rejected(self):
        manifest = self.source.with_suffix(".sql.json")
        for contents in ("[]", "1", "null", "{invalid", '{"version": 1}'):
            with self.subTest(contents=contents):
                manifest.write_text(contents)
                with self.assertRaises(ValueError):
                    verify_database_backup(self.source)
        manifest.unlink()
        with self.assertRaises(ValueError):
            verify_database_backup(self.source)

    @patch("apps.admin_portal.services.restore_service.subprocess.run")
    def test_unsafe_dump_missing_tool_and_non_mysql_backend_stop_before_import(self, process):
        self.source = publish_fixture(data=DUMP.replace(b"CREATE TABLE", b"USE shared_database;\nCREATE TABLE"))
        with self.assertRaises(ValueError):
            self.restore()
        self.source = publish_fixture()
        (self.directory / "mysql.exe").unlink()
        with self.assertRaisesRegex(RuntimeError, "mysql executable"):
            self.restore()
        with override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3"}}):
            with self.assertRaisesRegex(RuntimeError, "MySQL"):
                self.restore()
        process.assert_not_called()


class DatabaseRestoreHttpTests(TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="crm restore http ")
        self.addCleanup(temporary.cleanup)
        override = override_settings(BASE_DIR=Path(temporary.name))
        override.enable()
        self.addCleanup(override.disable)
        account = get_user_model()
        self.admin = account.objects.create_superuser("restore-admin@example.test", "RestorePass!2026")
        self.manager = account.objects.create_user("restore-manager@example.test", "RestorePass!2026", role=AccountRole.MANAGER)
        self.customer = account.objects.create_user("restore-customer@example.test", "RestorePass!2026")
        self.data = {"filename": "source.sql", "target_database": settings.DATABASES["default"]["NAME"],
                     "maintenance_ack": "on"}
        self.data["restore_confirm"] = restore_confirmation(self.data["filename"], self.data["target_database"])

    @patch("apps.admin_portal.views.restore_database_from_backup", return_value=Path("recovery.sql"))
    def test_restore_requires_admin_post_csrf_and_exact_confirmation(self, restore):
        url = reverse("database_restore")
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(url, self.data).status_code, 403)
        self.assertEqual(self.client.post(url, self.data).status_code, 302)
        for actor in (self.manager, self.customer):
            self.client.force_login(actor)
            self.assertEqual(self.client.post(url, self.data).status_code, 403)
        client.force_login(self.admin)
        self.assertEqual(client.get(url).status_code, 405)
        self.assertEqual(client.post(url, self.data).status_code, 403)
        client.get(reverse("database_tools"))
        token = client.cookies["csrftoken"].value
        for missing in ("target_database", "maintenance_ack", "restore_confirm"):
            data = dict(self.data, csrfmiddlewaretoken=token)
            del data[missing]
            self.assertEqual(client.post(url, data).status_code, 302)
        restore.assert_not_called()
        response = client.post(url, dict(self.data, csrfmiddlewaretoken=token))
        self.assertContains(response, "Recovery backup retained")
        restore.assert_called_once()
        client.force_login(self.admin)
        self.admin.status = AccountStatus.LOCKED
        self.admin.save(update_fields=["status"])
        self.assertEqual(client.post(url, dict(self.data, csrfmiddlewaretoken=token)).status_code, 302)
        self.assertEqual(restore.call_count, 1)

    @patch("apps.admin_portal.views.restore_database_from_backup")
    def test_restore_failure_response_has_recovery_instructions_and_no_success(self, restore):
        from django.contrib.sessions.models import Session

        self.client.force_login(self.admin)
        session_key = self.client.session.session_key

        def failed_import_replacing_session(*args, **kwargs):
            Session.objects.filter(session_key=session_key).delete()
            raise RestoreFailed("Recovery backup retained: recovery.sql. Import may have applied partially; not rolled back.")

        restore.side_effect = failed_import_replacing_session
        response = self.client.post(reverse("database_restore"), self.data)
        self.assertContains(response, "recovery.sql", status_code=503)
        self.assertNotContains(response, "successfully restored", status_code=503)

    @patch("apps.admin_portal.views.restore_database_from_backup")
    def test_success_when_import_replaced_the_current_session_returns_result_without_session_save(self, restore):
        from django.contrib.sessions.models import Session

        self.client.force_login(self.admin)
        session_key = self.client.session.session_key

        def import_replacing_session(*args, **kwargs):
            Session.objects.filter(session_key=session_key).delete()
            return Path("recovery.sql")

        restore.side_effect = import_replacing_session
        response = self.client.post(reverse("database_restore"), self.data)
        self.assertContains(response, "Database restored")
        self.assertContains(response, "recovery.sql")
        self.assertContains(response, reverse("admin_login"))
        self.assertEqual(response.cookies[settings.SESSION_COOKIE_NAME]["max-age"], 0)

    def test_confirmation_page_identifies_file_database_and_maintenance(self):
        publish_fixture()
        self.client.force_login(self.admin)
        response = self.client.get(reverse("database_tools"))
        self.assertContains(response, self.data["restore_confirm"])
        self.assertContains(response, 'name="target_database"')
        self.assertContains(response, 'name="maintenance_ack"')
