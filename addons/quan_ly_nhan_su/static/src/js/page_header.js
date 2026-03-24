/** @odoo-module **/
/**
 * Tự động thêm tiêu đề trang vào control panel
 * Dựa vào action name hiện tại
 */

const PAGE_ICONS = {
    'Nhân viên':            { icon: 'fa-users',          color: '#00A09D' },
    'Hợp đồng':             { icon: 'fa-file-text',      color: '#00A09D' },
    'Hợp đồng sắp hết hạn': { icon: 'fa-clock-o',        color: '#F0A500' },
    'Chấm công':            { icon: 'fa-calendar-check-o',color: '#00A09D' },
    'Chấm công bất thường': { icon: 'fa-exclamation-triangle', color: '#DC3545' },
    'Phòng ban':            { icon: 'fa-sitemap',         color: '#00A09D' },
    'Chức vụ':              { icon: 'fa-id-badge',        color: '#00A09D' },
    'Nghỉ phép':            { icon: 'fa-calendar-minus-o',color: '#28A745' },
    'Tính lương':           { icon: 'fa-money',           color: '#F0A500' },
    'Tuyển dụng':           { icon: 'fa-user-plus',       color: '#00A09D' },
    'Đào tạo':              { icon: 'fa-graduation-cap',  color: '#7e3af2' },
    'Đánh giá':             { icon: 'fa-star',            color: '#F0A500' },
    // Công việc
    'Dự án':                { icon: 'fa-folder-open',     color: '#00A09D' },
    'Công việc':            { icon: 'fa-tasks',           color: '#00A09D' },
    'Timesheet':            { icon: 'fa-clock-o',         color: '#00A09D' },
    'Báo cáo tiến độ':      { icon: 'fa-bar-chart',       color: '#00A09D' },
    // Khách hàng
    'Khách hàng':           { icon: 'fa-handshake-o',     color: '#00A09D' },
    'Báo giá':              { icon: 'fa-file-text-o',     color: '#F0A500' },
    'Cơ hội bán hàng':      { icon: 'fa-line-chart',      color: '#28A745' },
    'Hợp đồng khách hàng':  { icon: 'fa-file-signature',  color: '#00A09D' },
    'Ticket hỗ trợ':        { icon: 'fa-life-ring',       color: '#DC3545' },
};

const SUBTITLES = {
    'Nhân viên':            'Danh sách hồ sơ nhân viên',
    'Hợp đồng':             'Quản lý hợp đồng lao động',
    'Hợp đồng sắp hết hạn': 'Hợp đồng hết hạn trong 30 ngày tới',
    'Chấm công':            'Ghi nhận thời gian làm việc',
    'Chấm công bất thường': 'Các trường hợp cần xem xét',
    'Phòng ban':            'Cơ cấu tổ chức phòng ban',
    'Chức vụ':              'Danh mục chức vụ trong doanh nghiệp',
    'Nghỉ phép':            'Quản lý đơn xin nghỉ phép',
    'Tính lương':           'Bảng lương và thanh toán',
    'Tuyển dụng':           'Hồ sơ ứng viên và tuyển dụng',
    'Đào tạo':              'Chương trình đào tạo nhân viên',
    'Đánh giá':             'Đánh giá hiệu suất làm việc',
    'Dự án':                'Quản lý dự án đang thực hiện',
    'Công việc':            'Phân công và theo dõi task',
    'Khách hàng':           'Hồ sơ và chăm sóc khách hàng',
    'Báo giá':              'Tạo và gửi báo giá khách hàng',
    'Cơ hội bán hàng':      'Pipeline CRM và theo dõi deal',
    'Hợp đồng khách hàng':  'Quản lý hợp đồng với khách hàng',
    'Ticket hỗ trợ':        'Yêu cầu hỗ trợ và xử lý SLA',
};

function injectPageHeader() {
    // Lấy tiêu đề từ breadcrumb Odoo
    const breadcrumb = document.querySelector('.o_breadcrumb .o_last_breadcrumb_item');
    if (!breadcrumb) return;
    const title = breadcrumb.textContent.trim();

    // Chỉ inject vào list/kanban/calendar, không inject vào form
    const isListView = document.querySelector('.o_list_view, .o_kanban_view, .o_calendar_view');
    if (!isListView) return;

    // Tránh inject 2 lần
    if (document.querySelector('.erp-page-header')) return;

    const meta = PAGE_ICONS[title];
    if (!meta) return;

    const subtitle = SUBTITLES[title] || '';
    const header = document.createElement('div');
    header.className = 'erp-page-header';
    header.innerHTML = `
        <div class="erp-page-header-left">
            <div class="erp-page-header-icon" style="background:${meta.color}">
                <i class="fa ${meta.icon}"></i>
            </div>
            <div>
                <div class="erp-page-header-title">${title}</div>
                ${subtitle ? `<div class="erp-page-header-sub">${subtitle}</div>` : ''}
            </div>
        </div>
    `;

    // Insert trước list view
    const view = document.querySelector('.o_list_view, .o_kanban_view, .o_calendar_view');
    if (view && view.parentElement) {
        view.parentElement.insertBefore(header, view);
    }
}

// CSS inject
const style = document.createElement('style');
style.textContent = `
.erp-page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 0 12px;
    margin-bottom: 4px;
    border-bottom: 1px solid #DDE5EA;
}
.erp-page-header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}
.erp-page-header-icon {
    width: 40px; height: 40px;
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.erp-page-header-icon .fa {
    font-size: 17px; color: #fff;
}
.erp-page-header-title {
    font-size: 18px; font-weight: 700; color: #1C2B33; line-height: 1.3;
}
.erp-page-header-sub {
    font-size: 12px; color: #6B7A85; margin-top: 1px;
}
`;
document.head.appendChild(style);

// Theo dõi DOM thay đổi (SPA navigation)
const obs = new MutationObserver(() => {
    setTimeout(injectPageHeader, 200);
});

if (document.body) obs.observe(document.body, { childList: true, subtree: true });
else document.addEventListener('DOMContentLoaded', () => {
    obs.observe(document.body, { childList: true, subtree: true });
});
