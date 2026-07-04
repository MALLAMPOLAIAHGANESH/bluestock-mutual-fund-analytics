// frontend/script.js

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Lucide Icons
    lucide.createIcons();

    // 2. Global Dark/Light Theme Switching
    const themeSwitch = document.getElementById('theme-switch');
    themeSwitch.addEventListener('change', () => {
        if (themeSwitch.checked) {
            document.body.classList.remove('light-mode');
            document.documentElement.style.setProperty('--bg-color', '#070B14');
            document.documentElement.style.setProperty('--surface-color', '#111827');
            document.documentElement.style.setProperty('--card-bg', 'rgba(255, 255, 255, 0.03)');
            document.documentElement.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.08)');
            document.documentElement.style.setProperty('--text-color', '#F8FAFC');
        } else {
            document.body.classList.add('light-mode');
            document.documentElement.style.setProperty('--bg-color', '#F1F5F9');
            document.documentElement.style.setProperty('--surface-color', '#FFFFFF');
            document.documentElement.style.setProperty('--card-bg', 'rgba(0, 0, 0, 0.02)');
            document.documentElement.style.setProperty('--border-color', 'rgba(0, 0, 0, 0.08)');
            document.documentElement.style.setProperty('--text-color', '#0F172A');
        }
    });

    // 3. Command Palette (Ctrl + K)
    const cmdOverlay = document.getElementById('cmd-palette-overlay');
    const cmdInput = document.getElementById('cmd-input');
    const searchBar = document.getElementById('global-search');

    const toggleCmdPalette = (show) => {
        if (show) {
            cmdOverlay.classList.add('open');
            cmdInput.focus();
        } else {
            cmdOverlay.classList.remove('open');
            cmdInput.value = '';
        }
    };

    window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            toggleCmdPalette(true);
        }
        if (e.key === 'Escape') {
            toggleCmdPalette(false);
        }
    });

    cmdOverlay.addEventListener('click', (e) => {
        if (e.target === cmdOverlay) {
            toggleCmdPalette(false);
        }
    });

    searchBar.addEventListener('click', () => {
        toggleCmdPalette(true);
    });

    // Card Mouse Move Tilt Effect
    const cards = document.querySelectorAll('.kpi-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
    });

    // =============================================
    // 4. SIDEBAR NAVIGATION — SPA page switching
    // =============================================
    const allMenuItems = document.querySelectorAll('.menu-item[data-page]');
    const allPages = document.querySelectorAll('.page-panel[data-page]');
    const renderedPages = new Set();

    window.navigateTo = function navigateTo(pageId) {
        // Hide all pages
        allPages.forEach(p => p.classList.remove('active'));
        // Remove active from all menu items
        allMenuItems.forEach(m => m.classList.remove('active'));
        // Show target page
        const targetPage = document.querySelector(`.page-panel[data-page="${pageId}"]`);
        if (targetPage) {
            targetPage.classList.add('active');
            // Re-init Lucide icons for the newly visible page
            lucide.createIcons();
        }
        // Mark matching menu items active
        allMenuItems.forEach(m => {
            if (m.dataset.page === pageId) m.classList.add('active');
        });
        // Scroll viewport to top
        const viewport = document.querySelector('.dashboard-viewport');
        if (viewport) viewport.scrollTop = 0;
        // Lazy-render charts for this page
        if (!renderedPages.has(pageId)) {
            renderedPages.add(pageId);
            renderChartsForPage(pageId);
        }
    }

    allMenuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = item.dataset.page;
            navigateTo(pageId);
        });
    });

    // Profile button → navigate to profile page
    const profileBtn = document.getElementById('profile-btn');
    if (profileBtn) {
        profileBtn.style.cursor = 'pointer';
        profileBtn.addEventListener('click', () => navigateTo('profile'));
    }

    // Also handle command palette navigation
    document.querySelectorAll('.cmd-item[data-url]').forEach(cmd => {
        cmd.addEventListener('click', () => {
            const pageId = cmd.dataset.url.replace('#', '');
            navigateTo(pageId);
            toggleCmdPalette(false);
        });
    });

    // =============================================
    // 5. CHART RENDERING (lazy per page)
    // =============================================
    const chartTheme = {
        foreColor: '#94A3B8',
        gridColor: 'rgba(255, 255, 255, 0.05)',
        tooltipTheme: 'dark'
    };

    function renderChartsForPage(pageId) {
        switch (pageId) {
            case 'overview':
                renderOverviewCharts();
                break;
            case 'dashboard':
                renderDashboardChart();
                break;
            case 'risk':
                renderDrawdownChart();
                break;
            case 'markowitz':
                renderFrontierChart();
                break;
            case 'montecarlo':
                renderMonteCarloChart();
                break;
            case 'report-sip':
                renderSipReportChart();
                break;
        }
    }

    // === OVERVIEW page charts ===
    function renderOverviewCharts() {
        // AUM Growth Chart
        new ApexCharts(document.querySelector("#aum-growth-chart"), {
            series: [{ name: 'AUM', data: [120000, 145000, 138000, 160000, 172000, 195000, 185000, 210000, 225000, 245678] }],
            chart: { type: 'area', height: 280, toolbar: { show: false }, foreColor: chartTheme.foreColor },
            colors: ['#8B5CF6'],
            fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.45, opacityTo: 0.05, stops: [0, 95, 100] } },
            dataLabels: { enabled: false },
            stroke: { curve: 'smooth', width: 3 },
            xaxis: { categories: ['Jul 2024','Aug 2024','Sep 2024','Oct 2024','Nov 2024','Dec 2024','Jan 2025','Feb 2025','Mar 2025','May 2025'], axisBorder:{show:false}, axisTicks:{show:false} },
            yaxis: { labels: { formatter: v => `₹ ${v/1000}L Cr` } },
            grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
            tooltip: { theme: chartTheme.tooltipTheme }
        }).render();

        // Category Donut
        new ApexCharts(document.querySelector("#category-donut-chart"), {
            series: [65.4, 18.7, 10.2, 5.7],
            chart: { type: 'donut', height: 220, foreColor: chartTheme.foreColor },
            labels: ['Equity','Debt','Hybrid','Solution Oriented'],
            colors: ['#3B82F6','#22C55E','#F4B400','#8B5CF6'],
            stroke: { show: false },
            legend: { position: 'bottom', fontSize: '11px', markers: { radius: 12 } },
            dataLabels: { enabled: false },
            plotOptions: { pie: { donut: { size: '72%' } } },
            tooltip: { theme: chartTheme.tooltipTheme }
        }).render();

        // Sparklines
        const sparkData = {
            nifty: [24100,24350,24200,24500,24700,24650,24834],
            sensex: [80100,80500,80300,81000,81400,81200,81721],
            bank: [53900,54200,54000,54600,54900,54800,55187],
            vix: [14.2,13.8,14.5,13.2,13.0,12.8,12.64]
        };
        const mkSpark = (id, data, pos) => {
            new ApexCharts(document.querySelector(id), {
                series: [{ data }], chart: { type: 'line', width: 100, height: 36, sparkline: { enabled: true } },
                colors: [pos ? '#22C55E' : '#EF4444'], stroke: { width: 2, curve: 'smooth' }, tooltip: { enabled: false }
            }).render();
        };
        mkSpark("#nifty-sparkline", sparkData.nifty, true);
        mkSpark("#sensex-sparkline", sparkData.sensex, true);
        mkSpark("#bank-sparkline", sparkData.bank, true);
        mkSpark("#vix-sparkline", sparkData.vix, false);

        // Risk Gauge
        new ApexCharts(document.querySelector("#risk-gauge-chart"), {
            series: [38], chart: { type: 'radialBar', height: 220, offsetY: -10 },
            plotOptions: { radialBar: { startAngle: -135, endAngle: 135, dataLabels: { name: { fontSize: '13px', color: '#94A3B8', offsetY: 76 }, value: { offsetY: 0, fontSize: '28px', color: '#fff', fontWeight: 'bold', formatter: v => `${v}` } }, track: { background: 'rgba(255,255,255,0.05)', strokeWidth: '100%' } } },
            fill: { type: 'gradient', gradient: { shade: 'dark', type: 'horizontal', gradientToColors: ['#F4B400'], stops: [0, 100] } },
            colors: ['#22C55E'], labels: ['Moderate Risk']
        }).render();

        // SIP Bar
        new ApexCharts(document.querySelector("#sip-trend-chart"), {
            series: [{ name: 'SIP Volume', data: [6500,7200,6800,7900,8400,9200,8900,9700,10500,10200] }],
            chart: { type: 'bar', height: 240, toolbar: { show: false }, foreColor: chartTheme.foreColor },
            colors: ['#3B82F6'],
            plotOptions: { bar: { borderRadius: 4, columnWidth: '50%' } },
            dataLabels: { enabled: false },
            xaxis: { categories: ['Jul','Aug','Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr'], axisBorder:{show:false}, axisTicks:{show:false} },
            yaxis: { labels: { formatter: v => `₹ ${v} Cr` } },
            grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
            tooltip: { theme: chartTheme.tooltipTheme }
        }).render();
    }

    // === DASHBOARD page chart ===
    function renderDashboardChart() {
        const el = document.querySelector("#dashboard-perf-chart");
        if (!el) return;
        new ApexCharts(el, {
            series: [
                { name: 'Quant Flexi Cap', data: [12,18,14,22,28,26,32,28,35] },
                { name: 'Parag Parikh', data: [10,14,12,16,20,22,24,22,25] },
                { name: 'Mirae Large Cap', data: [8,12,10,14,18,16,20,19,22] }
            ],
            chart: { type: 'line', height: 260, toolbar: { show: false }, foreColor: chartTheme.foreColor },
            colors: ['#3B82F6','#22C55E','#8B5CF6'],
            stroke: { curve: 'smooth', width: 2.5 },
            dataLabels: { enabled: false },
            xaxis: { categories: ['Sep 24','Oct 24','Nov 24','Dec 24','Jan 25','Feb 25','Mar 25','Apr 25','May 25'] },
            grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
            tooltip: { theme: chartTheme.tooltipTheme },
            legend: { position: 'top' }
        }).render();
    }

    // === RISK page drawdown ===
    function renderDrawdownChart() {
        const el = document.querySelector("#drawdown-chart");
        if (!el) return;
        new ApexCharts(el, {
            series: [{ name: 'Drawdown', data: [0,-2.1,-5.4,-8.2,-12.6,-18.6,-14.2,-9.8,-6.1,-3.4,-1.2,0] }],
            chart: { type: 'area', height: 260, toolbar: { show: false }, foreColor: chartTheme.foreColor },
            colors: ['#EF4444'],
            fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05 } },
            stroke: { curve: 'smooth', width: 2.5 },
            dataLabels: { enabled: false },
            xaxis: { categories: ['Jun 24','Jul 24','Aug 24','Sep 24','Oct 24','Nov 24','Dec 24','Jan 25','Feb 25','Mar 25','Apr 25','May 25'] },
            yaxis: { labels: { formatter: v => `${v}%` } },
            grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
            tooltip: { theme: chartTheme.tooltipTheme }
        }).render();
    }

    // === MARKOWITZ efficient frontier ===
    function renderFrontierChart() {
        const el = document.querySelector("#frontier-chart");
        if (!el) return;
        // Generate scatter data for the frontier curve
        const frontierPts = [];
        for (let i = 0; i <= 20; i++) {
            const risk = 5 + i * 1.2;
            const ret = 6 + Math.sqrt(i) * 4.2 - (i > 15 ? (i-15)*0.8 : 0);
            frontierPts.push([parseFloat(risk.toFixed(1)), parseFloat(ret.toFixed(1))]);
        }
        const randomPts = Array.from({length: 40}, () => [
            parseFloat((6 + Math.random() * 22).toFixed(1)),
            parseFloat((4 + Math.random() * 18).toFixed(1))
        ]);
        new ApexCharts(el, {
            series: [
                { name: 'Efficient Frontier', data: frontierPts },
                { name: 'Individual Funds', data: randomPts }
            ],
            chart: { type: 'scatter', height: 300, toolbar: { show: false }, foreColor: chartTheme.foreColor },
            colors: ['#3B82F6', 'rgba(139,92,246,0.5)'],
            xaxis: { title: { text: 'Risk (σ %)', style: { color: '#94A3B8' } }, tickAmount: 8 },
            yaxis: { title: { text: 'Return (%)', style: { color: '#94A3B8' } } },
            markers: { size: [5, 4] },
            grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
            tooltip: { theme: chartTheme.tooltipTheme },
            legend: { position: 'top' }
        }).render();
    }

    // === MONTE CARLO simulation ===
    function renderMonteCarloChart() {
        const el = document.querySelector("#montecarlo-chart");
        if (!el) return;
        const months = Array.from({length: 61}, (_, i) => `M${i}`);
        // Generate 3 percentile paths
        const p90 = [100]; const p50 = [100]; const p10 = [100];
        for (let i = 1; i <= 60; i++) {
            p90.push(parseFloat((p90[i-1] * (1 + 0.015 + Math.random() * 0.008)).toFixed(2)));
            p50.push(parseFloat((p50[i-1] * (1 + 0.008 + Math.random() * 0.005)).toFixed(2)));
            p10.push(parseFloat((p10[i-1] * (1 + 0.001 + (Math.random()-0.5) * 0.008)).toFixed(2)));
        }
        new ApexCharts(el, {
            series: [
                { name: '90th Percentile', data: p90 },
                { name: '50th Percentile (Median)', data: p50 },
                { name: '10th Percentile', data: p10 }
            ],
            chart: { type: 'line', height: 300, toolbar: { show: false }, foreColor: chartTheme.foreColor },
            colors: ['#22C55E', '#3B82F6', '#EF4444'],
            stroke: { curve: 'smooth', width: 2, dashArray: [0, 5, 3] },
            dataLabels: { enabled: false },
            xaxis: { categories: months, tickAmount: 12, labels: { show: true, rotate: 0 } },
            yaxis: { title: { text: 'NAV (₹)', style: { color: '#94A3B8' } } },
            grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
            tooltip: { theme: chartTheme.tooltipTheme },
            legend: { position: 'top' }
        }).render();
    }

    // === SIP Report chart ===
    function renderSipReportChart() {
        const el = document.querySelector("#sip-report-chart");
        if (!el) return;
        new ApexCharts(el, {
            series: [{ name: 'SIP Inflows', data: [14500,15200,16100,17800,18400,19200,20100,20800,21500] }],
            chart: { type: 'bar', height: 260, toolbar: { show: false }, foreColor: chartTheme.foreColor },
            colors: ['#22C55E'],
            plotOptions: { bar: { borderRadius: 6, columnWidth: '45%' } },
            dataLabels: { enabled: false },
            xaxis: { categories: ['Sep 24','Oct 24','Nov 24','Dec 24','Jan 25','Feb 25','Mar 25','Apr 25','May 25'] },
            yaxis: { labels: { formatter: v => `₹ ${v} Cr` } },
            grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
            tooltip: { theme: chartTheme.tooltipTheme }
        }).render();
    }

    // =============================================
    // 6. INITIAL RENDER — Overview page
    // =============================================
    renderedPages.add('overview');
    renderOverviewCharts();
});
