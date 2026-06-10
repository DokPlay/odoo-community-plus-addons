from odoo import _, api, fields, models
from odoo.exceptions import AccessError
from odoo.tools import ustr


class CpModuleHealthScan(models.Model):
    _name = 'cp.module.health.scan'
    _description = 'Module Health Scan'
    _order = 'scan_date desc, id desc'

    name = fields.Char(required=True, default=lambda self: self._default_name())
    scan_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, readonly=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('error', 'Error'),
        ],
        default='draft',
        required=True,
        readonly=True,
    )
    include_uninstalled = fields.Boolean(default=False)
    total_modules = fields.Integer(readonly=True)
    installed_modules = fields.Integer(readonly=True)
    problem_modules = fields.Integer(readonly=True)
    warning_count = fields.Integer(readonly=True)
    critical_count = fields.Integer(readonly=True)
    line_ids = fields.One2many('cp.module.health.line', 'scan_id', string='Modules')
    notes = fields.Text(readonly=True)

    @api.model
    def _default_name(self):
        return _('Scan %s') % fields.Datetime.to_string(fields.Datetime.now())

    def _check_module_health_manager(self):
        if not self.env.user.has_group('cp_module_health_checker.group_module_health_manager'):
            raise AccessError(_('Only Module Health Managers can run module health scans.'))

    def action_run_scan(self):
        for scan in self:
            scan._check_module_health_manager()
            try:
                scan._run_scan()
            except Exception as exc:  # noqa: BLE001 - convert scanner failures into scan state
                scan.write({
                    'state': 'error',
                    'notes': _('Scan failed: %s') % ustr(exc),
                })
        return True

    def action_rescan(self):
        return self.action_run_scan()

    def _run_scan(self):
        self.ensure_one()
        Module = self.env['ir.module.module'].sudo()
        Line = self.env['cp.module.health.line']

        domain = []
        if not self.include_uninstalled:
            domain.append(('state', '=', 'installed'))
        modules = Module.search(domain, order='name')

        self.line_ids.unlink()

        values = []
        counters = {
            'installed_modules': 0,
            'problem_modules': 0,
            'warning_count': 0,
            'critical_count': 0,
        }

        for module in modules:
            line_values = self._prepare_line_values(module)
            if line_values['module_state'] == 'installed':
                counters['installed_modules'] += 1
            if line_values['severity'] != 'ok':
                counters['problem_modules'] += 1
            if line_values['severity'] == 'warning':
                counters['warning_count'] += 1
            if line_values['severity'] == 'critical':
                counters['critical_count'] += 1
            values.append(line_values)

        if values:
            Line.create(values)

        self.write({
            'scan_date': fields.Datetime.now(),
            'user_id': self.env.user.id,
            'company_id': self.env.company.id,
            'state': 'done',
            'total_modules': len(modules),
            'installed_modules': counters['installed_modules'],
            'problem_modules': counters['problem_modules'],
            'warning_count': counters['warning_count'],
            'critical_count': counters['critical_count'],
            'notes': False,
        })

    def _prepare_line_values(self, module):
        self.ensure_one()
        technical_name = module.name or ''
        dependency_names = []
        missing_dependency_names = []

        for dependency in module.dependencies_id.sudo():
            dependency_names.append(dependency.name)
            if module.state == 'installed' and dependency.state != 'installed':
                missing_dependency_names.append(dependency.name)

        issues = []
        flags = {
            'missing_author': self._is_blank(module.author),
            'missing_license': self._is_blank(module.license),
            'missing_version': self._is_blank(module.latest_version) and self._is_blank(module.installed_version),
            'missing_website': self._is_blank(module.website),
            'missing_description': self._is_blank(module.summary) and self._is_blank(module.description),
            'has_missing_dependencies': bool(missing_dependency_names),
        }

        self._append_issue(issues, flags['missing_author'], 'warning', _('Missing author'))
        self._append_issue(issues, flags['missing_license'], 'warning', _('Missing license'))
        self._append_issue(issues, flags['missing_version'], 'warning', _('Missing version'))
        self._append_issue(issues, flags['missing_website'], 'info', _('Missing website'))
        self._append_issue(issues, flags['missing_description'], 'info', _('Missing description'))

        for dependency_name in missing_dependency_names:
            issues.append(('critical', _('Dependency is not installed: %s') % dependency_name))

        is_potential_custom = self._is_potential_custom_module(module)
        if is_potential_custom:
            issues.append(('info', _('Potential custom module')))

        severity = self._get_highest_severity(issues)

        return {
            'scan_id': self.id,
            'module_id': module.id,
            'technical_name': technical_name,
            'module_name': module.shortdesc or technical_name,
            'module_state': module.state or '',
            'author': module.author or '',
            'license': module.license or '',
            'version': module.latest_version or module.installed_version or module.published_version or '',
            'category': module.category_id.display_name or '',
            'website': module.website or module.url or '',
            'summary': module.summary or module.description or '',
            'is_potential_custom': is_potential_custom,
            'severity': severity,
            'issue_count': len(issues),
            'issues_text': '\n'.join(issue[1] for issue in issues),
            'dependency_names': '\n'.join(dependency_names),
            'missing_dependency_names': '\n'.join(missing_dependency_names),
            **flags,
        }

    @staticmethod
    def _is_blank(value):
        return not str(value or '').strip()

    @staticmethod
    def _append_issue(issues, condition, severity, message):
        if condition:
            issues.append((severity, message))

    @staticmethod
    def _get_highest_severity(issues):
        order = {
            'ok': 0,
            'info': 1,
            'warning': 2,
            'critical': 3,
        }
        highest = 'ok'
        for severity, _message in issues:
            if order[severity] > order[highest]:
                highest = severity
        return highest

    def _is_potential_custom_module(self, module):
        technical_name = module.name or ''
        author = (module.author or '').lower()
        if technical_name.startswith('l10n_'):
            return False
        if 'odoo' in author:
            return False
        return True

    def action_open_problem_modules(self):
        self.ensure_one()
        return self._line_action(
            _('Problem Modules'),
            [('scan_id', '=', self.id), ('severity', '!=', 'ok')],
        )

    def action_open_critical(self):
        self.ensure_one()
        return self._line_action(
            _('Critical Modules'),
            [('scan_id', '=', self.id), ('severity', '=', 'critical')],
        )

    def _line_action(self, name, domain):
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'cp.module.health.line',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_scan_id': self.id,
                'search_default_group_by_severity': 1,
            },
        }
