/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, xml, onWillStart, onMounted, useState } from "@odoo/owl";
import { useSetupAction } from "@web/webclient/actions/action_hook";

/**
 * Composant pour la gestion des notifications d'incidents
 * Ce composant s'initialise automatiquement et vérifie périodiquement 
 * s'il y a de nouveaux incidents non assignés
 */
export class IncidentNotificationManager extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.action = useService("action");
        this.bus = useService("bus_service");
        this.state = useState({
            lastCheckTime: null,
            incidentCount: 0,
            hasNewIncidents: false,
        });

        // Configurer l'intervalle pour vérifier les nouveaux incidents
        onWillStart(async () => {
            this.state.lastCheckTime = new Date();
            const result = await this._checkForNewIncidents();
            this.state.incidentCount = result.count;
            
            // S'abonner au canal de notification des incidents
            this.bus.subscribe("it_park_incidents", (payload) => {
                if (payload.type === "new_incident") {
                    this._handleNewIncidentNotification(payload.payload);
                }
            });
        });

        onMounted(() => {
            // Configurer une vérification périodique (toutes les 2 minutes)
            this.intervalId = setInterval(() => {
                this._checkForNewIncidents();
            }, 2 * 60 * 1000);

            // Créer l'élément audio pour les notifications sonores
            this.audioElement = document.createElement('audio');
            this.audioElement.src = '/it__park/static/src/sounds/chime-alert-demo-309545.mp3';
            this.audioElement.setAttribute('preload', 'auto');
            document.body.appendChild(this.audioElement);
        });
    }

    /**
     * Vérifie s'il y a de nouveaux incidents non assignés
     * @private
     * @returns {Promise<Object>} Résultat contenant le nombre d'incidents et s'il y en a de nouveaux
     */
    async _checkForNewIncidents() {
        const result = await this.rpc("/it_park/check_new_incidents", {
            last_check_time: this.state.lastCheckTime ? this.state.lastCheckTime.toISOString() : false,
        });

        if (result.new_incidents && result.count > 0) {
            this.state.hasNewIncidents = true;
            this.state.incidentCount = result.count;
            
            // Jouer un son pour avertir l'utilisateur
            if (this.audioElement) {
                try {
                    this.audioElement.play();
                } catch (e) {
                    console.warn("Impossible de jouer le son de notification:", e);
                }
            }

            // Afficher une notification dans l'interface
            this._showNotification(result);
        }

        this.state.lastCheckTime = new Date();
        return result;
    }

    /**
     * Gère la réception d'une notification d'un nouvel incident via le bus
     * @private
     * @param {Object} data Données de l'incident
     */
    _handleNewIncidentNotification(data) {
        if (!data || !data.incident_id) {
            return;
        }

        // Incrémenter le compteur d'incidents
        this.state.hasNewIncidents = true;
        this.state.incidentCount += 1;
        
        // Jouer un son pour avertir l'utilisateur
        if (this.audioElement) {
            try {
                this.audioElement.currentTime = 0;
                this.audioElement.play();
            } catch (e) {
                console.warn("Impossible de jouer le son de notification:", e);
            }
        }

        // Afficher une notification dans l'interface
        this.notification.add(
            this._formatNotificationTitle(data),
            {
                type: "warning",
                sticky: true,
                buttons: [{
                    name: "Voir",
                    onClick: () => this._openIncident(data.incident_id),
                    primary: true
                }],
                message: data.description,
                className: 'o_incident_notification',
            }
        );
    }

    /**
     * Affiche une notification dans l'interface utilisateur
     * @private
     * @param {Object} data Données sur les nouveaux incidents
     */
    _showNotification(data) {
        if (!data.incidents || data.incidents.length === 0) {
            return;
        }

        // Afficher une notification pour chaque incident (jusqu'à 3 max)
        const incidentsToShow = data.incidents.slice(0, 3);
        
        incidentsToShow.forEach(incident => {
            this.notification.add(
                this._formatNotificationTitle(incident),
                {
                    type: "warning",
                    sticky: true,
                    buttons: [{
                        name: "Voir",
                        onClick: () => this._openIncident(incident.id),
                        primary: true
                    }],
                    message: incident.description.substring(0, 100) + (incident.description.length > 100 ? '...' : '')
                }
            );
        });

        // Si plus de 3 incidents, afficher un message pour le reste
        if (data.incidents.length > 3) {
            const remainingCount = data.incidents.length - 3;
            this.notification.add(
                `${remainingCount} autre(s) ticket(s) en attente`,
                {
                    type: "info",
                    buttons: [{
                        name: "Voir tous",
                        onClick: () => this._openIncidentList(),
                        primary: true
                    }],
                }
            );
        }
    }

    /**
     * Formate le titre de la notification
     * @private
     * @param {Object} incident Données d'un incident
     * @returns {string} Titre formaté pour la notification
     */
    _formatNotificationTitle(incident) {
        const priorityIcons = {
            '0': '🟢',
            '1': '🟠',
            '2': '🔴',
            '3': '⚠️'
        };
        const icon = priorityIcons[incident.priority] || '🔔';
        return `${icon} Nouveau ticket: ${incident.reference} - ${incident.name}`;
    }

    /**
     * Ouvre le formulaire d'un incident spécifique
     * @private
     * @param {number} incidentId ID de l'incident à ouvrir
     */
    _openIncident(incidentId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "it.incident",
            res_id: incidentId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    /**
     * Ouvre la liste des incidents non assignés
     * @private
     */
    _openIncidentList() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Nouveaux tickets",
            res_model: "it.incident",
            domain: [["state", "=", "new"], ["tech_id", "=", false]],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

IncidentNotificationManager.template = xml`
    <div class="incident-notification-manager">
        <t t-if="state.hasNewIncidents and state.incidentCount > 0">
            <div class="incident-counter">
                <span class="badge rounded-pill bg-danger" t-on-click="_openIncidentList">
                    <t t-esc="state.incidentCount"/>
                </span>
            </div>
        </t>
    </div>
`;

// Enregistrer le composant pour qu'il soit automatiquement initialisé
registry.category("main_components").add("IncidentNotificationManager", {
    Component: IncidentNotificationManager,
}); 