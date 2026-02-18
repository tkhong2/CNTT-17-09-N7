# -*- coding: utf-8 -*-
{
    'name': "quan_ly_nhan_su",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Mô đun quản lý nhân sự cho doanh nghiệp:
        - Quản lý thông tin nhân viên
        - Quản lý cấu trúc phòng ban (phân cấp)
        - Quản lý chức vụ
        - Quản lý hợp đồng lao động
        - Quản lý đánh giá hiệu suất
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/automation_params.xml',
        'data/automation_cron.xml',
        'data/demo_content.xml',
        'views/ops/nhan_vien.xml',
        'views/admin/phong_ban.xml',
        'views/admin/chuc_vu.xml',
        'views/ops/hop_dong.xml',
        'views/admin/danh_gia.xml',
        'views/admin/dao_tao.xml',
        'views/ops/cham_cong.xml',
        'views/ops/menu.xml',
    ],
    'license': 'LGPL-3',
}
