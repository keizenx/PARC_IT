/** @odoo-module **/

/**
 * Gestion des notifications pour les tickets IT
 */
import { bus } from '@web/core/network/bus_service';
import { registry } from '@web/core/registry';
import { session } from '@web/session';
import { browser } from '@web/core/browser/browser';
import { _t } from 'web.core';

export const ticketNotificationService = {
    dependencies: ['notification'],
    
    start(env, { notification }) {
        let audio;
        
        bus.addEventListener('notification', ({ detail: notifications }) => {
            // Filtrer les notifications pour les tickets
            const ticketNotifications = notifications.filter(
                notification => notification.type === 'it_park_tickets'
            );
            
            // Traiter les notifications de tickets
            ticketNotifications.forEach(notification => {
                const { payload } = notification;
                
                if (payload.message === 'new_ticket') {
                    handleNewTicket(payload.data);
                }
            });
        });
        
        function isITAdmin() {
            // Vérifier si l'utilisateur a le droit admin pour IT
            return session.user_has_group('it__park.group_it_park_manager');
        }
        
        function handleNewTicket(data) {
            // Vérifier si l'utilisateur est un administrateur IT
            if (!isITAdmin()) {
                return;
            }
            
            // Afficher une notification
            displayTicketNotification(data);
            
            // Jouer un son si demandé
            if (data.play_sound) {
                playSound();
            }
        }
        
        function displayTicketNotification(data) {
            // Créer une notification de navigateur
            const title = _t('Nouveau ticket: ') + data.reference;
            const message = data.title + '\n' + _t('Client: ') + data.client_name;
            
            // Vérifier si les notifications sont supportées
            if ('Notification' in browser.window) {
                if (browser.Notification.permission === 'granted') {
                    const notif = new browser.Notification(title, {
                        body: message,
                        icon: '/it__park/static/src/img/ticket_icon.png',
                    });
                    
                    // Rediriger vers le ticket lors du clic sur la notification
                    notif.onclick = function () {
                        browser.window.focus();
                        env.services.action.doAction({
                            type: 'ir.actions.act_window',
                            res_model: 'it.ticket',
                            res_id: data.ticket_id,
                            views: [[false, 'form']],
                            target: 'current',
                        });
                    };
                } else if (browser.Notification.permission !== 'denied') {
                    browser.Notification.requestPermission();
                }
            }
            
            // Afficher aussi dans l'interface Odoo
            notification.add(title, {
                message: message,
                type: 'warning',
                sticky: true,
                className: 'o_it_ticket_notification',
            });
        }
        
        function playSound() {
            // Jouer un son de notification
            if (!audio) {
                audio = new Audio('/it__park/static/src/sounds/notification.mp3');
            }
            audio.play().catch(function (error) {
                console.error('Erreur lors de la lecture du son:', error);
            });
        }
    }
};

registry.category('services').add('ticketNotification', ticketNotificationService);

odoo.define('it__park.ticket_notification', function (require) {
    'use strict';
    
    var core = require('web.core');
    var session = require('web.session');
    var BusService = require('bus.BusService');
    
    // Remplacer la méthode _handleNotification du BusService
    BusService.include({
        _handleNotification: function (notification) {
            var self = this;
            var channel = notification[0];
            var message = notification[1];
            
            // Gérer spécifiquement les notifications de ticket
            if (channel === 'it_park_tickets' && message.notification_type === 'new_ticket_alert' && message.sound) {
                self._displayTicketNotification(message);
            }
            
            // Appeler la méthode d'origine
            this._super.apply(this, arguments);
        },
        
        _displayTicketNotification: function (message) {
            // Vérifier si le navigateur prend en charge les notifications
            if (!("Notification" in window)) {
                console.warn("Ce navigateur ne prend pas en charge les notifications de bureau");
                return;
            }
            
            // Vérifier si l'utilisateur est administrateur
            session.user_has_group('it__park.group_it_admin').then(function (is_admin) {
                if (!is_admin) {
                    return; // Ne pas afficher la notification si l'utilisateur n'est pas administrateur
                }
                
                // Demander la permission si nécessaire
                if (Notification.permission === "granted") {
                    // Si c'est autorisé, créer une notification
                    self._createTicketNotification(message);
                } else if (Notification.permission !== "denied") {
                    // Nous devons demander la permission
                    Notification.requestPermission().then(function (permission) {
                        if (permission === "granted") {
                            self._createTicketNotification(message);
                        }
                    });
                }
            });
        },
        
        _createTicketNotification: function (message) {
            // Créer une notification
            var notification = new Notification("Nouveau ticket IT", {
                body: message.client_name + ": " + message.title,
                icon: "/it__park/static/src/img/ticket_icon.png"
            });
            
            // Jouer un son d'alerte
            var audio = new Audio('/it__park/static/src/sounds/notification.mp3');
            audio.play();
            
            // Gérer le clic sur la notification
            notification.onclick = function () {
                window.focus();
                var action = {
                    type: 'ir.actions.act_window',
                    res_model: 'it.ticket',
                    res_id: message.ticket_id,
                    views: [[false, 'form']],
                    target: 'current'
                };
                self.do_action(action);
                notification.close();
            };
        }
    });
}); 