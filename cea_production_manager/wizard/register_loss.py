from odoo import api, fields, models, _
import datetime


class RegisterLossWizard(models.TransientModel):
    _name = 'register.loss'
    _description = 'Log Cultivar Loss'

    production_order_id = fields.Many2one('production.model', readonly=True)
    cultivar_profile_id = fields.Many2one('cultivar.bom', 'Cultivar Profile',
                                          related='production_order_id.cultivar_bom_id')
    system_id = fields.Many2one('system.specifications', related='production_order_id.current_system_id', readonly=True)
    date_lost = fields.Datetime('Date', default=lambda self: datetime.datetime.now())
    quantity_lost = fields.Integer('Quantity Lost', required=True)
    notes = fields.Text('Notes')
    current_quantity = fields.Integer('Cultivar Current Quantity', related='production_order_id.quantity_current')

    def button_register_loss(self):
        for wizard in self:
            production_order = wizard.production_order_id
            if production_order:
                loss_log = self.env['loss.logs'].create({
                    'production_order_id': production_order.id,
                    'cultivar_profile_id': wizard.cultivar_profile_id.id,
                    'system_id': wizard.system_id.id,
                    'date_lost': wizard.date_lost,
                    'quantity_lost': wizard.quantity_lost,
                    'notes': wizard.notes,
                })
                production_order.write({'loss_logs_id': [(4, loss_log.id)]})
        return {'type': 'ir.actions.act_window_close'}
