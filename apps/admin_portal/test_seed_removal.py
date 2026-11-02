from django.template.loader import get_template
from django.test import SimpleTestCase
from django.urls import NoReverseMatch, Resolver404, resolve, reverse


class AdminSeedRemovalTests(SimpleTestCase):
    def test_seed_endpoint_and_name_are_removed(self):
        with self.assertRaises(NoReverseMatch):
            reverse('seed_data')
        with self.assertRaises(Resolver404):
            resolve('/admin/database/seed/')

    def test_database_tools_renders_backup_restore_download_without_seed(self):
        html = get_template('admin/portal/database.html').render({
            'database_name': 'crm_db',
            'backups': [{'filename': 'crm_db_20261101.sql', 'verified': True}],
        })
        for text in ['Development Seed Data', 'Run Seed Data', 'seed-confirm', '/admin/database/seed/']:
            self.assertNotIn(text, html)
        for name in ['database_backup', 'database_restore']:
            self.assertIn(reverse(name), html)
        self.assertIn(reverse('database_download_backup', args=['crm_db_20261101.sql']), html)
        self.assertIn('maintenance_ack', html)
        self.assertIn('restore_confirm', html)

    def test_database_tools_routes_are_preserved(self):
        for name in ['database_tools', 'database_backup', 'database_restore']:
            self.assertEqual(resolve(reverse(name)).url_name, name)
        self.assertEqual(resolve(reverse('database_download_backup', args=['crm_db_20261101.sql'])).url_name,
                         'database_download_backup')
