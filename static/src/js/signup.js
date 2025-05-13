odoo.define('it__park.signup', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.ITSignupForm = publicWidget.Widget.extend({
        selector: '.oe_signup_form',
        events: {
            'submit': '_onSubmit',
        },

        _onSubmit: function (ev) {
            var $form = $(ev.currentTarget);
            var $button = $form.find('button[type="submit"]');
            
            if (!$button.prop('disabled')) {
                $button.prop('disabled', true);
                $button.prepend('<i class="fa fa-spinner fa-spin me-2"/>');
            }
        },
    });
}); 