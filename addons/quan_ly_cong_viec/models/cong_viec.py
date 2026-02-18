# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CongViec(models.Model):
    _name = "cong_viec"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Công việc"
    _rec_name = "ten_cong_viec"
    _order = "ngay_bat_dau, ma_cong_viec"
    
    ma_cong_viec = fields.Char(string="Mã công việc", required=True, index=True)
    ten_cong_viec = fields.Char(string="Tên công việc", required=True)
    mo_ta = fields.Text(string="Mô tả")
    
    # Thời gian
    ngay_bat_dau = fields.Date(string="Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc")
    
    # Quan hệ
    du_an_id = fields.Many2one('du_an', string="Thuộc dự án", required=True, ondelete='cascade')
    nguoi_phu_trach_id = fields.Many2one('nhan_vien', string="Người phụ trách")
    
    # Các trường quan hệ tham chiếu ngược
    nguoi_tham_gia_ids = fields.One2many('nguoi_tham_gia', 'cong_viec_id', string="Người tham gia")
    bao_cao_tien_do_ids = fields.One2many('bao_cao_tien_do', 'cong_viec_id', string="Báo cáo tiến độ")
    nguon_luc_ids = fields.One2many('phan_bo_nguon_luc', 'cong_viec_id', string="Nguồn lực phân bổ")
    
    # Thông tin tiến độ
    ke_hoach_gio = fields.Float(string="Kế hoạch (giờ)")
    thuc_te_gio = fields.Float(string="Thực tế (giờ)", compute="_compute_thuc_te_gio", store=True)
    tien_do = fields.Float(string="Tiến độ (%)", compute="_compute_tien_do", store=True)
    
    # Độ ưu tiên, trạng thái
    do_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('rat_cao', 'Rất cao')
    ], string="Độ ưu tiên", default='trung_binh')
    
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('tam_dung', 'Tạm dừng'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy_bo', 'Hủy bỏ')
    ], string="Trạng thái", default='moi', tracking=True)
    
    _sql_constraints = [
        ('ma_cong_viec_unique', 'unique(ma_cong_viec)', 'Mã công việc phải là duy nhất!'),
    ]
    
    @api.depends('bao_cao_tien_do_ids', 'bao_cao_tien_do_ids.so_gio')
    def _compute_thuc_te_gio(self):
        for record in self:
            record.thuc_te_gio = sum(record.bao_cao_tien_do_ids.mapped('so_gio'))
    
    @api.depends('bao_cao_tien_do_ids', 'bao_cao_tien_do_ids.tien_do')
    def _compute_tien_do(self):
        for record in self:
            if record.bao_cao_tien_do_ids:
                # Lấy báo cáo tiến độ mới nhất
                bao_cao_moi_nhat = record.bao_cao_tien_do_ids.sorted(key=lambda r: r.ngay_bao_cao, reverse=True)[0]
                record.tien_do = bao_cao_moi_nhat.tien_do
            else:
                record.tien_do = 0
    
    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for record in self:
            if record.ngay_ket_thuc and record.ngay_bat_dau > record.ngay_ket_thuc:
                raise ValidationError(_("Ngày bắt đầu không thể sau ngày kết thúc!"))
    
    @api.constrains('du_an_id', 'ngay_bat_dau', 'ngay_ket_thuc')
    def _check_project_dates(self):
        for record in self:
            if record.du_an_id.ngay_bat_dau and record.ngay_bat_dau < record.du_an_id.ngay_bat_dau:
                raise ValidationError(_("Ngày bắt đầu công việc không thể trước ngày bắt đầu dự án!"))
            
            if record.du_an_id.ngay_ket_thuc and record.ngay_ket_thuc and record.ngay_ket_thuc > record.du_an_id.ngay_ket_thuc:
                raise ValidationError(_("Ngày kết thúc công việc không thể sau ngày kết thúc dự án!"))

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

    def _create_single_activity(self, summary, note, deadline=False):
        todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        model_id = self.env['ir.model']._get_id('cong_viec')
        fallback_user = self.env.ref('base.user_admin', raise_if_not_found=False) or self.env.user

        for task in self:
            owner_user = self._find_user_from_employee(task.nguoi_phu_trach_id)
            if not owner_user:
                owner_user = self._find_user_from_employee(task.du_an_id.nguoi_quan_ly_id)
            if not owner_user:
                owner_user = fallback_user

            existed = self.env['mail.activity'].sudo().search_count([
                ('res_model_id', '=', model_id),
                ('res_id', '=', task.id),
                ('user_id', '=', owner_user.id),
                ('summary', '=', summary),
            ])
            if existed:
                continue

            values = {
                'res_model_id': model_id,
                'res_id': task.id,
                'user_id': owner_user.id,
                'summary': summary,
                'note': note,
                'date_deadline': deadline or fields.Date.today(),
            }
            if todo_type:
                values['activity_type_id'] = todo_type.id
            self.env['mail.activity'].sudo().create(values)

    @api.model
    def _cron_task_automation(self):
        today = fields.Date.today()
        stale_days = max(self._get_int_param('quan_ly_cong_viec.task_stale_days', 3), 1)

        overdue_tasks = self.search([
            ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo']),
            ('ngay_ket_thuc', '!=', False),
            ('ngay_ket_thuc', '<', today),
        ])
        for task in overdue_tasks:
            values = {'do_uu_tien': 'rat_cao'}
            if task.trang_thai == 'moi':
                values['trang_thai'] = 'dang_thuc_hien'
            task.write(values)
            task._create_single_activity(
                summary=_("Công việc quá hạn: %s") % task.ten_cong_viec,
                note=_(
                    "Công việc đã quá hạn từ ngày %(deadline)s, tiến độ hiện tại %(progress)s%%. "
                    "Vui lòng xử lý ưu tiên."
                ) % {
                    'deadline': task.ngay_ket_thuc,
                    'progress': task.tien_do,
                },
                deadline=today,
            )

        stale_day = fields.Date.add(today, days=-stale_days)
        stale_tasks = self.search([
            ('trang_thai', 'in', ['moi', 'dang_thuc_hien']),
            ('ngay_bat_dau', '!=', False),
            ('ngay_bat_dau', '<=', stale_day),
        ])
        stale_tasks = stale_tasks.filtered(lambda task: not task.bao_cao_tien_do_ids)
        for task in stale_tasks:
            task._create_single_activity(
                summary=_("Công việc chưa cập nhật tiến độ: %s") % task.ten_cong_viec,
                note=_(
                    "Công việc đã bắt đầu từ %(start)s nhưng chưa có báo cáo tiến độ. "
                    "Vui lòng cập nhật trạng thái thực tế."
                ) % {
                    'start': task.ngay_bat_dau,
                },
                deadline=today,
            )
