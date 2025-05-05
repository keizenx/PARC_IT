# -*- coding: utf-8 -*-
{
    'name': "Gestion de Parc Informatique",
    'version': '18.0.1.0.0',
    'depends': [
        'base',
        'mail',
        'portal',
        'website',
        'contacts',
        'product',
        'stock',
        'account',
        'helpdesk',
        'rating',
    ],
    'author': "Your Company",
    'category': 'Services/IT',
    'description': """
        Module de gestion de parc informatique avec portail client
    """,
    'data': [
        'security/it_security.xml',
        'security/ir.model.access.csv',
        # Données de base
        'data/it_park_sequences.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        # Menus principaux
        'views/it_park_menus.xml',
        # Vues des modèles
        'views/it_equipment_views.xml',
        'views/it_software_views.xml',
        'views/it_license_views.xml',
        'views/it_contract_views.xml',
        'views/it_incident_views.xml',
        'views/it_intervention_views.xml',
        'views/it_ticket_views.xml',
        'views/it_dashboard_views.xml',
        'views/it_sla_views.xml',
        # Vues étendues
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/hr_employee_views.xml',
        'views/res_users_views.xml',
        'views/helpdesk_views.xml',
        # Vues portail
        'views/portal_templates.xml',
        'views/menus.xml',
        'views/it_park_portal_templates.xml',
        'views/it_support_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'it__park/static/src/scss/portal.scss',
            'it__park/static/src/js/portal.js',
            'it__park/static/src/js/portal_enhancements.js',
            'it__park/static/src/js/ticket_notification.js',
            'it__park/static/src/js/website_it_support.js',
        ],
    },
    'demo': [
        'demo/demo.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

