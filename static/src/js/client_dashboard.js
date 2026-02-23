odoo.define('PARC_IT.client_dashboard', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.ClientDashboard = publicWidget.Widget.extend({
        selector: '.progress-circle',
        
        start: function () {
            var def = this._super.apply(this, arguments);
            this._initProgressCircle();
            return def;
        },

        _initProgressCircle: function () {
            var progress = this.el.dataset.progress || 0;
            this.el.style.setProperty('--progress', progress);
        },
    });
}); 