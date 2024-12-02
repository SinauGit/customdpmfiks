# -*- coding: utf-8 -*-
{
    'name': "DPM Cashback Commission",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': '',
    'version': '17.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'dpm_commission',
        'dpm_commission_2',
        'dpm_commission_3',
        'account',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_register_payment_view.xml',
        'views/account_move_line_view.xml',
    ],

    'installable': True,
}

