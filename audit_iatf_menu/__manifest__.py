# Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "IATF and Audit Model linking menu",
    "version": "16.0.1.0.1",
    "author": "Akshat Gupta",
    "category": "Management System",
    "depends": ["mgmtstem_modify", "mgmtsystem", 'iatf'],
    "data": [
        'views/audit_menu_merging.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
