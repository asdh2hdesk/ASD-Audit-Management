# Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Management System - Audit Modified",
    "version": "16.0.1.0.1",
    'sequence': 1,

    "author": "Akshat Gupta",
    "category": "Management System",
    "depends": ["mgmtsystem_audit", 'hr','mgmtsystem','mgmtsystem_action','mgmtsystem_nonconformity', 'mgmtstem_modify'],
    "data": [
        'views/auditors_view.xml',
        'views/auditor_checklist_view.xml',
        'views/actions_view.xml',
        'views/nonconfirmities_view.xml',
        'views/revision_view.xml',

    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
