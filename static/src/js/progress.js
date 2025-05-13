odoo.define('it__park.progress', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.ITProgress = publicWidget.Widget.extend({
        selector: '.progress-circle',
        
        start: function () {
            this._super.apply(this, arguments);
            this._initProgressCircle();
            return this;
        },
        
        _initProgressCircle: function () {
            var self = this;
            var progressValue = this.$el.data('value');
            
            // Convertir la valeur en degrés pour le gradient conique
            var degrees = (progressValue / 100) * 360;
            
            // Mettre à jour la propriété CSS personnalisée
            this.$el.css('--progress', degrees + 'deg');
            
            // Animation du cercle
            $({progress: 0}).animate({progress: progressValue}, {
                duration: 1500,
                step: function(now) {
                    var degrees = (now / 100) * 360;
                    self.$el.css('--progress', degrees + 'deg');
                }
            });
        },
    });
}); 