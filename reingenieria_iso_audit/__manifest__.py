# -*- coding: utf-8 -*-
{
    'name': 'Reingeniería - Gestión de Auditorías ISO 9001 & CDO',
    'version': '19.0.1.0.0',
    'category': 'Quality',
    'summary': 'Auditorías internas por CDO, ingestión masiva de checklists Excel F-CAL-15_R01, NCR y CAPA.',
    'author': 'Reingeniería de Procedimientos',
    'depends': [
        'base',
        'mail',
        'hr',
    ],
    'data': [
        # Seguridad y Permisos
        'security/security_groups.xml',
        'security/ir.model.access.csv',

        # Secuencias y Datos Iniciales
        'data/ir_sequence_data.xml',
        'data/iso_clause_data.xml',

        # Vistas de Asistentes / Wizards
        'wizards/audit_excel_import_wizard_views.xml',

        # Vistas de Modelos
        'views/audit_cdo_views.xml',
        'views/audit_template_views.xml',
        'views/iso_audit_views.xml',
        'views/quality_ncr_views.xml',
        'views/quality_capa_views.xml',

        # Reportes QWeb
        'reports/audit_report_templates.xml',
        'reports/audit_reports.xml',

        # Menús Principales (siempre al final de las vistas)
        'views/audit_menus.xml',
    ],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
