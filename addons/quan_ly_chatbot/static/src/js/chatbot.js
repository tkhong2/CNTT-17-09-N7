/**
 * ERP Chatbot — dùng odoo.define legacy + session.rpc
 * Đúng chuẩn Odoo 15, không bị lỗi 404/CSRF
 */
odoo.define('quan_ly_chatbot.chatbot', function (require) {
    'use strict';

    var Widget = require('web.Widget');
    var session = require('web.session');

    var ERPChatbot = Widget.extend({
        conversationId: null,
        isOpen: false,
        isBusy: false,

        start: function () {
            this._super.apply(this, arguments);
            this._renderUI();
            this._bindEvents();
            setTimeout(() => this._showWelcome(), 800);
        },

        // ── Render HTML ─────────────────────────────────────────
        _renderUI: function () {
            var C = '#00A09D';
            var html = `
<div id="ecb-fab" style="position:fixed;bottom:24px;right:24px;z-index:99999;
  width:56px;height:56px;border-radius:50%;background:${C};cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 4px 20px rgba(0,160,157,.5);transition:transform .2s">
  <i id="ecb-fab-icon" class="fa fa-comments" style="color:#fff;font-size:22px"></i>
  <span id="ecb-badge" style="display:none;position:absolute;top:-4px;right:-4px;
    background:#e02424;color:#fff;font-size:9px;font-weight:800;padding:2px 6px;
    border-radius:999px;border:2px solid #fff">AI</span>
</div>

<div id="ecb-win" style="display:none;position:fixed;bottom:90px;right:24px;z-index:99999;
  width:390px;max-height:580px;background:#fff;border-radius:16px;
  box-shadow:0 16px 50px rgba(0,0,0,.15);border:1px solid #DDE5EA;
  flex-direction:column;overflow:hidden;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">

  <!-- Header -->
  <div style="background:${C};padding:12px 14px;display:flex;align-items:center;gap:10px;flex-shrink:0">
    <div style="width:36px;height:36px;background:rgba(255,255,255,.2);border-radius:50%;
      display:flex;align-items:center;justify-content:center">
      <i class="fa fa-robot" style="color:#fff;font-size:16px"></i>
    </div>
    <div style="flex:1">
      <div style="color:#fff;font-size:14px;font-weight:700">
        Trợ lý ERP
        <span style="background:rgba(255,255,255,.2);border-radius:999px;
          font-size:9px;padding:2px 7px;margin-left:4px">AI</span>
      </div>
      <div style="color:rgba(255,255,255,.85);font-size:11px;margin-top:1px">
        <span style="color:#7FFFD4">●</span> Đang hoạt động
      </div>
    </div>
    <button id="ecb-close" style="background:rgba(255,255,255,.15);
      border:1px solid rgba(255,255,255,.25);color:#fff;width:28px;height:28px;
      border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center">
      <i class="fa fa-times" style="font-size:13px"></i>
    </button>
  </div>

  <!-- Quick topics -->
  <div style="padding:8px 12px;display:flex;gap:6px;flex-wrap:wrap;
    background:#FAFCFC;border-bottom:1px solid #DDE5EA;flex-shrink:0">
    <button class="ecb-topic" data-q="Xin chào"
      style="padding:4px 11px;border-radius:999px;border:1px solid #B2D8D6;
      background:#fff;color:#007B78;font-size:11px;font-weight:600;cursor:pointer">
      <i class="fa fa-hand-o-right"></i> Xin chào
    </button>
    <button class="ecb-topic" data-q="Thống kê tổng quan hệ thống"
      style="padding:4px 11px;border-radius:999px;border:1px solid #B2D8D6;
      background:#fff;color:#007B78;font-size:11px;font-weight:600;cursor:pointer">
      <i class="fa fa-bar-chart"></i> Thống kê
    </button>
    <button class="ecb-topic" data-q="Task của tôi đang xử lý"
      style="padding:4px 11px;border-radius:999px;border:1px solid #B2D8D6;
      background:#fff;color:#007B78;font-size:11px;font-weight:600;cursor:pointer">
      <i class="fa fa-tasks"></i> Task của tôi
    </button>
    <button class="ecb-topic" data-q="Hướng dẫn sử dụng hệ thống"
      style="padding:4px 11px;border-radius:999px;border:1px solid #B2D8D6;
      background:#fff;color:#007B78;font-size:11px;font-weight:600;cursor:pointer">
      <i class="fa fa-question-circle"></i> Hướng dẫn
    </button>
  </div>

  <!-- Messages -->
  <div id="ecb-msgs" style="flex:1;overflow-y:auto;padding:12px 14px 6px;
    display:flex;flex-direction:column;gap:10px;
    min-height:180px;max-height:310px;scroll-behavior:smooth"></div>

  <!-- Suggestions -->
  <div id="ecb-sugg" style="display:flex;flex-wrap:wrap;gap:5px;
    padding:4px 14px 5px;flex-shrink:0"></div>

  <!-- Input -->
  <div style="padding:10px 12px;border-top:1px solid #DDE5EA;
    display:flex;gap:8px;align-items:flex-end;background:#fff;flex-shrink:0">
    <textarea id="ecb-inp" rows="1"
      placeholder="Nhập câu hỏi về ERP..."
      style="flex:1;border:1.5px solid #B2D8D6;border-radius:10px;padding:8px 12px;
      font-size:13px;resize:none;outline:none;font-family:inherit;color:#1C2B33;
      background:#F4F7F9;max-height:90px;min-height:36px;line-height:1.4"></textarea>
    <button id="ecb-send" style="width:36px;height:36px;border-radius:9px;background:${C};
      border:none;color:#fff;cursor:pointer;display:flex;align-items:center;
      justify-content:center;flex-shrink:0;box-shadow:0 3px 10px rgba(0,160,157,.35)">
      <i class="fa fa-paper-plane" style="font-size:13px"></i>
    </button>
  </div>

  <!-- Footer -->
  <div style="text-align:center;font-size:10px;color:#9BADB8;
    padding:4px 12px 7px;border-top:1px solid #F0F5FA;background:#FAFCFC;flex-shrink:0">
    Trợ lý ERP &mdash; Gemini AI + Rule-based
  </div>

</div>`;

            var $container = $('<div>').html(html);
            $('body').append($container);
        },

        // ── Events ───────────────────────────────────────────────
        _bindEvents: function () {
            var self = this;

            $('#ecb-fab').on('click', function () { self._toggle(); });
            $('#ecb-close').on('click', function () { self._close(); });
            $('#ecb-send').on('click', function () { self._handleSend(); });

            $('#ecb-inp').on('keydown', function (e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    self._handleSend();
                }
            }).on('input', function () {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 90) + 'px';
            });

            // Topics
            $(document).on('click', '.ecb-topic', function () {
                var q = $(this).data('q');
                if (q) self._send(q);
            });

            // Suggestions (delegate vì dynamic)
            $(document).on('click', '.ecb-sugg-btn', function () {
                var q = $(this).data('q');
                if (q) {
                    $('#ecb-sugg').empty();
                    self._send(q);
                }
            });
        },

        // ── Window ──────────────────────────────────────────────
        _toggle: function () { this.isOpen ? this._close() : this._open(); },

        _open: function () {
            this.isOpen = true;
            $('#ecb-win').css('display', 'flex');
            $('#ecb-fab-icon').removeClass('fa-comments').addClass('fa-times');
            $('#ecb-badge').hide();
            setTimeout(function () { $('#ecb-inp').focus(); }, 100);
        },

        _close: function () {
            this.isOpen = false;
            $('#ecb-win').hide();
            $('#ecb-fab-icon').removeClass('fa-times').addClass('fa-comments');
        },

        // ── Send ────────────────────────────────────────────────
        _handleSend: function () {
            var txt = $('#ecb-inp').val().trim();
            if (!txt || this.isBusy) return;
            $('#ecb-inp').val('').css('height', 'auto');
            this._send(txt);
        },

        _send: function (message) {
            var self = this;
            if (this.isBusy) return;

            this._addUserBubble(message);
            $('#ecb-sugg').empty();
            this.isBusy = true;
            $('#ecb-send').prop('disabled', true).css('opacity', '0.4');
            var typingId = this._showTyping();

            // Gọi Python controller qua session.rpc (Odoo chuẩn)
            session.rpc('/erp_chatbot/message', {
                message: message,
                conversation_id: self.conversationId || false,
            }).then(function (result) {
                self._removeTyping(typingId);
                self.isBusy = false;
                $('#ecb-send').prop('disabled', false).css('opacity', '1');

                if (result && result.answer) {
                    self.conversationId = result.conversation_id;
                    self._addBotBubble(result.answer);
                    if (result.suggestions && result.suggestions.length) {
                        self._showSuggestions(result.suggestions);
                    }
                }
            }).catch(function (err) {
                self._removeTyping(typingId);
                self.isBusy = false;
                $('#ecb-send').prop('disabled', false).css('opacity', '1');
                self._addBotBubble('❌ <strong>Lỗi:</strong> ' +
                    (err.message || 'Không kết nối được server. Vui lòng thử lại.'));
                console.error('Chatbot error:', err);
            });
        },

        // ── Bubbles ─────────────────────────────────────────────
        _addUserBubble: function (text) {
            var escaped = $('<div>').text(text).html();
            var $div = $('<div>').css({display: 'flex', justifyContent: 'flex-end'})
                .html('<div style="max-width:80%;padding:9px 13px;background:#00A09D;color:#fff;' +
                      'border-radius:14px;border-bottom-right-radius:3px;font-size:13px;' +
                      'line-height:1.5;word-break:break-word">' + escaped + '</div>');
            $('#ecb-msgs').append($div);
            this._scroll();
        },

        _addBotBubble: function (html) {
            var formatted = this._format(html);
            var $div = $('<div>').css({display: 'flex', gap: '8px', alignItems: 'flex-end'})
                .html('<div style="width:28px;height:28px;background:#00A09D;border-radius:50%;' +
                      'flex-shrink:0;display:flex;align-items:center;justify-content:center">' +
                      '<i class="fa fa-robot" style="color:#fff;font-size:12px"></i></div>' +
                      '<div style="max-width:83%;padding:9px 13px;background:#F4F7F9;color:#1C2B33;' +
                      'border-radius:14px;border-bottom-left-radius:3px;border:1px solid #DDE5EA;' +
                      'font-size:13px;line-height:1.6;word-break:break-word">' + formatted + '</div>');
            $('#ecb-msgs').append($div);
            this._scroll();
        },

        _format: function (text) {
            // Gemini trả về markdown -> convert sang HTML
            return text
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.+?)\*/g, '<em>$1</em>')
                .replace(/^#{1,4}\s+(.+)$/gm, '<strong>$1</strong>')
                .replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>')
                .replace(/(<li>[\s\S]+?<\/li>)/g, '<ul style="margin:4px 0;padding-left:18px">$1</ul>')
                .replace(/<\/ul>\s*<ul[^>]*>/g, '')
                .replace(/\n{2,}/g, '<br><br>')
                .replace(/\n/g, '<br>');
        },

        _showTyping: function () {
            var id = 'ecb-typing-' + Date.now();
            if (!$('#ecb-anim').length) {
                $('<style id="ecb-anim">').text(
                    '.ecb-dot{width:7px;height:7px;background:#B2D8D6;border-radius:50%;' +
                    'display:inline-block;animation:ecbBop 1.2s infinite}' +
                    '.ecb-dot:nth-child(2){animation-delay:.2s}' +
                    '.ecb-dot:nth-child(3){animation-delay:.4s}' +
                    '@keyframes ecbBop{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-6px)}}'
                ).appendTo('head');
            }
            var $div = $('<div>').attr('id', id)
                .css({display: 'flex', gap: '8px', alignItems: 'flex-end'})
                .html('<div style="width:28px;height:28px;background:#00A09D;border-radius:50%;' +
                      'flex-shrink:0;display:flex;align-items:center;justify-content:center">' +
                      '<i class="fa fa-robot" style="color:#fff;font-size:12px"></i></div>' +
                      '<div style="padding:10px 14px;background:#F4F7F9;border-radius:14px;' +
                      'border-bottom-left-radius:3px;border:1px solid #DDE5EA;' +
                      'display:flex;gap:4px;align-items:center">' +
                      '<span class="ecb-dot"></span>' +
                      '<span class="ecb-dot"></span>' +
                      '<span class="ecb-dot"></span></div>');
            $('#ecb-msgs').append($div);
            this._scroll();
            return id;
        },

        _removeTyping: function (id) { $('#' + id).remove(); },

        _showSuggestions: function (items) {
            var html = items.map(function (s) {
                return '<button class="ecb-sugg-btn" data-q="' + s + '" ' +
                    'style="padding:4px 11px;background:#E0F5F5;border:1px solid #B2D8D6;' +
                    'border-radius:999px;font-size:11px;color:#007B78;font-weight:600;cursor:pointer">' +
                    s + '</button>';
            }).join('');
            $('#ecb-sugg').html(html);
        },

        _showWelcome: function () {
            this._addBotBubble(
                '👋 <strong>Xin chào! Tôi là Trợ lý ERP AI.</strong><br><br>' +
                'Tôi có thể giúp bạn:<br>' +
                '<ul style="margin:4px 0;padding-left:18px">' +
                '<li><strong>Nhân sự</strong> – nhân viên, lương, chấm công</li>' +
                '<li><strong>Công việc</strong> – dự án, task, tiến độ</li>' +
                '<li><strong>Khách hàng</strong> – CRM, báo giá, hợp đồng</li>' +
                '<li><strong>Thống kê</strong> tổng quan hệ thống</li>' +
                '</ul>' +
                'Nhấn nút nhanh phía trên hoặc gõ câu hỏi! 💬'
            );
            this._showSuggestions(['Thống kê tổng quan', 'Task của tôi', 'Hướng dẫn']);
        },

        _scroll: function () {
            var el = document.getElementById('ecb-msgs');
            if (el) el.scrollTop = el.scrollHeight;
        },
    });

    // ── Mount vào body sau khi Odoo load xong ──────────────────
    $(document).ready(function () {
        setTimeout(function () {
            var widget = new ERPChatbot(null);
            widget.appendTo($('body'));
        }, 2000);
    });

    return ERPChatbot;
});
