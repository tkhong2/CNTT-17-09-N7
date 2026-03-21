# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import calendar

class NghiPhep(models.Model):
    _name = "nghi_phep"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Quản lý đơn xin nghỉ phép"
    _rec_name = "ma_nghi_phep"
    _order = "ngay_bat_dau desc, id desc"

    ma_nghi_phep = fields.Char(string="Mã đơn", required=True, index=True, default=lambda self: _('New'))
    def _default_nhan_vien_id(self):
        employee = self.env.user.nhan_vien_id
        if employee:
            return employee
        return self.env['nhan_vien'].search([('trang_thai', '=', 'active')], limit=1)

    nhan_vien_id = fields.Many2one(
        'nhan_vien',
        string="Nhân viên",
        required=True,
        tracking=True,
        ondelete='cascade',
        default=_default_nhan_vien_id,
    )
    
    # Loại nghỉ phép
    loai_nghi_phep = fields.Selection([
        ('phep_nam', 'Phép năm'),
        ('om', 'Nghỉ ốm'),
        ('om_khong_giay_to', 'Nghỉ ốm (không giấy tờ)'),
        ('thai_san', 'Nghỉ thai sản'),
        ('nhan_su', 'Nghỉ nhân sự'),
        ('cong_tac', 'Công tác'),
        ('khong_luong', 'Nghỉ không lương'),
    ], string="Loại nghỉ phép", required=True, tracking=True)
    
    # Thời gian
    ngay_bat_dau = fields.Date(string="Ngày bắt đầu", required=True, tracking=True)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc", required=True, tracking=True)
    so_ngay = fields.Float(string="Số ngày", compute="_compute_so_ngay", store=True)
    so_ngay_lam_viec = fields.Float(string="Số ngày làm việc", compute="_compute_so_ngay_lam_viec", store=True)
    
    # Thông tin nộp đơn
    ngay_nop_don = fields.Date(string="Ngày nộp đơn", default=fields.Date.today, tracking=True)
    
    # Phê duyệt cấp 1
    nguoi_duyet_cap_1_id = fields.Many2one('nhan_vien', string="Người duyệt cấp 1", tracking=True)
    ngay_duyet_cap_1 = fields.Date(string="Ngày duyệt cấp 1", tracking=True)
    ghi_chu_duyet_cap_1 = fields.Text(string="Ghi chú cấp 1")
    
    # Phê duyệt cấp 2 (nếu > 5 ngày)
    nguoi_duyet_cap_2_id = fields.Many2one('nhan_vien', string="Người duyệt cấp 2", tracking=True)
    ngay_duyet_cap_2 = fields.Date(string="Ngày duyệt cấp 2", tracking=True)
    ghi_chu_duyet_cap_2 = fields.Text(string="Ghi chú cấp 2")
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('cho_duyet', 'Chờ duyệt'),
        ('duyet_cap_1', 'Duyệt cấp 1'),
        ('duyet_cap_2', 'Duyệt cấp 2'),
        ('tu_choi', 'Từ chối'),
        ('huy_bo', 'Hủy bỏ'),
    ], string="Trạng thái", default='cho_duyet', required=True, tracking=True)
    
    # Chi tiết
    ly_do = fields.Text(string="Lý do")
    ghi_chu = fields.Text(string="Ghi chú")
    so_dien_thoai_lien_he = fields.Char(string="Số điện thoại liên hệ")
    nguoi_thay_the_id = fields.Many2one('nhan_vien', string="Người thay thế")
    
    # Giấy tờ đính kèm (cho phép ốm)
    file_giay_to = fields.Binary(string="File giấy tờ")
    file_name = fields.Char(string="Tên file")
    
    @api.depends('ngay_bat_dau', 'ngay_ket_thuc')
    def _compute_so_ngay(self):
        """Tính tổng số ngày (bao gồm cả ngày lễ)"""
        for record in self:
            if record.ngay_bat_dau and record.ngay_ket_thuc:
                delta = record.ngay_ket_thuc - record.ngay_bat_dau
                record.so_ngay = delta.days + 1  # +1 để bao gồm ngày bắt đầu
            else:
                record.so_ngay = 0
    
    @api.depends('ngay_bat_dau', 'ngay_ket_thuc')
    def _compute_so_ngay_lam_viec(self):
        """Tính số ngày làm việc (trừ thứ bảy, chủ nhật)"""
        for record in self:
            if record.ngay_bat_dau and record.ngay_ket_thuc:
                ngay_lam_viec = 0
                current_date = record.ngay_bat_dau
                while current_date <= record.ngay_ket_thuc:
                    # weekday(): 0=Monday, 5=Saturday, 6=Sunday
                    if current_date.weekday() < 5:  # Monday to Friday
                        ngay_lam_viec += 1
                    current_date += timedelta(days=1)
                record.so_ngay_lam_viec = ngay_lam_viec
            else:
                record.so_ngay_lam_viec = 0
    
    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for record in self:
            if record.ngay_bat_dau > record.ngay_ket_thuc:
                raise ValidationError(_("Ngày bắt đầu không thể lớn hơn ngày kết thúc!"))
            # Không cho phép nộp đơn cho quá khứ
            if record.ngay_bat_dau < fields.Date.today():
                raise ValidationError(_("Không được nộp đơn nghỉ phép cho ngày đã qua!"))
    
    @api.constrains('nhan_vien_id', 'ngay_bat_dau', 'ngay_ket_thuc', 'trang_thai')
    def _check_overlapping_leave(self):
        """Kiểm tra không có 2 đơn nghỉ phép trùng nhau"""
        for record in self:
            if record.trang_thai in ['duyet_cap_1', 'duyet_cap_2']:
                overlapping = self.search([
                    ('id', '!=', record.id),
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('trang_thai', 'in', ['duyet_cap_1', 'duyet_cap_2']),
                    ('ngay_bat_dau', '<=', record.ngay_ket_thuc),
                    ('ngay_ket_thuc', '>=', record.ngay_bat_dau),
                ])
                if overlapping:
                    raise ValidationError(_("Nhân viên đã có đơn nghỉ phép khác trong khoảng thời gian này!"))
    
    @api.constrains('loai_nghi_phep', 'file_giay_to')
    def _check_attach_for_sick_leave(self):
        """Kiểm tra giấy tờ khi nghỉ ốm (ngoài trường hợp 1 ngày không giấy tờ)"""
        for record in self:
            if record.loai_nghi_phep == 'om' and record.so_ngay > 1 and not record.file_giay_to:
                raise ValidationError(_("Nghỉ ốm từ 2 ngày trở lên cần đính kèm giấy tờ!"))

    def _get_attendance_status_from_leave_type(self):
        self.ensure_one()
        mapping = {
            'phep_nam': 'nghi_phep',
            'om': 'nghi_om',
            'om_khong_giay_to': 'nghi_om',
            'thai_san': 'nghi_phep',
            'nhan_su': 'nghi_phep',
            'cong_tac': 'cong_tac',
            'khong_luong': 'nghi_khong_luong',
        }
        return mapping.get(self.loai_nghi_phep, 'nghi_phep')

    def _sync_to_attendance(self):
        ChamCong = self.env['cham_cong']
        for record in self:
            if not (record.nhan_vien_id and record.ngay_bat_dau and record.ngay_ket_thuc):
                continue

            status = record._get_attendance_status_from_leave_type()
            current_date = record.ngay_bat_dau
            while current_date <= record.ngay_ket_thuc:
                if current_date.weekday() < 5:
                    existing = ChamCong.search([
                        ('nhan_vien_id', '=', record.nhan_vien_id.id),
                        ('ngay_cham_cong', '=', current_date),
                    ], limit=1)
                    vals = {
                        'nhan_vien_id': record.nhan_vien_id.id,
                        'ngay_cham_cong': current_date,
                        'trang_thai': status,
                        'ghi_chu': _("Đồng bộ từ đơn nghỉ phép %s") % record.ma_nghi_phep,
                    }
                    if existing:
                        existing.write({'trang_thai': status, 'ghi_chu': vals['ghi_chu']})
                    else:
                        ChamCong.create(vals)
                current_date += timedelta(days=1)
    
    def action_submit(self):
        """Nộp đơn - cập nhật trạng thái cho Chờ duyệt"""
        for record in self:
            if record.trang_thai != 'cho_duyet':
                raise ValidationError(_("Chỉ có thể nộp đơn ở trạng thái 'Chờ duyệt'!"))
            record.ngay_nop_don = fields.Date.today()
    
    def action_approve_level_1(self):
        """Duyệt cấp 1"""
        for record in self:
            if record.trang_thai != 'cho_duyet':
                raise ValidationError(_("Chỉ có thể duyệt đơn ở trạng thái 'Chờ duyệt'!"))
            
            record.trang_thai = 'duyet_cap_1'
            record.nguoi_duyet_cap_1_id = self.env.user.nhan_vien_id
            record.ngay_duyet_cap_1 = fields.Date.today()
            
            # Nếu số ngày <= 5, coi như duyệt hoàn toàn
            if record.so_ngay <= 5:
                record.trang_thai = 'duyet_cap_2'
                record.nguoi_duyet_cap_2_id = self.env.user.nhan_vien_id
                record.ngay_duyet_cap_2 = fields.Date.today()
                record._sync_to_attendance()
    
    def action_approve_level_2(self):
        """Duyệt cấp 2"""
        for record in self:
            # Đơn <= 5 ngày có thể đã tự động duyệt hoàn tất từ cấp 1
            if record.trang_thai == 'duyet_cap_2':
                continue
            if record.trang_thai != 'duyet_cap_1':
                raise ValidationError(_("Chỉ có thể duyệt cấp 2 khi đã duyệt cấp 1!"))
            
            record.trang_thai = 'duyet_cap_2'
            record.nguoi_duyet_cap_2_id = self.env.user.nhan_vien_id
            record.ngay_duyet_cap_2 = fields.Date.today()
            record._sync_to_attendance()
    
    def action_reject(self):
        """Từ chối đơn"""
        for record in self:
            if record.trang_thai not in ['cho_duyet', 'duyet_cap_1']:
                raise ValidationError(_("Không thể từ chối đơn ở trạng thái hiện tại!"))
            record.trang_thai = 'tu_choi'
    
    def action_cancel(self):
        """Hủy đơn"""
        for record in self:
            if record.trang_thai == 'tu_choi':
                raise ValidationError(_("Không thể hủy đơn đã bị từ chối!"))
            record.trang_thai = 'huy_bo'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_nghi_phep', _('New')) == _('New'):
                vals['ma_nghi_phep'] = self.env['ir.sequence'].next_by_code('nghi_phep') or _('New')
        return super().create(vals_list)
