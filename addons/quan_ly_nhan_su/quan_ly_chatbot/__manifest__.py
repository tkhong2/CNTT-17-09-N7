# -*- coding: utf-8 -*-
{
    'name': 'Chatbot AI - Trợ lý ERP',
    'summary': 'Chatbot AI hỗ trợ 3 module: Nhân sự, Công việc, Khách hàng',
    'version': '1.0',
    'category': 'Tools',
    'author': 'My Company',
    'depends': [
        'base', 'web', 'mail',
        'quan_ly_nhan_su',
        'quan_ly_cong_viec',
        'quan_ly_khach_hang',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/chatbot_assistant_data.xml',
        'views/chatbot_assistant_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'quan_ly_chatbot/static/src/js/chatbot.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
