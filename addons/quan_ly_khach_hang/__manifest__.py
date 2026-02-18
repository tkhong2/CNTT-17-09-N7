{
	'name': 'quan_ly_khach_hang',
	'summary': 'Quản lý khách hàng liên thông nhân sự và công việc',
	'description': """
		Mô đun quản lý khách hàng:
		- Quản lý hồ sơ khách hàng
		- Liên kết tự động với dự án/công việc
		- Liên thông nhân sự phụ trách
	""",
	'author': 'My Company',
	'website': 'http://www.yourcompany.com',
	'category': 'Sales',
	'version': '15.0.1.0.0',
	'depends': ['base', 'mail', 'quan_ly_nhan_su', 'quan_ly_cong_viec'],
	'data': [
		'security/khach_hang_groups.xml',
		'security/khach_hang_rules.xml',
		'security/ir.model.access.csv',
		'data/sequence_data.xml',
		'data/dashboard_data.xml',
		'data/followup_cron_data.xml',
		'data/auto_assign_cron_data.xml',
		'data/manager_automation_cron_data.xml',
		'data/auto_heal_cron_data.xml',
		'data/transfer_template_data.xml',
		'data/demo_content.xml',
		'views/khach_hang_dashboard_views.xml',
		'views/khach_hang_views.xml',
		'views/khach_hang_merge_suggestion_views.xml',
		'views/khach_hang_assign_owner_wizard_views.xml',
		'views/khach_hang_transfer_template_views.xml',
		'views/khach_hang_transfer_owner_wizard_views.xml',
		'views/khach_hang_merge_wizard_views.xml',
		'views/khach_hang_tuong_tac_views.xml',
		'views/du_an_inherit_views.xml',
		'views/cong_viec_inherit_views.xml',
		'views/nhan_vien_inherit_views.xml',
	],
	'installable': True,
	'application': True,
	'auto_install': False,
	'license': 'LGPL-3',
}
