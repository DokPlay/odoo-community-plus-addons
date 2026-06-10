{
    'name': 'CP Module Health Checker',
    'summary': 'Audit installed Odoo modules for metadata and dependency issues',
    'description': """
Audit installed Odoo modules for missing metadata, dependency issues, and potential custom module indicators.
The checker is read-only and keeps scan history for review.
""",
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'author': 'DokPlay',
    'website': 'https://github.com/DokPlay/odoo-community-plus-addons',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/module_health_security.xml',
        'security/ir.model.access.csv',
        'views/module_health_scan_views.xml',
        'views/module_health_line_views.xml',
        'views/module_health_menu.xml',
    ],
    'installable': True,
    'application': True,
}
