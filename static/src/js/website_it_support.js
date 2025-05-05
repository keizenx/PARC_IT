/** @odoo-module **/

/**
 * JavaScript pour la gestion du support IT sur le site web
 */
import publicWidget from 'web.public.widget';
import { _t } from 'web.core';
import ajax from 'web.ajax';
import time from 'web.time';

// Widget pour la gestion du formulaire de ticket
const TicketFormWidget = publicWidget.Widget.extend({
    selector: '.it-ticket-form',
    events: {
        'change #equipment_id': '_onEquipmentChange',
        'click .attachment-clear': '_onAttachmentClear',
        'change input[type="file"]': '_onFileChange',
        'submit': '_onFormSubmit'
    },

    /**
     * @override
     */
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            // Initialisation du formulaire
            self._initForm();
        });
    },

    /**
     * Initialise le formulaire avec des valeurs par défaut et états
     * @private
     */
    _initForm: function () {
        // Afficher le nom du fichier après sélection
        this.$('input[type="file"]').on('change', function (e) {
            var fileName = e.target.files[0] ? e.target.files[0].name : '';
            $(this).next('.custom-file-label').html(fileName || _t('Choose file'));
        });

        // Masquer le bouton de suppression de pièce jointe au départ
        this.$('.attachment-clear').hide();
    },

    /**
     * Gère le changement d'équipement sélectionné
     * @private
     * @param {Event} ev
     */
    _onEquipmentChange: function (ev) {
        var equipmentId = $(ev.currentTarget).val();
        if (equipmentId) {
            // Récupérer les informations de l'équipement pour pré-remplir certains champs
            ajax.jsonRpc('/it-support/equipment-info', 'call', {
                'equipment_id': equipmentId
            }).then(function (result) {
                if (result && result.equipment) {
                    // Pré-remplir des informations basées sur l'équipement
                    if (result.equipment.type_id && result.equipment.type_id[0]) {
                        $('#incident_type_id').val(result.equipment.type_id[0]);
                    }
                }
            });
        }
    },

    /**
     * Gère la suppression de la pièce jointe
     * @private
     */
    _onAttachmentClear: function () {
        this.$('input[type="file"]').val('');
        this.$('.custom-file-label').html(_t('Choose file'));
        this.$('.attachment-clear').hide();
    },

    /**
     * Gère le changement de fichier
     * @private
     */
    _onFileChange: function (ev) {
        var fileName = ev.target.files[0] ? ev.target.files[0].name : '';
        if (fileName) {
            this.$('.attachment-clear').show();
        } else {
            this.$('.attachment-clear').hide();
        }
    },

    /**
     * Gère la soumission du formulaire
     * @private
     * @param {Event} ev
     */
    _onFormSubmit: function (ev) {
        // Validation de base côté client
        var $form = $(ev.currentTarget);
        var isValid = true;

        // Vérifier les champs requis
        $form.find('[required]').each(function () {
            if (!$(this).val()) {
                isValid = false;
                $(this).addClass('is-invalid');
            } else {
                $(this).removeClass('is-invalid');
            }
        });

        if (!isValid) {
            ev.preventDefault();
            return false;
        }

        // Ajouter un indicateur de chargement
        this.$('button[type="submit"]').prop('disabled', true).html(
            '<i class="fa fa-spinner fa-spin"></i> ' + _t('Sending...')
        );
    }
});

// Widget pour l'affichage des détails du ticket
const TicketDetailWidget = publicWidget.Widget.extend({
    selector: '.it-ticket-detail',

    /**
     * @override
     */
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self._setupRefreshTimer();
        });
    },

    /**
     * Configurer un rafraîchissement périodique de l'état du ticket
     * @private
     */
    _setupRefreshTimer: function () {
        var self = this;
        var ticketId = this.$el.data('ticket-id');
        
        if (ticketId) {
            // Rafraîchir le statut toutes les 5 minutes
            setInterval(function () {
                self._refreshTicketStatus(ticketId);
            }, 5 * 60 * 1000);
        }
    },

    /**
     * Rafraîchir l'état du ticket sans recharger la page
     * @private
     * @param {Number} ticketId
     */
    _refreshTicketStatus: function (ticketId) {
        var self = this;
        ajax.jsonRpc('/it-support/ticket-status', 'call', {
            'ticket_id': ticketId
        }).then(function (result) {
            if (result && result.state) {
                // Mettre à jour l'affichage de l'état
                self.$('.ticket-status').html(result.state_label);
                self.$('.ticket-status').removeClass().addClass('ticket-status badge badge-' + result.state);
                
                // Mettre à jour la dernière mise à jour
                self.$('.last-update-time').text(result.last_update);
                
                // Si résolu, afficher la résolution
                if (result.state === 'resolved' && result.resolution) {
                    self.$('.resolution-section').removeClass('d-none');
                    self.$('.resolution-content').html(result.resolution);
                }
            }
        });
    }
});

// Enregistrement des widgets
publicWidget.registry.itTicketForm = TicketFormWidget;
publicWidget.registry.itTicketDetail = TicketDetailWidget;

return {
    TicketFormWidget: TicketFormWidget,
    TicketDetailWidget: TicketDetailWidget
}; 