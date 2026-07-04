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

    // 4. Initializing ApexCharts

    // Chart A: AUM Growth Chart
    const aumChartOptions = {
        series: [{
            name: 'AUM',
            data: [120000, 145000, 138000, 160000, 172000, 195000, 185000, 210000, 225000, 245678]
        }],
        chart: {
            type: 'area',
            height: 280,
            toolbar: { show: false },
            foreColor: '#94A3B8'
        },
        colors: ['#8B5CF6'],
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.45,
                opacityTo: 0.05,
                stops: [0, 95, 100]
            }
        },
        dataLabels: { enabled: false },
        stroke: {
            curve: 'smooth',
            width: 3
        },
        xaxis: {
            categories: ['Jul 2024', 'Aug 2024', 'Sep 2024', 'Oct 2024', 'Nov 2024', 'Dec 2024', 'Jan 2025', 'Feb 2025', 'Mar 2025', 'May 2025'],
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: {
            labels: {
                formatter: (value) => `₹ ${value / 1000}L Cr`
            }
        },
        grid: {
            borderColor: 'rgba(255, 255, 255, 0.05)',
            strokeDashArray: 4
        },
        tooltip: {
            theme: 'dark'
        }
    };
    const aumChart = new ApexCharts(document.querySelector("#aum-growth-chart"), aumChartOptions);
    aumChart.render();

    // Chart B: Category Donut Chart
    const donutOptions = {
        series: [65.4, 18.7, 10.2, 5.7],
        chart: {
            type: 'donut',
            height: 220,
            foreColor: '#94A3B8'
        },
        labels: ['Equity', 'Debt', 'Hybrid', 'Solution Oriented'],
        colors: ['#3B82F6', '#22C55E', '#F4B400', '#8B5CF6'],
        stroke: { show: false },
        legend: {
            position: 'bottom',
            fontSize: '11px',
            markers: { radius: 12 }
        },
        dataLabels: { enabled: false },
        plotOptions: {
            pie: {
                donut: {
                    size: '72%'
                }
            }
        },
        tooltip: {
            theme: 'dark'
        }
    };
    const donutChart = new ApexCharts(document.querySelector("#category-donut-chart"), donutOptions);
    donutChart.render();

    // Chart C: Sparkline Spark Charts
    const sparklineData = {
        nifty: [24100, 24350, 24200, 24500, 24700, 24650, 24834],
        sensex: [80100, 80500, 80300, 81000, 81400, 81200, 81721],
        bank: [53900, 54200, 54000, 54600, 54900, 54800, 55187],
        vix: [14.2, 13.8, 14.5, 13.2, 13.0, 12.8, 12.64]
    };

    const makeSparkline = (id, data, positive) => {
        const options = {
            series: [{ data }],
            chart: {
                type: 'line',
                width: 100,
                height: 36,
                sparkline: { enabled: true }
            },
            colors: [positive ? '#22C55E' : '#EF4444'],
            stroke: { width: 2, curve: 'smooth' },
            tooltip: { enabled: false }
        };
        new ApexCharts(document.querySelector(id), options).render();
    };

    makeSparkline("#nifty-sparkline", sparklineData.nifty, true);
    makeSparkline("#sensex-sparkline", sparklineData.sensex, true);
    makeSparkline("#bank-sparkline", sparklineData.bank, true);
    makeSparkline("#vix-sparkline", sparklineData.vix, false);

    // Chart D: Risk Gauge RadialBar
    const gaugeOptions = {
        series: [38],
        chart: {
            type: 'radialBar',
            height: 220,
            offsetY: -10
        },
        plotOptions: {
            radialBar: {
                startAngle: -135,
                endAngle: 135,
                dataLabels: {
                    name: {
                        fontSize: '13px',
                        color: '#94A3B8',
                        offsetY: 76
                    },
                    value: {
                        offsetY: 0,
                        fontSize: '28px',
                        color: '#fff',
                        fontWeight: 'bold',
                        formatter: (val) => `${val}`
                    }
                },
                track: {
                    background: 'rgba(255, 255, 255, 0.05)',
                    strokeWidth: '100%'
                }
            }
        },
        fill: {
            type: 'gradient',
            gradient: {
                shade: 'dark',
                type: 'horizontal',
                gradientToColors: ['#F4B400'],
                stops: [0, 100]
            }
        },
        colors: ['#22C55E'],
        labels: ['Moderate Risk']
    };
    const gaugeChart = new ApexCharts(document.querySelector("#risk-gauge-chart"), gaugeOptions);
    gaugeChart.render();

    // Chart E: SIP Contribution Trend
    const barOptions = {
        series: [{
            name: 'SIP Volume',
            data: [6500, 7200, 6800, 7900, 8400, 9200, 8900, 9700, 10500, 10200]
        }],
        chart: {
            type: 'bar',
            height: 240,
            toolbar: { show: false },
            foreColor: '#94A3B8'
        },
        colors: ['#3B82F6'],
        plotOptions: {
            bar: {
                borderRadius: 4,
                columnWidth: '50%'
            }
        },
        dataLabels: { enabled: false },
        xaxis: {
            categories: ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'],
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: {
            labels: {
                formatter: (val) => `₹ ${val} Cr`
            }
        },
        grid: {
            borderColor: 'rgba(255, 255, 255, 0.05)',
            strokeDashArray: 4
        },
        tooltip: {
            theme: 'dark'
        }
    };
    const barChart = new ApexCharts(document.querySelector("#sip-trend-chart"), barOptions);
    barChart.render();
});
