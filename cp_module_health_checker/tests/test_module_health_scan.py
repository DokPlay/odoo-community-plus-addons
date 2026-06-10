from odoo.tests.common import TransactionCase


class TestModuleHealthScan(TransactionCase):
    def test_run_scan_creates_lines_and_totals(self):
        admin = self.env.ref('base.user_admin')
        scan = self.env['cp.module.health.scan'].with_user(admin).create({
            'name': 'Automated Test Scan',
        })

        scan.action_run_scan()

        self.assertEqual(scan.state, 'done')
        self.assertGreater(scan.total_modules, 0)
        self.assertEqual(scan.total_modules, len(scan.line_ids))
        self.assertEqual(
            scan.problem_modules,
            len(scan.line_ids.filtered(lambda line: line.severity != 'ok')),
        )
        self.assertEqual(
            scan.warning_count,
            len(scan.line_ids.filtered(lambda line: line.severity == 'warning')),
        )
        self.assertEqual(
            scan.critical_count,
            len(scan.line_ids.filtered(lambda line: line.severity == 'critical')),
        )

