/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";

export class ReingenieriaAuditDashboard extends Component {
    static template = "reingenieria_iso_audit.DashboardTemplate";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.trendCanvas = useRef("trendChart");
        this.severityCanvas = useRef("severityChart");
        this.charts = [];

        this.state = useState({
            period: "6m",
            data: null,
        });

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.loadData();
        });

        onMounted(() => {
            this.renderCharts();
        });
    }

    async loadData() {
        this.state.data = await this.orm.call(
            "audit.dashboard",
            "get_dashboard_data",
            [this.state.period]
        );
    }

    async onChangePeriod(ev) {
        this.state.period = ev.target.value;
        await this.loadData();
        this.renderCharts();
    }

    async onRefresh() {
        await this.loadData();
        this.renderCharts();
    }

    renderCharts() {
        this.charts.forEach((c) => c.destroy());
        this.charts = [];
        if (!this.state.data || !window.Chart) return;

        // 1. Gráfica de Tendencia (Línea)
        if (this.trendCanvas.el) {
            const ctxTrend = this.trendCanvas.el.getContext("2d");
            this.charts.push(
                new window.Chart(ctxTrend, {
                    type: "line",
                    data: {
                        labels: this.state.data.trend.labels,
                        datasets: [{
                            label: "NCRs Detectadas",
                            data: this.state.data.trend.values,
                            borderColor: "#198754",
                            backgroundColor: "rgba(25, 135, 84, 0.15)",
                            tension: 0.3,
                            fill: true,
                        }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
                    },
                })
            );
        }

        // 2. Gráfica de Severidad (Dona)
        if (this.severityCanvas.el) {
            const sev = this.state.data.severity;
            const ctxSev = this.severityCanvas.el.getContext("2d");
            this.charts.push(
                new window.Chart(ctxSev, {
                    type: "doughnut",
                    data: {
                        labels: ["Menor", "Mayor", "Crítica"],
                        datasets: [{
                            data: [sev.minor, sev.major, sev.critical],
                            backgroundColor: ["#0d6efd", "#fd7e14", "#dc3545"],
                        }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: "60%",
                    },
                })
            );
        }
    }

    openAction(resModel, name, domain = []) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: name,
            res_model: resModel,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
        });
    }

    openNcrRecord(ncrId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "quality.ncr",
            res_id: ncrId,
            views: [[false, "form"]],
        });
    }
}

registry.category("actions").add("reingenieria_iso_audit.dashboard_tag", ReingenieriaAuditDashboard);
