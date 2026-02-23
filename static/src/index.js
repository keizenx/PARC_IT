/** @odoo-module **/

/**
 * Ce fichier est le point d'entrée pour les composants JavaScript du module PARC_IT.
 * Il importe et réexporte tous les composants pour s'assurer qu'ils sont correctement 
 * chargés et disponibles dans l'application.
 */

// Import et export des composants du dashboard
import { ITDashboard, ITDashboardCard, ITDashboardChartComponent } from './js/dashboard';
import { ITDashboardChartWidget } from './js/dashboard_chart';

// Réexporter les composants
export {
    ITDashboard,
    ITDashboardCard,
    ITDashboardChartComponent,
    ITDashboardChartWidget
}; 