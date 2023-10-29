from odoo import api, fields, models, _


class CloseOrderConfirmationWizard(models.TransientModel):
    _name = 'close.confirmation'
    _description = 'Close Order Confirmation Wizard'

    production_order_id = fields.Many2one('production.model', 'Production Order', required=True, readonly=True)

    def confirm_close_order(self):
        self.ensure_one()
        self.production_order_id.state = 'closed'
        return {'type': 'ir.actions.act_window_close'}