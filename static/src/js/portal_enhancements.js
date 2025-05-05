/** @odoo-module **/

/**
 * Module JavaScript pour les améliorations visuelles du portail IT Park
 */
import publicWidget from 'web.public.widget';
import { _t } from 'web.core';

// Affiche un message dans la console pour confirmer que le script est chargé
console.log('IT Park Portal Enhancements loaded successfully!');

// Widget pour les améliorations du portail
publicWidget.registry.ITPortalEnhancements = publicWidget.Widget.extend({
    selector: '.o_portal',
    events: {
        'click .btn-primary': '_onButtonClick',
    },

    /**
     * @override
     */
    start: function () {
        var self = this;
        this._applyVisualEnhancements();
        return this._super.apply(this, arguments);
    },

    /**
     * Applique les améliorations visuelles via JavaScript
     * @private
     */
    _applyVisualEnhancements: function () {
        // Ajoute des classes pour les animations
        $('.o_portal_navbar, header').addClass('animate-fadeInUp');
        
        // Ajoute des effets d'animation aux éléments du tableau
        $('.table tbody tr').each(function(index) {
            $(this).addClass('animate-fadeInUp');
            $(this).css('animation-delay', (index * 0.1) + 's');
        });

        // Améliore l'aspect des badges
        $('.badge').addClass('shadow-sm');

        // Ajoute un bouton retour en haut de page
        if ($('.o_portal').length && !$('#back-to-top').length) {
            $('body').append('<button id="back-to-top" class="btn btn-primary btn-sm rounded-circle shadow">' +
                '<i class="fa fa-arrow-up"></i></button>');
            
            $('#back-to-top').css({
                'position': 'fixed',
                'bottom': '20px',
                'right': '20px',
                'display': 'none',
                'z-index': '999',
                'width': '40px',
                'height': '40px',
            }).click(function() {
                $('html, body').animate({scrollTop: 0}, 500);
            });
            
            // Affiche le bouton quand on défile
            $(window).scroll(function() {
                if ($(this).scrollTop() > 300) {
                    $('#back-to-top').fadeIn();
                } else {
                    $('#back-to-top').fadeOut();
                }
            });
        }

        // Ajoute un effet de survol sur les cartes
        $('.card').hover(
            function() { $(this).addClass('shadow-lg').css('transform', 'translateY(-5px)'); },
            function() { $(this).removeClass('shadow-lg').css('transform', 'translateY(0)'); }
        );
        
        // S'assurer que les liens des tickets pointent vers la bonne route
        $('a[href="/my/tickets"]').attr('href', '/my/tickets');
        $('a:contains("Créer un ticket support")').attr('href', '/my/tickets/create');

        // Affiche un message de confirmation que les améliorations sont appliquées
        console.log('Visual enhancements applied successfully!');
    },

    /**
     * Gère le clic sur les boutons principaux
     * @private
     */
    _onButtonClick: function (ev) {
        // Ajoute un effet de pulsation au bouton cliqué
        $(ev.currentTarget).addClass('btn-pulse');
        setTimeout(function() {
            $(ev.currentTarget).removeClass('btn-pulse');
        }, 500);
    },
}); 