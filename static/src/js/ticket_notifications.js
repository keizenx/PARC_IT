odoo.define('PARC_IT.ticket_notifications', function (require) {
    "use strict";

    var core = require('web.core');
    var session = require('web.session');
    var ajax = require('web.ajax');
    var bus = require('bus.bus').bus;

    // Variables globales
    var notification_sound = new Audio('/PARC_IT/static/src/sounds/chime-alert-demo-309545.mp3');
    var last_notification_id = 0;
    var notifications = [];
    var is_admin = false;

    // Initialisation du module
    function initTicketNotifications() {
        console.log("Initialisation du système de notifications de tickets");

        // Vérifier si l'utilisateur est un administrateur IT
        ajax.rpc('/it_park/check_is_admin', {}).then(function (result) {
            is_admin = result.is_admin;
            console.log("Est administrateur IT: ", is_admin);
            
            if (is_admin) {
                // S'abonner au canal des notifications de tickets
                bus.add_channel('it_park_tickets');
                bus.start_polling();

                // Gestionnaire d'événements pour les notifications
                bus.on('notification', handleNotification);

                // Si nous sommes dans le module IT Park, afficher une alerte pour les tickets non traités
                if (window.location.href.includes('/web#action=it_park.action_it_tickets')) {
                    checkPendingTickets();
                }
            }
        });
    }

    // Gérer les notifications reçues
    function handleNotification(notifications) {
        notifications.forEach(function (notification) {
            var channel = notification[0];
            var message = notification[1];

            if (channel === 'it_park_tickets' && message.type === 'new_ticket_alert') {
                // Mémoriser l'ID de notification
                last_notification_id = message.id;

                // Jouer le son
                if (message.sound) {
                    notification_sound.play().catch(function(error) {
                        console.log("Impossible de jouer le son de notification:", error);
                    });
                }

                // Afficher une notification
                if (Notification && Notification.permission === "granted") {
                    var n = new Notification("Nouveau ticket IT", {
                        body: "Ticket #" + message.reference + " - " + message.title + " créé par " + message.client_name,
                        icon: "/PARC_IT/static/description/icon.png"
                    });

                    // Rediriger vers le ticket quand on clique
                    n.onclick = function() {
                        window.open('/web#id=' + message.ticket_id + '&model=it.ticket&view_type=form', '_blank');
                        n.close();
                    };
                }

                // Afficher une alerte dans l'interface Odoo
                if (window.location.href.includes('/web')) {
                    showTicketAlert(message);
                }
            }
        });
    }

    // Vérifier s'il y a des tickets en attente
    function checkPendingTickets() {
        ajax.rpc('/it_park/check_pending_tickets', {}).then(function (result) {
            if (result.pending_count > 0) {
                showPendingTicketsAlert(result.pending_count);
            }
        });
    }

    // Afficher une alerte pour un nouveau ticket
    function showTicketAlert(message) {
        var alertDiv = $('<div>').addClass('alert alert-info alert-dismissible fade show')
            .attr('role', 'alert')
            .css({
                'position': 'fixed',
                'top': '20px',
                'right': '20px',
                'z-index': '9999',
                'width': '300px',
                'box-shadow': '0 4px 8px rgba(0,0,0,0.2)'
            });

        alertDiv.html(
            '<strong>Nouveau ticket!</strong>' +
            '<p>Ticket #' + message.reference + ' - ' + message.title + '</p>' +
            '<p>Client: ' + message.client_name + '</p>' +
            '<p>Priorité: ' + message.priority + '</p>' +
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'
        );

        $('body').append(alertDiv);

        // Disparaître après 10 secondes
        setTimeout(function() {
            alertDiv.alert('close');
        }, 10000);
    }

    // Afficher une alerte pour les tickets en attente
    function showPendingTicketsAlert(count) {
        var alertDiv = $('<div>').addClass('alert alert-warning')
            .css({
                'margin': '20px',
                'text-align': 'center',
                'font-size': '16px'
            });

        alertDiv.html(
            '<strong>Attention!</strong> Vous avez ' + count + ' ticket(s) en attente de traitement.'
        );

        // Insérer au début du contenu principal
        $('.o_content').prepend(alertDiv);
    }

    // Demander la permission pour les notifications
    function requestNotificationPermission() {
        if (Notification && Notification.permission !== "granted") {
            Notification.requestPermission();
        }
    }

    // Initialiser le module
    $(document).ready(function() {
        requestNotificationPermission();
        initTicketNotifications();
    });

    return {
        initTicketNotifications: initTicketNotifications,
        requestNotificationPermission: requestNotificationPermission
    };
}); 