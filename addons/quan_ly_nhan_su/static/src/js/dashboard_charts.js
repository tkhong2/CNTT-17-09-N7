/** @odoo-module **/
const CDN   = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
const TEAL  = '#00A09D';
const TEAL2 = 'rgba(0,160,157,0.75)';
const PIE_C = ['#00A09D','#28A745','#F0A500','#DC3545','#7e3af2','#0694a2','#c27803'];

async function loadChart() {
    if (window.Chart) return;
    await new Promise((res, rej) => {
        const s = document.createElement('script');
        s.src = CDN; s.onload = res; s.onerror = rej;
        document.head.appendChild(s);
    });
}

function parseCanvas(canvas, sep) {
    // Đọc data từ hidden span thay vì data-attribute (t-att không hoạt động trong form view)
    const labelsEl = document.getElementById(canvas.id + '_labels');
    const valuesEl = document.getElementById(canvas.id + '_values');
    const rawLabels = labelsEl ? labelsEl.innerText.trim() : (canvas.getAttribute('data-labels') || '');
    const rawValues = valuesEl ? valuesEl.innerText.trim() : (canvas.getAttribute('data-values') || '');
    const labels = rawLabels.split(sep).map(s=>s.trim()).filter(Boolean);
    const values = rawValues.split(',').map(Number).filter(n=>!isNaN(n));
    return { labels, values };
}

function drawBar(canvas) {
    if (canvas._drawn) return;
    canvas._drawn = true;
    canvas.style.cssText = 'width:100%!important;height:190px!important;display:block;';

    let { labels, values } = parseCanvas(canvas, ',');
    if (!labels.length) { labels = ['Chưa có dữ liệu']; values = [0]; }

    const fmtLabels = labels.map(l => {
        const m = l.match(/^(\d{4})-(\d{2})$/);
        return m ? `T${parseInt(m[2])}/${m[1]}` : l;
    });

    new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: fmtLabels,
            datasets: [{ label: 'Triệu VNĐ', data: values,
                backgroundColor: TEAL2, borderRadius: 6,
                borderSkipped: false, hoverBackgroundColor: TEAL }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: '#1C2B33', padding: 10, cornerRadius: 8,
                    callbacks: { label: c => `  ${c.parsed.y.toLocaleString('vi-VN')} triệu VNĐ` } }
            },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 11 }, color: '#6B7A85' } },
                y: { beginAtZero: true,
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    ticks: { font: { size: 11 }, color: '#6B7A85', callback: v => v + 'M' } }
            }
        }
    });
}

function drawPie(canvas) {
    if (canvas._drawn) return;
    canvas._drawn = true;
    canvas.style.cssText = 'width:100%!important;height:210px!important;display:block;';

    let { labels, values } = parseCanvas(canvas, '|');
    if (!labels.length) { labels = ['Chưa có phòng ban']; values = [1]; }

    new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{ data: values,
                backgroundColor: PIE_C.slice(0, labels.length),
                borderWidth: 2, borderColor: '#fff', hoverOffset: 8 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '62%',
            plugins: {
                legend: { position: 'bottom',
                    labels: { padding: 10, boxWidth: 10, font: { size: 11, weight: '600' },
                        color: '#374151', usePointStyle: true } },
                tooltip: { backgroundColor: '#1C2B33', padding: 10, cornerRadius: 8,
                    callbacks: { label: c => `  ${c.label}: ${c.parsed} nhân viên` } }
            }
        }
    });
}

function tryRender() {
    const bar = document.getElementById('ns_bar_chart');
    const pie = document.getElementById('ns_pie_chart');
    if (!bar && !pie) return;
    loadChart().then(() => {
        if (bar && !bar._drawn) drawBar(bar);
        if (pie && !pie._drawn) drawPie(pie);
    }).catch(e => console.warn('[Chart] load error:', e));
}

const obs = new MutationObserver(() => {
    if (document.getElementById('ns_bar_chart') || document.getElementById('ns_pie_chart'))
        setTimeout(tryRender, 300);
});

if (document.body) obs.observe(document.body, { childList: true, subtree: true });
else document.addEventListener('DOMContentLoaded', () => obs.observe(document.body, { childList: true, subtree: true }));
