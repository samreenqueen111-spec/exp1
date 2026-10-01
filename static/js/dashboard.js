// CareBridge Frontend JavaScript - Premium Interactive Charts, Sliders, Theme Switcher & UI

document.addEventListener('DOMContentLoaded', function() {
    initThemeToggle();
    initSliders();
    initSurvivorTrendCharts();
    initCounselorDistributionChart();
    initCounselorRealtimeAlerts();
});

// 1. Dark / Light Mode Theme Switcher
function initThemeToggle() {
    const toggleBtn = document.getElementById('themeToggle');
    if (!toggleBtn) return;

    // Check initial state
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    updateToggleButton(toggleBtn, currentTheme);

    toggleBtn.addEventListener('click', function() {
        const activeTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = activeTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('carebridge_theme', newTheme);
        updateToggleButton(toggleBtn, newTheme);

        // Re-render charts on theme change to update colors/grid lines if charts exist
        if (window.survivorChartInstance) {
            window.survivorChartInstance.destroy();
            initSurvivorTrendCharts();
        }
        if (window.counselorChartInstance) {
            window.counselorChartInstance.destroy();
            initCounselorDistributionChart();
        }
    });
}

function updateToggleButton(btn, theme) {
    if (theme === 'dark') {
        btn.innerHTML = '☀️ Light Mode';
    } else {
        btn.innerHTML = '🌙 Dark Mode';
    }
}

// 2. Interactive Sliders setup with smooth value output
function initSliders() {
    const sliders = document.querySelectorAll('input[type=range]');
    sliders.forEach(slider => {
        const outputId = slider.getAttribute('data-output');
        if (outputId) {
            const outputElem = document.getElementById(outputId);
            if (outputElem) {
                slider.addEventListener('input', function() {
                    outputElem.textContent = this.value;
                });
            }
        }
    });
}

// 3. Survivor Well-being Trends Charts using Chart.js with Soft Gradients
function initSurvivorTrendCharts() {
    const trendCanvas = document.getElementById('survivorTrendChart');
    if (!trendCanvas) return;

    fetch('/api/survivor/trends')
        .then(response => response.json())
        .then(data => {
            if (!data.labels || data.labels.length === 0) {
                const parent = trendCanvas.parentElement;
                parent.innerHTML = '<div class="alert alert-info" style="text-align:center;">🌱 No check-in reflections available yet. Complete your first daily check-in to see your personalized trend visualization!</div>';
                return;
            }

            const ctx = trendCanvas.getContext('2d');
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(99, 102, 241, 0.08)';
            const textColor = isDark ? '#94a3b8' : '#64748b';

            // Linear gradients for dataset fills
            const stressGradient = ctx.createLinearGradient(0, 0, 0, 320);
            stressGradient.addColorStop(0, isDark ? 'rgba(244, 63, 94, 0.35)' : 'rgba(244, 63, 94, 0.22)');
            stressGradient.addColorStop(1, 'rgba(244, 63, 94, 0.0)');

            const sleepGradient = ctx.createLinearGradient(0, 0, 0, 320);
            sleepGradient.addColorStop(0, isDark ? 'rgba(99, 102, 241, 0.4)' : 'rgba(99, 102, 241, 0.22)');
            sleepGradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

            const supportGradient = ctx.createLinearGradient(0, 0, 0, 320);
            supportGradient.addColorStop(0, isDark ? 'rgba(16, 185, 129, 0.35)' : 'rgba(16, 185, 129, 0.2)');
            supportGradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

            window.survivorChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: '⚡ Stress Level',
                            data: data.stress,
                            borderColor: '#f43f5e',
                            backgroundColor: stressGradient,
                            borderWidth: 3,
                            pointBackgroundColor: '#ffffff',
                            pointBorderColor: '#f43f5e',
                            pointBorderWidth: 2.5,
                            pointRadius: 4.5,
                            pointHoverRadius: 7,
                            tension: 0.38,
                            fill: true
                        },
                        {
                            label: '🌙 Sleep Rest',
                            data: data.sleep,
                            borderColor: '#6366f1',
                            backgroundColor: sleepGradient,
                            borderWidth: 3,
                            pointBackgroundColor: '#ffffff',
                            pointBorderColor: '#6366f1',
                            pointBorderWidth: 2.5,
                            pointRadius: 4.5,
                            pointHoverRadius: 7,
                            tension: 0.38,
                            fill: true
                        },
                        {
                            label: '🤝 Felt Support',
                            data: data.support,
                            borderColor: '#10b981',
                            backgroundColor: supportGradient,
                            borderWidth: 3,
                            pointBackgroundColor: '#ffffff',
                            pointBorderColor: '#10b981',
                            pointBorderWidth: 2.5,
                            pointRadius: 4.5,
                            pointHoverRadius: 7,
                            tension: 0.38,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    scales: {
                        y: {
                            min: 1,
                            max: 10,
                            ticks: {
                                stepSize: 2,
                                color: textColor,
                                font: {
                                    family: "'Plus Jakarta Sans', sans-serif",
                                    weight: 600
                                }
                            },
                            grid: {
                                color: gridColor
                            },
                            title: {
                                display: true,
                                text: 'Score Rating (1 - 10)',
                                color: textColor,
                                font: {
                                    family: "'Plus Jakarta Sans', sans-serif",
                                    weight: 700,
                                    size: 12
                                }
                            }
                        },
                        x: {
                            ticks: {
                                color: textColor,
                                font: {
                                    family: "'Plus Jakarta Sans', sans-serif",
                                    weight: 600
                                }
                            },
                            grid: {
                                color: gridColor
                            },
                            title: {
                                display: true,
                                text: 'Check-in Date & Time',
                                color: textColor,
                                font: {
                                    family: "'Plus Jakarta Sans', sans-serif",
                                    weight: 700,
                                    size: 12
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: isDark ? '#f1f5f9' : '#1e1b4b',
                                font: {
                                    family: "'Plus Jakarta Sans', sans-serif",
                                    weight: 700,
                                    size: 13
                                },
                                usePointStyle: true,
                                padding: 20
                            }
                        },
                        tooltip: {
                            backgroundColor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(30, 27, 75, 0.92)',
                            titleFont: { family: "'Plus Jakarta Sans', sans-serif", weight: 'bold', size: 13 },
                            bodyFont: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
                            padding: 12,
                            cornerRadius: 12,
                            boxPadding: 6,
                            callbacks: {
                                afterBody: function(context) {
                                    const index = context[0].dataIndex;
                                    return `Distress Indicator: ${data.indicators[index]}`;
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(err => console.error("Error fetching survivor trend data:", err));
}

// 4. Counselor Distress Indicator Distribution Chart
function initCounselorDistributionChart() {
    const distCanvas = document.getElementById('distressDistributionChart');
    if (!distCanvas) return;

    fetch('/api/counselor/distress_distribution')
        .then(response => response.json())
        .then(data => {
            const ctx = distCanvas.getContext('2d');
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

            window.counselorChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Low Indicator', 'Moderate Indicator', 'High Indicator'],
                    datasets: [{
                        data: [data.Low || 0, data.Moderate || 0, data.High || 0],
                        backgroundColor: ['#10b981', '#f59e0b', '#f43f5e'],
                        borderColor: isDark ? '#0c0f1d' : '#ffffff',
                        borderWidth: 3,
                        hoverOffset: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '72%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: isDark ? '#e2e8f0' : '#334155',
                                font: {
                                    family: "'Plus Jakarta Sans', sans-serif",
                                    weight: 600,
                                    size: 12
                                },
                                usePointStyle: true,
                                padding: 15
                            }
                        },
                        tooltip: {
                            backgroundColor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(30, 27, 75, 0.92)',
                            titleFont: { family: "'Plus Jakarta Sans', sans-serif", weight: 'bold' },
                            bodyFont: { family: "'Plus Jakarta Sans', sans-serif" },
                            padding: 10,
                            cornerRadius: 10
                        }
                    }
                }
            });
        })
        .catch(err => console.error("Error loading counselor distribution chart:", err));
}

// 5. Counselor Real-Time High-Distress Alert System (Polling & Dynamic DOM Updates)
function initCounselorRealtimeAlerts() {
    const modal = document.getElementById('liveAlertModal');
    const backdrop = document.getElementById('liveAlertBackdrop');
    if (!modal) return; // Only runs on pages with the alert modal (e.g. counselor dashboard)

    const survivorIdEl = document.getElementById('liveAlertSurvivorId');
    const riskBadgeEl = document.getElementById('liveAlertRiskBadge');
    const timeEl = document.getElementById('liveAlertTime');
    const messageEl = document.getElementById('liveAlertMessage');
    const dismissBtn = document.getElementById('liveAlertDismissBtn');
    const reviewBtn = document.getElementById('liveAlertReviewBtn');

    // Stat metric elements
    const statPendingAlerts = document.getElementById('statPendingAlertsCount');
    const statHighDistress = document.getElementById('statHighDistressCount');
    const statRecentCheckins = document.getElementById('statRecentCheckins');
    const statTotalSurvivors = document.getElementById('statTotalSurvivors');
    const headerPendingAlerts = document.getElementById('headerPendingAlertsCount');
    const alertsContainer = document.getElementById('counselorAlertsContainer');

    let currentAlertId = null;
    let dismissedAlertIds = new Set(
        JSON.parse(sessionStorage.getItem('carebridge_dismissed_alerts') || '[]')
    );

    function showModal(alertData) {
        currentAlertId = alertData.id;
        if (survivorIdEl) survivorIdEl.textContent = alertData.anonymous_id;
        if (riskBadgeEl) riskBadgeEl.textContent = alertData.indicator || 'High';
        if (timeEl) timeEl.textContent = alertData.created_at || 'Just now';
        if (messageEl) {
            messageEl.textContent = alertData.message || 
                'High Distress Alert: A survivor’s recent responses indicate elevated distress. Please review and consider follow-up.';
        }

        modal.classList.add('show');
        if (backdrop) backdrop.classList.add('show');
    }

    function hideModal() {
        modal.classList.remove('show');
        if (backdrop) backdrop.classList.remove('show');
    }

    // Dismiss Button handler
    if (dismissBtn) {
        dismissBtn.addEventListener('click', function() {
            if (!currentAlertId) {
                hideModal();
                return;
            }
            const alertIdToDismiss = currentAlertId;
            dismissedAlertIds.add(alertIdToDismiss);
            sessionStorage.setItem('carebridge_dismissed_alerts', JSON.stringify([...dismissedAlertIds]));
            hideModal();

            fetch('/api/counselor/dismiss_alert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ alert_id: alertIdToDismiss })
            })
            .then(res => res.json())
            .then(() => pollAlerts())
            .catch(err => console.error("Error dismissing alert:", err));
        });
    }

    // Review Button handler
    if (reviewBtn) {
        reviewBtn.addEventListener('click', function() {
            if (!currentAlertId) {
                window.location.href = '/counselor/alerts';
                return;
            }
            const alertIdToReview = currentAlertId;
            dismissedAlertIds.add(alertIdToReview);
            sessionStorage.setItem('carebridge_dismissed_alerts', JSON.stringify([...dismissedAlertIds]));
            hideModal();

            fetch('/api/counselor/review_alert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ alert_id: alertIdToReview })
            })
            .then(() => {
                window.location.href = '/counselor/alerts';
            })
            .catch(() => {
                window.location.href = '/counselor/alerts';
            });
        });
    }

    // Backdrop click dismisses modal gently
    if (backdrop) {
        backdrop.addEventListener('click', hideModal);
    }

    // Update alerts table preview dynamically without reloading page
    function updateRecentAlertsTable(recentAlerts) {
        if (!alertsContainer) return;

        if (!recentAlerts || recentAlerts.length === 0) {
            alertsContainer.innerHTML = `
                <div id="counselorEmptyAlerts" style="text-align: center; padding: 2rem 0; color: var(--text-muted);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">✨</div>
                    <p style="font-size: 0.95rem;">All participants are currently reporting manageable wellness scores. No urgent follow-ups pending.</p>
                </div>
            `;
            return;
        }

        let rowsHtml = '';
        recentAlerts.slice(0, 4).forEach(a => {
            const indClass = (a.indicator || 'low').toLowerCase();
            const statusClass = (a.status || 'pending').toLowerCase().replace(' ', '-');
            rowsHtml += `
                <tr>
                    <td><code>${escapeHtml(a.anonymous_id)}</code></td>
                    <td><span class="badge badge-${indClass}">${escapeHtml(a.indicator)}</span></td>
                    <td>${escapeHtml(a.reason)}</td>
                    <td><span class="badge badge-${statusClass}">${escapeHtml(a.status)}</span></td>
                    <td>${escapeHtml(a.created_at)}</td>
                </tr>
            `;
        });

        alertsContainer.innerHTML = `
            <div class="table-responsive">
                <table class="table" style="font-size: 0.88rem;">
                    <thead>
                        <tr>
                            <th>Participant ID</th>
                            <th>Care Indicator</th>
                            <th>Trigger Reason</th>
                            <th>Status</th>
                            <th>Logged At</th>
                        </tr>
                    </thead>
                    <tbody id="counselorAlertsTableBody">
                        ${rowsHtml}
                    </tbody>
                </table>
            </div>
        `;
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Poll live alerts API
    function pollAlerts() {
        fetch('/api/counselor/live_alerts')
            .then(res => {
                if (!res.ok) throw new Error("Network response not ok");
                return res.json();
            })
            .then(data => {
                // Update live counters
                if (statPendingAlerts && data.pending_alerts_count !== undefined) {
                    statPendingAlerts.textContent = data.pending_alerts_count;
                }
                if (headerPendingAlerts && data.pending_alerts_count !== undefined) {
                    headerPendingAlerts.textContent = data.pending_alerts_count;
                }
                if (statHighDistress && data.high_distress_count !== undefined) {
                    statHighDistress.textContent = data.high_distress_count;
                }
                if (statRecentCheckins && data.recent_checkins_count !== undefined) {
                    statRecentCheckins.textContent = data.recent_checkins_count;
                }
                if (statTotalSurvivors && data.total_survivors !== undefined) {
                    statTotalSurvivors.textContent = data.total_survivors;
                }

                // Update recent alerts list in table
                if (data.recent_alerts) {
                    updateRecentAlertsTable(data.recent_alerts);
                }

                // Check if there is an unhandled High-distress alert that wasn't dismissed yet
                if (data.has_high_alert && data.high_alert) {
                    const alertObj = data.high_alert;
                    if (!dismissedAlertIds.has(alertObj.id) && !modal.classList.contains('show')) {
                        showModal(alertObj);
                    }
                }
            })
            .catch(err => {
                // Silent fail for polling to avoid interrupting counselor
                console.debug("Alert polling tick:", err);
            });
    }

    // Initial check
    pollAlerts();

    // Poll every 3.5 seconds
    const pollInterval = setInterval(pollAlerts, 3500);

    // Clean up interval when navigating away
    window.addEventListener('beforeunload', () => clearInterval(pollInterval));
}
