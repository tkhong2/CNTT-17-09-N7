{
	'name': 'quan_ly_khach_hang',
	'summary': 'Quản lý khách hàng liên thông nhân sự và công việc',
	'description': """
		Mô đun quản lý khách hàng:
		- Quản lý hồ sơ khách hàng
		- Liên kết tự động với dự án/công việc
		- Liên thông nhân sự phụ trách
		- Dashboard KPI theo dõi hiệu quả chăm sóc
		- Tương tác: gọi điện, lịch hẹn, báo giá
		- Phát hiện và gộp khách hàng trùng
	""",
	'author': 'My Company',
	'website': 'http://www.yourcompany.com',
	'category': 'Sales',
	'version': '15.0.2.0.0',
	'depends': ['base', 'mail', 'quan_ly_nhan_su', 'quan_ly_cong_viec'],
	'data': [
		'security/khach_hang_nhom_quyen.xml',
		'security/khach_hang_quy_tac_truy_cap.xml',
		'security/ir.model.access.csv',
		'data/sequence.xml',
		'views/khach_hang_views.xml',
		'views/khach_hang_tuong_tac_views.xml',
		'views/cong_viec_mo_rong_views.xml',
		'views/du_an_mo_rong_views.xml',
		'views/nhan_vien_mo_rong_views.xml',
		'views/khach_hang_bang_dieu_views.xml',
		'views/khach_hang_de_xuat_gop_views.xml',
		'views/khach_hang_phan_cong_chu_tro_ly_views.xml',
		'views/khach_hang_gop_tro_ly_views.xml',
		'views/khach_hang_chuyen_chu_tro_ly_views.xml',
		'views/khach_hang_chuyen_mau_views.xml',
        'views/menu.xml',
	],
	'installable': True,
	'application': True,
	'auto_install': False,
	'license': 'LGPL-3',
}
