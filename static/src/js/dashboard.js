/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, useRef, onMounted, useEffect, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * Composant pour afficher une carte de statistique dans le tableau de bord
 */
class ITDashboardCard extends Component {
    static template = "it_park.DashboardCard";
    static props = {
        title: { type: String, optional: true },
        value: { type: Number, optional: true },
        description: { type: String, optional: true },
        onClick: { type: Function, optional: true },
    };
}

/**
 * Composant pour afficher un graphique des incidents par priorité
 */
class ITDashboardChartComponent extends Component {
    static template = "it_park.DashboardChart";
    
    setup() {
        this.state = useState({ loaded: false });
        this.chartRef = useRef("chart");
        this.orm = useService("orm");
        this.chartData = {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#4CAF50', // Vert
                    '#FFC107', // Jaune
                    '#F44336', // Rouge
                    '#9C27B0'  // Violet
                ]
            }]
        };
        
        onWillStart(async () => {
            await this.fetchData();
        });
        
        onMounted(() => {
            this.renderChart();
        });
    }
    
    async fetchData() {
        try {
            const result = await this.orm.call('it.incident', 'get_incidents_by_priority', []);
            if (result && result.length) {
                // Formater les données pour le graphique
                const labels = [];
                const data = [];
                
                result.forEach(item => {
                    labels.push(item.priority_name);
                    data.push(item.count);
                });
                
                this.chartData.labels = labels;
                this.chartData.datasets[0].data = data;
                
                this.state.loaded = true;
            }
        } catch (error) {
            console.error("Erreur lors du chargement des données du graphique", error);
        }
    }
    
    async renderChart() {
        if (!this.state.loaded || !this.chartRef.el) return;
        
        const { Chart } = await import('chart.js/auto');
        
        // Création du graphique
        this.chart = new Chart(this.chartRef.el, {
            type: 'pie',
            data: this.chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return `${context.label}: ${context.raw} incidents`;
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Composant principal du tableau de bord du parc IT
 */
class ITDashboard extends Component {
    static template = "it_park.Dashboard";
    static components = { 
        ITDashboardCard, 
        ITDashboardChart: ITDashboardChartComponent 
    };
    
    setup() {
        this.state = useState({
            equipmentCount: 0,
            softwareCount: 0,
            expiringLicenses: 0,
            openIncidents: 0,
            pendingInterventions: 0
        });
        
        this.orm = useService("orm");
        this.actionService = useService("action");
        
        onWillStart(async () => {
            await this.fetchDashboardData();
        });
    }
    
    async fetchDashboardData() {
        try {
            const data = await this.orm.call('it.dashboard', 'get_dashboard_data', []);
            this.state.equipmentCount = data.equipment_count || 0;
            this.state.softwareCount = data.software_count || 0;
            this.state.expiringLicenses = data.expiring_licenses || 0;
            this.state.openIncidents = data.open_incidents || 0;
            this.state.pendingInterventions = data.pending_interventions || 0;
        } catch (error) {
            console.error("Erreur lors du chargement des données du tableau de bord", error);
        }
    }
    
    openEquipments() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Équipements',
            res_model: 'it.equipment',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }
    
    openSoftware() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Logiciels',
            res_model: 'it.software',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }
    
    openExpiringLicenses() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Licences expirant prochainement',
            res_model: 'it.license',
            domain: [
                ['state', '=', 'active'],
                ['end_date', '!=', false],
                ['end_date', '>', (new Date()).toISOString().split('T')[0]],
                ['end_date', '<=', this.getDatePlusDays(30)],
            ],
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }
    
    openOpenIncidents() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Incidents en cours',
            res_model: 'it.incident',
            domain: [['state', '!=', 'done']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }
    
    openPendingInterventions() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Interventions planifiées',
            res_model: 'it.intervention',
            domain: [['state', '=', 'planned']],
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }
    
    getDatePlusDays(days) {
        const date = new Date();
        date.setDate(date.getDate() + days);
        return date.toISOString().split('T')[0];
    }
}

// Enregistrement des composants
registry.category("actions").add("it_park_dashboard", ITDashboard);

// Export explicite des composants pour s'assurer qu'ils sont disponibles
export { ITDashboard, ITDashboardCard, ITDashboardChartComponent }; 