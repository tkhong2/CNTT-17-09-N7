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
        - Quản lý chấm công
        - Quản lý đơn xin nghỉ phép
        - Quản lý tính lương hàng tháng
        - Quản lý đánh giá hiệu suất
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'web', 'hr'],

    'assets': {
        'web.assets_backend': [
            'quan_ly_nhan_su/static/src/scss/modern_backend.scss',
        ],
    },

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/actions.xml',
        'views/ops/menu.xml',
        'data/automation_params.xml',
        'data/automation_cron.xml',
        'data/demo_content.xml',
        'data/demo_seed_all_biz.xml',
        'data/demo_seed_massive.xml',
        'data/demo_seed_wave2.xml',
        'views/ops/nhan_vien.xml',
        'views/inherit/hr_employee_mix_views.xml',
        'views/admin/phong_ban.xml',
        'views/admin/chuc_vu.xml',
        'views/ops/hop_dong.xml',
        'views/admin/danh_gia.xml',
        'views/admin/dao_tao.xml',
        'views/ops/cham_cong.xml',
        'views/ops/nhan_su_dashboard.xml',
        'views/ops/nghi_phep.xml',
        'views/ops/tinh_luong.xml',
        'views/ops/tuyen_dung.xml',
    ],
    'license': 'LGPL-3',
}
