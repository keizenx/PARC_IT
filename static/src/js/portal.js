/** @odoo-module **/

/**
 * JavaScript pour le portail client IT Park
 */
import publicWidget from 'web.public.widget';
import { _t } from 'web.core';
import ajax from 'web.ajax';

publicWidget.registry.ItParkPortal = publicWidget.Widget.extend({
    selector: '.it_park_portal',
    events: {
        'click .toggle-details': '_onToggleDetails',
        'click .filter-status': '_onFilterStatus',
        'change .ticket-priority': '_onChangePriority',
    },

    /**
     * @override
     */
    start: function () {
        return this._super.apply(this, arguments);
    },

    /**
     * Affiche/masque les détails d'un élément
     * @param {Event} ev
     * @private
     */
    _onToggleDetails: function (ev) {
        ev.preventDefault();
        $(ev.currentTarget).closest('.card').find('.item-details').toggleClass('d-none');
    },

    /**
     * Filtre les éléments par statut
     * @param {Event} ev
     * @private
     */
    _onFilterStatus: function (ev) {
        ev.preventDefault();
        var status = $(ev.currentTarget).data('status');
        
        // Mise à jour visuelle du filtre actif
        $('.filter-status').removeClass('active');
        $(ev.currentTarget).addClass('active');
        
        if (status === 'all') {
            $('.it-item').removeClass('d-none');
        } else {
            $('.it-item').addClass('d-none');
            $('.it-item[data-status="' + status + '"]').removeClass('d-none');
        }
    },

    /**
     * Change la priorité d'un ticket
     * @param {Event} ev
     * @private
     */
    _onChangePriority: function (ev) {
        var ticketId = $(ev.currentTarget).data('ticket-id');
        var newPriority = $(ev.currentTarget).val();
        
        ajax.jsonRpc('/my/ticket/priority', 'call', {
            'ticket_id': ticketId,
            'priority': newPriority,
        }).then(function (result) {
            if (result.success) {
                // Affichage d'une notification de succès
                var $notification = $('<div class="alert alert-success alert-dismissible fade show" role="alert">')
                    .text(_t('Priorité mise à jour avec succès.'))
                    .append($('<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close">'));
                
                $('.o_portal_my_home').prepend($notification);
                
                // Auto-fermeture après 3 secondes
                setTimeout(function () {
                    $notification.alert('close');
                }, 3000);
            }
        });
    },
}); 