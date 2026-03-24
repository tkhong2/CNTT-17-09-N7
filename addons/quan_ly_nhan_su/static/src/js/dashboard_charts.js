/** @odoo-module **/

const TEAL  = '#00A09D';
const TEAL2 = 'rgba(0,160,157,0.75)';
const PIE_C = ['#00A09D','#28A745','#F0A500','#DC3545','#7e3af2','#0694a2','#c27803','#e3a008','#e02424','#057a55'];
const CDN   = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';

function loadChart() {
    if (window.Chart) return Promise.resolve();
    return new Promise((res, rej) => {
        const s = document.createElement('script');
        s.src = CDN;
        s.onload = res;
        s.onerror = () => {
            const s2 = document.createElement('script');
            s2.src = 'https://unpkg.com/chart.js@4.4.0/dist/chart.umd.min.js';
            s2.onload = res; s2.onerror = rej;
            document.head.appendChild(s2);
        };
        document.head.appendChild(s);
    });
}

function parseData(canvasId, sep) {
    const labelsEl = document.getElementById(canvasId + '_labels');
    const valuesEl = document.getElementById(canvasId + '_values');
    const rawL = labelsEl ? labelsEl.innerText.trim() : '';
    const rawV = valuesEl ? valuesEl.innerText.trim() : '';
    const labels = rawL ? rawL.split(sep).map(s => s.trim()).filter(Boolean) : [];
    const values = rawV ? rawV.split(',').map(Number).filter(n => !isNaN(n)) : [];
    return { labels, values };
}

function wrapInFixedDiv(canvas, height) {
    // Bọc canvas trong div có height cố định để responsive hoạt động đúng
    const parent = canvas.parentElement;
    if (parent && parent.dataset.chartWrapper) return; // đã wrap rồi
    const wrapper = document.createElement('div');
    wrapper.dataset.chartWrapper = '1';
    wrapper.style.cssText = `position:relative;width:100%;height:${height}px;`;
    parent.insertBefore(wrapper, canvas);
    wrapper.appendChild(canvas);
    canvas.style.cssText = 'display:block;';
}

function drawBar(canvas) {
    if (canvas._drawn) return;
    canvas._drawn = true;

    wrapInFixedDiv(canvas, 180);

    let { labels, values } = parseData(canvas.id, ',');
    if (!labels.length) { labels = ['Chưa có dữ liệu']; values = [0]; }

    const fmtLabels = labels.map(l => {
        const m = l.match(/^(\d{4})[-/](\d{1,2})$/);
        return m ? `T${parseInt(m[2])}/${m[1]}` : l;
    });

    if (canvas._chart) canvas._chart.destroy();
    canvas._chart = new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: fmtLabels,
            datasets: [{ label: 'Triệu VNĐ', data: values,
                backgroundColor: TEAL2, borderRadius: 5,
                borderSkipped: false, hoverBackgroundColor: TEAL }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: '#1C2B33', padding: 8, cornerRadius: 6,
                    callbacks: { label: c => ` ${c.parsed.y.toLocaleString('vi-VN')} triệu VNĐ` } }
            },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 }, color: '#6B7A85' } },
                y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' },
                    ticks: { font: { size: 10 }, color: '#6B7A85', callback: v => v + 'M' } }
            }
        }
    });
}

function drawPie(canvas) {
    if (canvas._drawn) return;
    canvas._drawn = true;

    wrapInFixedDiv(canvas, 280);

    let { labels, values } = parseData(canvas.id, '|');
    if (!labels.length) { labels = ['Chưa có phòng ban']; values = [1]; }

    if (canvas._chart) canvas._chart.destroy();
    canvas._chart = new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{ data: values,
                backgroundColor: PIE_C.slice(0, labels.length),
                borderWidth: 2, borderColor: '#fff', hoverOffset: 6 }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '58%',
            plugins: {
                legend: { position: 'bottom',
                    labels: { padding: 8, boxWidth: 10, font: { size: 10, weight: '600' },
                        color: '#374151', usePointStyle: true } },
                tooltip: { backgroundColor: '#1C2B33', padding: 8, cornerRadius: 6,
                    callbacks: { label: c => ` ${c.label}: ${c.parsed} nhân viên` } }
            }
        }
    });
}

let _timer = null;
function tryRender() {
    if (_timer) clearTimeout(_timer);
    _timer = setTimeout(async () => {
        const bar = document.getElementById('ns_bar_chart');
        const pie = document.getElementById('ns_pie_chart');
        if (!bar && !pie) return;
        try { await loadChart(); } catch(e) { console.warn('[Dashboard] Chart.js load lỗi:', e); return; }
        if (bar && !bar._drawn) drawBar(bar);
        if (pie && !pie._drawn) drawPie(pie);
    }, 600);
}

const obs = new MutationObserver(() => {
    if (document.getElementById('ns_bar_chart') || document.getElementById('ns_pie_chart'))
        tryRender();
});

function init() { obs.observe(document.body, { childList: true, subtree: true }); }
if (document.body) init();
else document.addEventListener('DOMContentLoaded', init);