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
                renderRiskPageCharts();
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
            chart: { type: 'area', height: 300, toolbar: { show: false }, foreColor: chartTheme.foreColor },
            colors: ['#8B5CF6'],
            fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.45, opacityTo: 0.05, stops: [0, 95, 100] } },
            dataLabels: { enabled: false },
            stroke: { curve: 'smooth', width: 3 },
            xaxis: { categories: ['Jul 2024','Aug 2024','Sep 2024','Oct 2024','Nov 2024','Dec 2024','Jan 2025','Feb 2025','Mar 2025','May 2025'], axisBorder:{show:false}, axisTicks:{show:false} },
            yaxis: { labels: { formatter: v => `₹ ${v/1000}L Cr` } },
            grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
            tooltip: { theme: chartTheme.tooltipTheme }
        }).render();

        // Fund Distribution Donut
        new ApexCharts(document.querySelector("#fund-dist-donut"), {
            series: [40, 25, 15, 12, 8],
            chart: { type: 'donut', height: 220, foreColor: chartTheme.foreColor },
            labels: ['Flexi Cap','Large Cap','Mid Cap','Small Cap','Hybrid'],
            colors: ['#3B82F6','#22C55E','#F4B400','#8B5CF6','#EF4444'],
            stroke: { show: false },
            legend: { position: 'bottom', fontSize: '11px', markers: { radius: 12 } },
            dataLabels: { enabled: false },
            plotOptions: { pie: { donut: { size: '72%' } } },
            tooltip: { theme: chartTheme.tooltipTheme }
        }).render();

        // Portfolio Allocation Donut
        new ApexCharts(document.querySelector("#portfolio-alloc-donut"), {
            series: [65, 20, 10, 5],
            chart: { type: 'donut', height: 220, foreColor: chartTheme.foreColor },
            labels: ['Equity','Debt','Gold','Cash'],
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
            largecap: [17800,18100,18000,18250,18400,18300,18450],
            midcap: [21100,21500,21300,21800,22050,21900,22120],
            smallcap: [16100,15900,15800,15700,15750,15600,15640]
        };
        const mkSpark = (id, data, pos) => {
            new ApexCharts(document.querySelector(id), {
                series: [{ data }], chart: { type: 'line', width: 100, height: 36, sparkline: { enabled: true } },
                colors: [pos ? '#22C55E' : '#EF4444'], stroke: { width: 2, curve: 'smooth' }, tooltip: { enabled: false }
            }).render();
        };
        mkSpark("#nifty-sparkline", sparkData.nifty, true);
        mkSpark("#sensex-sparkline", sparkData.sensex, true);
        mkSpark("#largecap-sparkline", sparkData.largecap, true);
        mkSpark("#midcap-sparkline", sparkData.midcap, true);
        mkSpark("#smallcap-sparkline", sparkData.smallcap, false);

        // Risk Gauge
        new ApexCharts(document.querySelector("#risk-gauge-chart"), {
            series: [38], chart: { type: 'radialBar', height: 220, offsetY: -10 },
            plotOptions: { radialBar: { startAngle: -135, endAngle: 135, dataLabels: { name: { fontSize: '13px', color: '#94A3B8', offsetY: 76 }, value: { offsetY: 0, fontSize: '28px', color: '#fff', fontWeight: 'bold', formatter: v => `${v}` } }, track: { background: 'rgba(255,255,255,0.05)', strokeWidth: '100%' } } },
            fill: { type: 'gradient', gradient: { shade: 'dark', type: 'horizontal', gradientToColors: ['#F4B400'], stops: [0, 100] } },
            colors: ['#22C55E'], labels: ['Moderate Risk']
        }).render();
    }

    // === DASHBOARD page chart ===
    function renderDashboardChart() {
        const el = document.querySelector("#dashboard-perf-chart");
        if (!el) return;
        new ApexCharts(el, {
            series: [
                { name: 'Quant Flexi Cap (NAV)', data: [120,135,130,145,152,150,158,154,162] },
                { name: 'Parag Parikh Flexi (NAV)', data: [110,122,118,128,135,132,140,136,144] },
                { name: 'Mirae Large Cap (NAV)', data: [100,108,105,114,120,118,124,122,128] }
            ],
            chart: { type: 'line', height: 280, toolbar: { show: false }, foreColor: chartTheme.foreColor },
            colors: ['#3B82F6','#22C55E','#8B5CF6'],
            stroke: { curve: 'smooth', width: 2.5 },
            dataLabels: { enabled: false },
            xaxis: { categories: ['Sep 24','Oct 24','Nov 24','Dec 24','Jan 25','Feb 25','Mar 25','Apr 25','May 25'] },
            grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
            tooltip: { theme: chartTheme.tooltipTheme },
            legend: { position: 'top' }
        }).render();

        // Drawdown Timeline chart for Dashboard
        const ddEl = document.querySelector("#dashboard-drawdown-chart");
        if (ddEl) {
            new ApexCharts(ddEl, {
                series: [{ name: 'Drawdown', data: [0,-2.1,-5.4,-8.2,-12.6,-18.6,-14.2,-9.8,-6.1,-3.4,-1.2,0] }],
                chart: { type: 'area', height: 250, toolbar: { show: false }, foreColor: chartTheme.foreColor },
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

        // Scatter plot (Risk vs Return) for Dashboard
        const scatEl = document.querySelector("#dashboard-scatter-chart");
        if (scatEl) {
            new ApexCharts(scatEl, {
                series: [
                    { name: 'High Return / High Risk', data: [[18.2, 28.3], [22.8, 31.2]] },
                    { name: 'Moderate Return / Mod Risk', data: [[12.4, 24.6], [14.1, 22.4]] },
                    { name: 'Stable Return / Low Risk', data: [[10.2, 16.7], [11.4, 19.5]] }
                ],
                chart: { type: 'scatter', height: 180, toolbar: { show: false }, foreColor: chartTheme.foreColor },
                colors: ['#EF4444', '#3B82F6', '#22C55E'],
                xaxis: { title: { text: 'Risk (σ)', style: { color: '#94A3B8', fontSize: '10px' } } },
                yaxis: { title: { text: 'Return (%)', style: { color: '#94A3B8', fontSize: '10px' } } },
                grid: { borderColor: chartTheme.gridColor },
                tooltip: { theme: chartTheme.tooltipTheme }
            }).render();
        }
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

    // === RISK page charts ===
    function renderRiskPageCharts() {
        // 4. Risk vs Return Scatter
        const scatEl = document.querySelector("#risk-scatter-chart");
        if (scatEl) {
            new ApexCharts(scatEl, {
                series: [
                    { name: 'Equity Funds', data: [[18.2, 28.3, 18], [22.8, 31.2, 11], [12.4, 24.6, 45]] },
                    { name: 'Hybrid Funds', data: [[10.2, 16.7, 15]] },
                    { name: 'Debt Funds', data: [[3.5, 7.4, 8]] }
                ],
                chart: { type: 'bubble', height: 250, toolbar: { show: false }, foreColor: chartTheme.foreColor },
                colors: ['#3B82F6', '#F4B400', '#22C55E'],
                xaxis: { title: { text: 'Risk (Volatility %)', style: { color: '#94A3B8' } }, tickAmount: 6 },
                yaxis: { title: { text: 'Return (%)', style: { color: '#94A3B8' } } },
                grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
                tooltip: { theme: chartTheme.tooltipTheme }
            }).render();
        }

        // 5. Volatility / Returns Distribution
        const distEl = document.querySelector("#vol-distribution-chart");
        if (distEl) {
            new ApexCharts(distEl, {
                series: [{ name: 'Return Frequency', data: [1, 2, 5, 12, 25, 40, 28, 14, 6, 2, 1] }],
                chart: { type: 'area', height: 220, toolbar: { show: false }, foreColor: chartTheme.foreColor },
                colors: ['#8B5CF6'],
                stroke: { curve: 'smooth', width: 2 },
                xaxis: { categories: ['-5%','-3%','-1%','0%','1%','2%','3%','4%','5%','6%','7%'] },
                grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
                tooltip: { theme: chartTheme.tooltipTheme }
            }).render();
        }

        // 6. Drawdown Timeline
        const ddEl = document.querySelector("#drawdown-timeline-chart");
        if (ddEl) {
            new ApexCharts(ddEl, {
                series: [{ name: 'Drawdown', data: [0,-1.5,-4.2,-6.8,-11.4,-18.6,-15.4,-11.2,-7.5,-4.1,-1.8,0] }],
                chart: { type: 'area', height: 220, toolbar: { show: false }, foreColor: chartTheme.foreColor },
                colors: ['#EF4444'],
                fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05 } },
                stroke: { curve: 'smooth', width: 2 },
                xaxis: { categories: ['Jun 24','Jul 24','Aug 24','Sep 24','Oct 24','Nov 24','Dec 24','Jan 25','Feb 25','Mar 25','Apr 25','May 25'] },
                grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
                tooltip: { theme: chartTheme.tooltipTheme }
            }).render();
        }
    }

    // === Navigation to Fund Details (Explorer Page) ===
    let explorerChartInstance = null;
    window.navigateToDetails = function(fundName) {
        const panel = document.getElementById('fund-details-panel');
        if (!panel) return;
        panel.style.display = 'flex';

        // Update Text Fields dynamically
        document.getElementById('detail-fund-title').textContent = fundName;
        const subtitle = document.getElementById('detail-fund-subtitle');
        const mngr = document.getElementById('det-manager');
        const exp = document.getElementById('det-expense');
        const bnch = document.getElementById('det-bench');

        let dataPoints = [];
        if (fundName.includes('Quant')) {
            subtitle.textContent = "Quant Mutual Fund | Equity - Flexi Cap";
            mngr.textContent = "Sandeep Tandon";
            exp.textContent = "0.72%";
            bnch.textContent = "NIFTY 500 TRI";
            dataPoints = [100, 115, 110, 125, 138, 134, 148, 142, 162.45];
        } else if (fundName.includes('Parag')) {
            subtitle.textContent = "Parag Parikh Mutual Fund | Equity - Flexi Cap";
            mngr.textContent = "Rajeev Thakkar";
            exp.textContent = "0.65%";
            bnch.textContent = "NIFTY 500 TRI";
            dataPoints = [100, 108, 105, 114, 122, 120, 128, 125, 144.20];
        } else {
            subtitle.textContent = "Mirae Asset Mutual Fund | Equity - Large Cap";
            mngr.textContent = "Harshad Borawake";
            exp.textContent = "0.82%";
            bnch.textContent = "NIFTY 100 TRI";
            dataPoints = [100, 105, 103, 110, 115, 112, 120, 118, 128.85];
        }

        // Render Fund Specific Growth Chart
        if (explorerChartInstance) {
            explorerChartInstance.destroy();
        }
        explorerChartInstance = new ApexCharts(document.querySelector("#explorer-growth-chart"), {
            series: [{ name: 'NAV', data: dataPoints }],
            chart: { type: 'area', height: 220, toolbar: { show: false }, foreColor: chartTheme.foreColor },
            colors: ['#3B82F6'],
            stroke: { curve: 'smooth', width: 2 },
            fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.3, opacityTo: 0.05 } },
            xaxis: { categories: ['Sep 24','Oct 24','Nov 24','Dec 24','Jan 25','Feb 25','Mar 25','Apr 25','May 25'] },
            grid: { borderColor: chartTheme.gridColor, strokeDashArray: 4 },
            tooltip: { theme: chartTheme.tooltipTheme }
        });
        explorerChartInstance.render();

        // Scroll to the detail section
        panel.scrollIntoView({ behavior: 'smooth' });
    };

    // =============================================
    // 6. INITIAL RENDER — Overview page
    // =============================================
    renderedPages.add('overview');
    renderOverviewCharts();
});
