{
    "name": "DPM Komisi 2",
    "author": "",
    "category": "",
    "depends": [
        "account",
        "dpm_commission",
        # "cashback_commission",
    ],
    "data": [
        "security/account_commission_security.xml",
        "security/ir.model.access.csv",
        # "data/menuitem_data.xml",
        "views/account_move_views.xml",
        "views/commission_settlement_views.xml",
        "views/commission_views.xml",
        "views/report_settlement_templates.xml",
        "report/commission_analysis_view.xml",
        "wizards/wizard_invoice.xml",
        # "views/account_payment_register_views.xml",
        "wizards/account_move_agent_wizard_view.xml",
    ],
    "installable": True,
}
