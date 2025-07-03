# Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Document Pages",
    "summary": "Document Pages Addons Pages",
    "version": "16.0.1.0.0",
    "category": "Management System",
    "author": "Akshat Gupta",
    "website": "https://github.com/OCA/management-system",
    "license": "AGPL-3",
    "depends": ["document_page"],
    "data": [
            'data/document_page_iatf_16949.xml',
            'data/document_page_iso_14001.xml',
            'data/document_page_iso_9001.xml',
            'data/document_page_iso_45001.xml',

            ],
    "installable": True,
    "auto_install": False,
    "images": ["images/wiki_pages_quality_manual.jpeg"],
}
