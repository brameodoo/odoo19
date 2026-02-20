# -*- coding: utf-8 -*-
{
    'name': 'Custodia Logística',
    'version': '19.0.1.0',
    'summary': 'Gestión de servicios de custodia con portal, asignaciones y seguimiento',
    'category': 'Operations',
    'author': 'Xentinell',
    'license': 'OEEL-1',
    'depends': [
        'base',
        'mail',
        'bus',
        'website',
        'portal',
        'hr',
        'fleet',
        'purchase',
        'account',
        'planning',
    ],
    'data': [
        # Datos
        'data/sequence.xml',

        # Seguridad
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        # Catálogos
        'views/custodia_carrier_views.xml',
        'views/custodia_ruta_views.xml',

        # Servicio principal
        'views/custodia_service_views.xml',
        'views/custodia_service_list_view.xml',

        # Asignaciones
        'views/custodia_asignacion_views.xml',

        # Menús
        'views/custodia_menus.xml',

        # Portal
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Aquí puedes agregar CSS/JS para personalizar el portal
            #'custodia_logistica/static/src/js/portal_chatter_live.js',
        ],
    },
    'application': True,
    'installable': True,
}





