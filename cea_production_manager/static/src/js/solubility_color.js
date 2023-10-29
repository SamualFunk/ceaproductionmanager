odoo.define('production_cycle.custom_script', function (require) {
    "use strict";

    var fieldRegistry = require('web.field_registry');
    var FieldFloat = fieldRegistry.get('float');

    var ExceededSolubilityField = FieldFloat.extend({
        _render: function () {
            this._super.apply(this, arguments);
            if (this.recordData.solubility_levels > this.recordData.solubility) {
                this.$el.addClass('exceeded-solubility-levels');
            } else {
                this.$el.removeClass('exceeded-solubility-levels');
            }
        },
    });

    fieldRegistry.add('exceeded_solubility_field', ExceededSolubilityField);
});
