# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ChamCong(models.Model):
    _name = "cham_cong"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Quản lý chấm công"
    _rec_name = "display_name"
    _order = "ngay_cham_cong desc, nhan_vien_id"
    
    display_name = fields.Char(string="Tên hiển thị", compute="_compute_display_name", store=True)
    
    # Các mối quan hệ
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, tracking=True)
    
    # Thông tin chấm công
    ngay_cham_cong = fields.Date(string="Ngày chấm công", required=True, default=fields.Date.today, tracking=True)
    thoi_gian_vao = fields.Datetime(string="Thời gian vào", tracking=True)
    thoi_gian_ra = fields.Datetime(string="Thời gian ra", tracking=True)
    trang_thai = fields.Selection([
        ('di_lam', 'Đi làm'),
        ('nghi_phep', 'Nghỉ phép'),
        ('nghi_le', 'Nghỉ lễ'),
        ('nghi_om', 'Nghỉ ốm'),
        ('nghi_khong_luong', 'Nghỉ không lương'),
        ('cong_tac', 'Công tác')
    ], string="Trạng thái", default='di_lam', required=True, tracking=True)
    
    # Giờ làm việc tính toán
    gio_lam_viec = fields.Float(string="Giờ làm việc", compute="_compute_gio_lam_viec", store=True)
    
    # Thông tin nghỉ phép
    ly_do_nghi = fields.Text(string="Lý do nghỉ", 
                           help="Chỉ áp dụng khi trạng thái là nghỉ phép, nghỉ ốm hoặc nghỉ không lương")
    nguoi_duyet_id = fields.Many2one('nhan_vien', string="Người duyệt")
    ngay_duyet = fields.Date(string="Ngày duyệt")
    
    # Ghi chú
    ghi_chu = fields.Text(string="Ghi chú")
    
    @api.depends('nhan_vien_id', 'ngay_cham_cong')
    def _compute_display_name(self):
        for record in self:
            if record.nhan_vien_id and record.ngay_cham_cong:
                record.display_name = f"{record.nhan_vien_id.ho_va_ten} - {record.ngay_cham_cong}"
            else:
                record.display_name = False
    
    @api.depends('thoi_gian_vao', 'thoi_gian_ra', 'trang_thai')
    def _compute_gio_lam_viec(self):
        for record in self:
            if record.trang_thai == 'di_lam' and record.thoi_gian_vao and record.thoi_gian_ra:
                delta = record.thoi_gian_ra - record.thoi_gian_vao
                record.gio_lam_viec = delta.total_seconds() / 3600.0
            else:
                record.gio_lam_viec = 0.0
    
    @api.constrains('thoi_gian_vao', 'thoi_gian_ra')
    def _check_thoi_gian(self):
        for record in self:
            if record.thoi_gian_vao and record.thoi_gian_ra and record.thoi_gian_vao > record.thoi_gian_ra:
                raise ValidationError(_("Thời gian vào không thể sau thời gian ra!"))
            
            if record.thoi_gian_vao and record.thoi_gian_ra:
                ngay_vao = record.thoi_gian_vao.date()
                ngay_ra = record.thoi_gian_ra.date()
                if ngay_vao != record.ngay_cham_cong or ngay_ra != record.ngay_cham_cong:
                    raise ValidationError(_("Thời gian vào và thời gian ra phải cùng ngày với ngày chấm công!"))
    
    _sql_constraints = [
        ('nhan_vien_ngay_unique', 'unique(nhan_vien_id, ngay_cham_cong)', 
         'Mỗi nhân viên chỉ có một bản ghi chấm công cho mỗi ngày!'),
    ]

    def _find_user_from_employee(self, employee):
        if not employee or not employee.email:
            return False
        return self.env['res.users'].sudo().search([
            '|', ('login', '=', employee.email), ('email', '=', employee.email)
        ], limit=1)

    @api.model
    def _get_int_param(self, key, default):
        value = self.env['ir.config_parameter'].sudo().get_param(key, default=str(default))
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @api.model
    def _cron_attendance_anomaly_alerts(self):
        lookback_days = max(self._get_int_param('quan_ly_nhan_su.attendance_anomaly_lookback_days', 1), 1)
        yesterday = fields.Date.add(fields.Date.today(), days=-lookback_days)
        anomaly_records = self.search([
            ('ngay_cham_cong', '=', yesterday),
            ('trang_thai', '=', 'di_lam'),
            ('thoi_gian_vao', '!=', False),
            ('thoi_gian_ra', '=', False),
        ])
        if not anomaly_records:
            return

        todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        model_id = self.env['ir.model']._get_id('cham_cong')
        fallback_user = self.env.ref('base.user_admin', raise_if_not_found=False) or self.env.user

        for attendance in anomaly_records:
            owner_user = self._find_user_from_employee(attendance.nhan_vien_id.quan_ly_id)
            if not owner_user:
                owner_user = fallback_user

            summary = _("Bất thường chấm công: %s") % attendance.nhan_vien_id.ho_va_ten
            existed = self.env['mail.activity'].sudo().search_count([
                ('res_model_id', '=', model_id),
                ('res_id', '=', attendance.id),
                ('user_id', '=', owner_user.id),
                ('summary', '=', summary),
            ])
            if existed:
                continue

            values = {
                'res_model_id': model_id,
                'res_id': attendance.id,
                'user_id': owner_user.id,
                'summary': summary,
                'date_deadline': fields.Date.today(),
                'note': _(
                    "Nhân viên %(employee)s có dữ liệu chấm công ngày %(date)s "
                    "với giờ vào nhưng chưa có giờ ra. Vui lòng kiểm tra và cập nhật."
                ) % {
                    'employee': attendance.nhan_vien_id.ho_va_ten,
                    'date': attendance.ngay_cham_cong,
                },
            }
            if todo_type:
                values['activity_type_id'] = todo_type.id
            self.env['mail.activity'].sudo().create(values)
