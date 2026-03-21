# -*- coding: utf-8 -*-
from odoo import models, fields, api


class KhachHang(models.Model):
    _name = 'khach_hang'
    _description = 'Khách hàng'
    _rec_name = 'ten_khach_hang'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    ma_khach_hang = fields.Char(
        string='Mã khách hàng', readonly=True, default='New', copy=False
    )
    ten_khach_hang = fields.Char(string='Tên khách hàng', required=True)
    nguoi_lien_he = fields.Char(string='Người liên hệ')
    email = fields.Char(string='Email')
    dien_thoai = fields.Char(string='Điện thoại')
    dia_chi = fields.Text(string='Địa chỉ')
    nguon = fields.Selection([
            ('facebook', 'Facebook'),
            ('zalo', 'Zalo'),
            ('website', 'Website'),
            ('gioi_thieu', 'Giới thiệu'),
            ('khac', 'Khác'),
        ], string='Nguồn', tracking=True)
    mo_ta = fields.Text(string='Mô tả')
    tong_ngan_sach = fields.Float(string='Tổng ngân sách (VNĐ)', digits=(16, 0))
    active = fields.Boolean(default=True, string='Hoạt động')
    rank = fields.Selection([
        ('dong', 'Đồng'),
        ('bac', 'Bạc'),
        ('vang', 'Vàng'),
    ], string='Phân hạng khách hàng', default='dong', tracking=True)
    nhan_vien_phu_trach_id = fields.Many2one(
        'nhan_vien', string='Nhân viên phụ trách', tracking=True
    )
    trang_thai_hop_tac = fields.Selection([
        ('tiem_nang', 'Tiềm năng'),
        ('dang_hop_tac', 'Đang hợp tác'),
        ('tam_ngung', 'Tạm ngưng'),
        ('ngung_hop_tac', 'Ngưng hợp tác'),
    ], string='Trạng thái hợp tác', default='tiem_nang', tracking=True)
    # Giai đoạn 2 - Gợi ý 2: Phân cấp khách hàng cho phép liên hệ đa cấp
    parent_khach_hang_id = fields.Many2one(
        'khach_hang', string='Khách hàng chính', ondelete='cascade', index=True
    )
    subsidiary_khach_hang_ids = fields.One2many(
        'khach_hang', 'parent_khach_hang_id', string='Liên hệ chi nhánh/phụ'
    )
    so_du_an = fields.Integer(string='Số dự án', compute='_compute_so_du_an')
    so_du_an_dang_thuc_hien = fields.Integer(
        string='Dự án đang thực hiện', compute='_compute_so_du_an'
    )
    so_cong_viec = fields.Integer(
        string='Số công việc', compute='_compute_so_cong_viec'
    )
    so_cong_viec_dang_thuc_hien = fields.Integer(
        string='Công việc đang thực hiện', compute='_compute_so_cong_viec'
    )
    so_lan_tuong_tac = fields.Integer(
        string='Số lần tương tác', compute='_compute_so_tuong_tac'
    )
    so_tuong_tac_qua_han = fields.Integer(
        string='Tương tác quá hạn', compute='_compute_so_tuong_tac'
    )
    so_ban_ghi_trung = fields.Integer(
        string='Bản ghi trùng', compute='_compute_so_ban_ghi_trung'
    )
    lan_tuong_tac_cuoi = fields.Datetime(
        string='Lần tương tác cuối', compute='_compute_lan_tuong_tac_cuoi', store=True
    )
    lan_tuong_tac_cuoi_index = fields.Date(
        string='Index tương tác cuối', compute='_compute_lan_tuong_tac_cuoi', store=True
    )
    du_an_ids = fields.One2many('du_an', 'khach_hang_id', string='Dự án')
    cong_viec_ids = fields.One2many('cong_viec', 'khach_hang_id', string='Công việc')
    tuong_tac_ids = fields.One2many('khach_hang_tuong_tac', 'khach_hang_id', string='Lịch sử tương tác')
    def _compute_so_du_an(self):
        DuAn = self.env['du_an']
        for rec in self:
            all_da = DuAn.search([('khach_hang_id', '=', rec.id)])
            rec.so_du_an = len(all_da)
            rec.so_du_an_dang_thuc_hien = len(all_da.filtered(
                lambda d: d.trang_thai not in ('hoan_thanh', 'huy')
            ))

    def _compute_so_cong_viec(self):
        CongViec = self.env['cong_viec']
        for rec in self:
            all_cv = CongViec.search([('khach_hang_id', '=', rec.id)])
            rec.so_cong_viec = len(all_cv)
            rec.so_cong_viec_dang_thuc_hien = len(all_cv.filtered(
                lambda c: c.trang_thai not in ('hoan_thanh', 'huy_bo')
            ))

    def _compute_so_tuong_tac(self):
        TuongTac = self.env['khach_hang_tuong_tac']
        today = fields.Date.today()
        for rec in self:
            all_tt = TuongTac.search([('khach_hang_id', '=', rec.id)])
            rec.so_lan_tuong_tac = len(all_tt)
            rec.so_tuong_tac_qua_han = len(all_tt.filtered(
                lambda t: t.trang_thai == 'planned' and t.hen_lien_he_tiep and t.hen_lien_he_tiep < today
            ))

    @api.depends('tuong_tac_ids.ngay_lien_he')
    def _compute_lan_tuong_tac_cuoi(self):
        for rec in self:
            tt = rec.tuong_tac_ids.sorted('ngay_lien_he', reverse=True)
            if tt:
                rec.lan_tuong_tac_cuoi = tt[0].ngay_lien_he
                rec.lan_tuong_tac_cuoi_index = tt[0].ngay_lien_he.date() if tt[0].ngay_lien_he else False
            else:
                rec.lan_tuong_tac_cuoi = False
                rec.lan_tuong_tac_cuoi_index = False

    def _compute_so_ban_ghi_trung(self):
        for rec in self:
            domain = [
                ('id', '!=', rec.id),
                '|',
                ('dien_thoai', '=', rec.dien_thoai),
                ('email', '=', rec.email),
            ]
            if rec.dien_thoai or rec.email:
                rec.so_ban_ghi_trung = self.search_count(domain)
            else:
                rec.so_ban_ghi_trung = 0

    @api.model
    def create(self, vals):
        if vals.get('ma_khach_hang', 'New') == 'New':
            vals['ma_khach_hang'] = self.env['ir.sequence'].next_by_code('khach_hang.sequence') or 'KH0001'
        return super().create(vals)

    # ==================== ACTIONS ====================
    def action_xem_du_an(self):
        return {
            'name': f'Dự án - {self.ten_khach_hang}',
            'type': 'ir.actions.act_window',
            'res_model': 'du_an',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id},
        }

    def action_xem_cong_viec(self):
        return {
            'name': f'Công việc - {self.ten_khach_hang}',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id},
        }

    def action_xem_tuong_tac(self):
        return {
            'name': f'Tương tác - {self.ten_khach_hang}',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang_tuong_tac',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id},
        }

    def action_xem_tuong_tac_qua_han(self):
        today = fields.Date.today()
        return {
            'name': f'Tương tác quá hạn - {self.ten_khach_hang}',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang_tuong_tac',
            'view_mode': 'tree,form',
            'domain': [
                ('khach_hang_id', '=', self.id),
                ('trang_thai', '=', 'planned'),
                ('hen_lien_he_tiep', '<', today),
            ],
        }

    def action_xem_ban_ghi_trung(self):
        domain = [
            ('id', '!=', self.id),
            '|',
            ('dien_thoai', '=', self.dien_thoai),
            ('email', '=', self.email),
        ]
        return {
            'name': f'Bản ghi trùng - {self.ten_khach_hang}',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': domain,
        }

    def action_tao_du_an_nhanh(self):
        return {
            'name': 'Tạo dự án nhanh',
            'type': 'ir.actions.act_window',
            'res_model': 'du_an',
            'view_mode': 'form',
            'context': {
                'default_khach_hang_id': self.id,
                'default_ten_du_an': f'Dự án - {self.ten_khach_hang}',
            },
            'target': 'new',
        }

    def action_merge_duplicate_khach_hang(self):
        domain = [
            ('id', '!=', self.id),
            '|',
            ('dien_thoai', '=', self.dien_thoai),
            ('email', '=', self.email),
        ]
        duplicates = self.search(domain)
        return {
            'name': 'Gộp khách hàng trùng',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang_merge_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_primary_khach_hang_id': self.id,
                'active_ids': [self.id] + duplicates.ids,
            },
        }
