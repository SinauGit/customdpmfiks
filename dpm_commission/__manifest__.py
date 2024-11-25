{
    "name": "DPM Komisi 1",
    "author": "",
    "category": "",
    "depends": [
        "sale",
        "product",
                
                ],
    "data": [
        "security/commission_security.xml",
        "security/ir.model.access.csv",
        "data/menuitem_data.xml",
        "views/commission_views.xml",
        "views/commission_settlement_views.xml",
        "views/commission_mixin_views.xml",
        "views/product_template_views.xml",
        "views/res_partner_views.xml",
        "reports/commission_settlement_report.xml",
        "reports/report_settlement_templates.xml",
        "wizards/commission_make_settle_views.xml",
    ],
    # "demo": ["demo/commission_and_agent_demo.xml"],
    "installable": True,
}
