# -*- coding: utf-8 -*-
"""
Telegram Bot Integration
Gửi thông báo tự động khi:
1. Hợp đồng lao động sắp hết hạn (cron hàng ngày)
2. Đơn nghỉ phép chờ duyệt (tức thì khi tạo)
3. Task bị chặn (từ module công việc)
4. Chatbot hỏi về thống kê → gửi báo cáo PDF qua Telegram
"""
import requests
import logging
from datetime import timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramConfig(models.Model):
    _name = 'telegram.config'
    _description = 'Cấu hình Telegram Bot'
    _rec_name = 'name'

    name       = fields.Char('Tên cấu hình', default='Telegram ERP Bot', required=True)
    bot_token  = fields.Char('Bot Token', help='Lấy từ @BotFather trên Telegram')
    chat_id    = fields.Char('Chat ID', help='ID nhóm hoặc cá nhân nhận thông báo')
    active     = fields.Boolean('Kích hoạt', default=True)

    # Cài đặt loại thông báo
    notify_hop_dong   = fields.Boolean('Cảnh báo hợp đồng sắp hết hạn', default=True)
    notify_nghi_phep  = fields.Boolean('Thông báo đơn nghỉ phép mới', default=True)
    notify_task_block = fields.Boolean('Cảnh báo task bị chặn', default=True)
    notify_daily      = fields.Boolean('Báo cáo hàng ngày', default=False)
    hop_dong_days     = fields.Integer('Cảnh báo trước (ngày)', default=30)

    def _send(self, message, parse_mode='HTML'):
        """Gửi tin nhắn Telegram. Trả về True nếu thành công."""
        if not self.bot_token or not self.chat_id:
            _logger.warning("Telegram: Chưa cấu hình bot_token hoặc chat_id")
            return False
        try:
            url = TELEGRAM_API.format(token=self.bot_token)
            resp = requests.post(url, json={
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
            }, timeout=10)
            if resp.status_code == 200:
                _logger.info("Telegram: Gửi thành công")
                return True
            else:
                _logger.warning("Telegram error %s: %s", resp.status_code, resp.text[:200])
                return False
        except Exception as e:
            _logger.warning("Telegram exception: %s", e)
            return False

    def action_test(self):
        """Nút test gửi tin nhắn thử."""
        ok = self._send(
            "✅ <b>ERP System</b>\nKết nối Telegram thành công!\n"
            f"Hệ thống đang hoạt động bình thường."
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Telegram',
                'message': 'Gửi thành công!' if ok else 'Gửi thất bại! Kiểm tra token/chat_id.',
                'type': 'success' if ok else 'danger',
            }
        }

    @api.model
    def _get_active(self):
        return self.search([('active', '=', True)], limit=1)

    # ──────────────────────────────────────────────────────────────
    # CRON: Cảnh báo hợp đồng sắp hết hạn
    # ──────────────────────────────────────────────────────────────
    @api.model
    def _cron_notify_hop_dong_sap_het_han(self):
        cfg = self._get_active()
        if not cfg or not cfg.notify_hop_dong:
            return
        deadline = fields.Date.today() + timedelta(days=cfg.hop_dong_days)
        contracts = self.env['hop_dong'].search([
            ('trang_thai', '=', 'hieu_luc'),
            ('ngay_ket_thuc', '<=', deadline),
            ('ngay_ket_thuc', '>=', fields.Date.today()),
        ])
        if not contracts:
            return
        lines = [f"⚠️ <b>CẢNH BÁO: {len(contracts)} hợp đồng sắp hết hạn</b>\n"]
        for c in contracts[:10]:
            nv_name = c.nhan_vien_id.ho_va_ten if c.nhan_vien_id else 'N/A'
            days_left = (c.ngay_ket_thuc - fields.Date.today()).days
            lines.append(f"👤 <b>{nv_name}</b> — HĐ: {c.ma_hop_dong}\n"
                        f"   📅 Hết hạn: {c.ngay_ket_thuc.strftime('%d/%m/%Y')} "
                        f"(còn <b>{days_left} ngày</b>)")
        if len(contracts) > 10:
            lines.append(f"\n... và {len(contracts)-10} hợp đồng khác")
        cfg._send('\n'.join(lines))

    # ──────────────────────────────────────────────────────────────
    # CRON: Báo cáo hàng ngày
    # ──────────────────────────────────────────────────────────────
    @api.model
    def _cron_daily_report(self):
        cfg = self._get_active()
        if not cfg or not cfg.notify_daily:
            return
        today = fields.Date.today().strftime('%d/%m/%Y')
        NV  = self.env['nhan_vien']
        CV  = self.env['cong_viec']
        KH  = self.env['khach_hang']
        NP  = self.env['nghi_phep']
        nv_active = NV.search_count([('trang_thai', '=', 'active')])
        cv_open   = CV.search_count([('trang_thai', 'not in', ['hoan_thanh', 'huy_bo'])])
        cv_block  = CV.search_count([('bi_chan', '=', True), ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo'])])
        kh_total  = KH.search_count([('active', '=', True)])
        np_cho    = NP.search_count([('trang_thai', '=', 'cho_duyet')])
        msg = (
            f"📊 <b>BÁO CÁO NGÀY {today}</b>\n\n"
            f"👥 Nhân viên đang làm việc: <b>{nv_active}</b>\n"
            f"📋 Task đang mở: <b>{cv_open}</b> | Bị chặn: <b>{cv_block}</b>\n"
            f"🤝 Tổng khách hàng: <b>{kh_total}</b>\n"
            f"🏖️ Đơn nghỉ chờ duyệt: <b>{np_cho}</b>"
        )
        cfg._send(msg)

    # ──────────────────────────────────────────────────────────────
    # TRIGGER: Thông báo khi có đơn nghỉ phép mới
    # ──────────────────────────────────────────────────────────────
    @api.model
    def notify_nghi_phep_moi(self, nghi_phep):
        cfg = self._get_active()
        if not cfg or not cfg.notify_nghi_phep:
            return
        nv = nghi_phep.nhan_vien_id
        msg = (
            f"🏖️ <b>ĐƠN NGHỈ PHÉP MỚI</b>\n\n"
            f"👤 Nhân viên: <b>{nv.ho_va_ten if nv else 'N/A'}</b>\n"
            f"📅 Từ: <b>{nghi_phep.ngay_bat_dau.strftime('%d/%m/%Y') if nghi_phep.ngay_bat_dau else 'N/A'}</b>"
            f" → <b>{nghi_phep.ngay_ket_thuc.strftime('%d/%m/%Y') if nghi_phep.ngay_ket_thuc else 'N/A'}</b>\n"
            f"📝 Lý do: {nghi_phep.ly_do or 'Không có'}\n"
            f"⏳ Trạng thái: <b>Chờ duyệt</b>"
        )
        cfg._send(msg)

    # ──────────────────────────────────────────────────────────────
    # TRIGGER: Thông báo task bị chặn
    # ──────────────────────────────────────────────────────────────
    @api.model
    def notify_task_bi_chan(self, task):
        cfg = self._get_active()
        if not cfg or not cfg.notify_task_block:
            return
        nv = task.nguoi_phu_trach_id
        da = task.du_an_id
        msg = (
            f"🔴 <b>TASK BỊ CHẶN</b>\n\n"
            f"📋 Task: <b>{task.ten_cong_viec}</b>\n"
            f"📁 Dự án: {da.ten_du_an if da else 'N/A'}\n"
            f"👤 Phụ trách: {nv.ho_va_ten if nv else 'N/A'}\n"
            f"📅 Deadline: {task.ngay_ket_thuc.strftime('%d/%m/%Y') if task.ngay_ket_thuc else 'Chưa có'}"
        )
        cfg._send(msg)
