from odoo import fields, models

MODULE_STATES = [
    ('uninstallable', 'Uninstallable'),
    ('uninstalled', 'Not Installed'),
    ('installed', 'Installed'),
    ('to upgrade', 'To be upgraded'),
    ('to remove', 'To be removed'),
    ('to install', 'To be installed'),
]


class CpModuleHealthLine(models.Model):
    _name = 'cp.module.health.line'
    _description = 'Module Health Line'
    _order = 'severity desc, technical_name, id'
    _rec_name = 'technical_name'

    scan_id = fields.Many2one(
        'cp.module.health.scan',
        required=True,
        ondelete='cascade',
        index=True,
    )
    module_id = fields.Many2one('ir.module.module', readonly=True)
    technical_name = fields.Char(readonly=True, index=True)
    module_name = fields.Char(readonly=True)
    module_state = fields.Selection(MODULE_STATES, readonly=True, index=True)
    author = fields.Char(readonly=True, index=True)
    license = fields.Char(readonly=True, index=True)
    version = fields.Char(readonly=True)
    category = fields.Char(readonly=True)
    website = fields.Char(readonly=True)
    summary = fields.Text(readonly=True)
    is_potential_custom = fields.Boolean(readonly=True, index=True)
    severity = fields.Selection(
        [
            ('ok', 'OK'),
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('critical', 'Critical'),
        ],
        default='ok',
        required=True,
        readonly=True,
        index=True,
    )
    issue_count = fields.Integer(string='Issues', readonly=True)
    issues_text = fields.Text(readonly=True)
    dependency_names = fields.Text(readonly=True)
    missing_dependency_names = fields.Text(readonly=True)
    missing_author = fields.Boolean(readonly=True, index=True)
    missing_license = fields.Boolean(readonly=True, index=True)
    missing_version = fields.Boolean(readonly=True, index=True)
    missing_website = fields.Boolean(readonly=True, index=True)
    missing_description = fields.Boolean(readonly=True, index=True)
    has_missing_dependencies = fields.Boolean(readonly=True, index=True)
