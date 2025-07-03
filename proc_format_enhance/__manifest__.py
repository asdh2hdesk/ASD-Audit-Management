# -*- coding: utf-8 -*-
{
    'name': 'Management System Procedure Format Enhanced',
    'version': '16.0.1.0',
    'category': 'Quality',
    'summary': 'Enhances the Procedure Format Number model with approval and revision features',
    'author': 'Akshat Gupta',
    'price': 0,
    'license': 'LGPL-3',
    'sequence': 1,
    'currency': "INR",
    'website': 'https://github.com/Akshat-10',
    
    'depends': ['mgmtstem_modify'],
    
    'data': [
        'security/procedure_format_security.xml',
        'security/ir.model.access.csv',
        'views/procedure_format_views.xml',
        'views/revision_views.xml',
        'views/approval_config_views.xml',
    ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}