/** @odoo-module **/

import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
import { useEffect, useRef } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

/**
 * Widget pour afficher des graphiques dans le tableau de bord IT
 * Utilise Chart.js pour le rendu
 */
class ITDashboardChartWidget extends Component {
    static template = "it_park.ITDashboardChart";
    static props = {
        ...standardFieldProps,
        options: { type: Object, optional: true },
    };

    setup() {
        this.chartRef = useRef("chart");
        this.chart = null;

        useEffect(() => {
            this._loadLibs().then(() => this._renderChart());
            return () => {
                if (this.chart) {
                    this.chart.destroy();
                }
            };
        });
    }

    /**
     * Charge Chart.js si nécessaire
     */
    async _loadLibs() {
        if (window.Chart) {
            return Promise.resolve();
        }
        return loadJS("/web/static/lib/Chart/Chart.js");
    }

    /**
     * Rend le graphique basé sur les données du modèle
     */
    _renderChart() {
        if (!this.chartRef.el) return;

        const data = JSON.parse(this.props.record.data[this.props.name] || "[]");
        if (!data || (Array.isArray(data) && !data.length)) {
            return;
        }

        const chartType = (this.props.options && this.props.options.type) || "bar";
        const ctx = this.chartRef.el.getContext("2d");

        // Préparation des données selon le format attendu par Chart.js
        let chartData;
        if (chartType === "pie" || chartType === "doughnut") {
            chartData = {
                labels: data.map(item => item.label || ""),
                datasets: [{
                    data: data.map(item => item.value || 0),
                    backgroundColor: data.map(item => item.color || this._getRandomColor()),
                    borderWidth: 0
                }]
            };
        } else {
            chartData = {
                labels: data.map(item => item.date || item.label || ""),
                datasets: [{
                    label: "Valeur",
                    data: data.map(item => item.value || 0),
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.2)',
                    borderWidth: 2,
                    fill: true,
                }]
            };
        }

        const chartConfig = {
            type: chartType,
            data: chartData,
            options: this._getChartOptions(chartType),
        };

        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, chartConfig);
    }

    /**
     * Obtient les options de configuration pour le type de graphique
     */
    _getChartOptions(chartType) {
        const options = {
            responsive: true,
            maintainAspectRatio: false,
        };

        if (chartType === "pie" || chartType === "doughnut") {
            options.plugins = {
                legend: {
                    position: "right",
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || "";
                            const value = context.formattedValue;
                            const dataset = context.dataset;
                            const total = dataset.data.reduce((acc, val) => acc + val, 0);
                            const percentage = Math.round((context.raw / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            };
        } else if (chartType === "line" || chartType === "bar") {
            options.plugins = {
                legend: {
                    position: "top",
                },
            };
            options.scales = {
                x: {
                    grid: {
                        display: false,
                    },
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false,
                    },
                    ticks: {
                        precision: 0,
                    },
                },
            };
        }

        return options;
    }

    /**
     * Génère une couleur aléatoire
     */
    _getRandomColor() {
        const colors = [
            '#4dc9f6', '#f67019', '#f53794', '#537bc4',
            '#acc236', '#166a8f', '#00a950', '#58595b',
            '#8549ba', '#e6194b', '#3cb44b', '#ffe119',
            '#4363d8', '#f58231', '#911eb4', '#46f0f0'
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }
}

// Enregistrement du widget dans le registre des champs
registry.category("fields").add("it_dashboard_chart", ITDashboardChartWidget);

// Export explicite du composant
export { ITDashboardChartWidget }; 