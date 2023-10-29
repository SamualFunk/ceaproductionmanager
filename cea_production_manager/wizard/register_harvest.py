from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import datetime

class RegisterHarvestWizard(models.TransientModel):
    _name = 'register.harvest.quantities'
    _description = 'Register Harvest Quantities'

    production_order_id = fields.Many2one('production.model', readonly=True)
    cultivar_profile_id = fields.Many2one('cultivar.bom', 'Cultivar Profile',
                                          related='production_order_id.cultivar_bom_id')
    system_id = fields.Many2one('system.specifications', related='production_order_id.current_system_id', readonly=True)
    date_harvested = fields.Datetime('Date', default=lambda self: datetime.datetime.now())
    quantity_harvested = fields.Integer('Quantity Harvested', required=True)
    harvest_unit = fields.Selection(selection=[
        ('lbs', 'Pounds'),
        ('g', 'Grams'),
        ('kg', 'Kilograms'),
        ('units', 'Units'),
    ],
        string='Harvest Unit of Measure',
        required='True',
        copy=False,
        related='production_order_id.harvest_unit')
    notes = fields.Text('Notes')
    cut_come_again = fields.Boolean("Cut & Come Again?", related='production_order_id.cultivar_bom_id.cut_come_again',
                                    readonly=True)
    current_quantity = fields.Integer('Cultivar Current Quantity', related='production_order_id.quantity_current')

    def button_register_harvest(self):
        for wizard in self:
            production_order = wizard.production_order_id
            if production_order:
                if wizard.cut_come_again:
                    harvest_log = self.env['harvest.logs'].create({
                        'production_order_id': production_order.id,
                        'cultivar_profile_id': wizard.cultivar_profile_id.id,
                        'system_id': wizard.system_id.id,
                        'date_harvested': wizard.date_harvested,
                        'quantity_harvested': wizard.quantity_harvested,
                        'harvest_uom': wizard.harvest_unit,
                        'notes': wizard.notes,
                    })
                    production_order.write({'harvest_logs_id': [(4, harvest_log.id)]})
                if not wizard.cut_come_again and wizard.quantity_harvested > wizard.current_quantity:
                    raise ValidationError(f"Cannot Harvest More Than Current Cultivar Quantity of {wizard.current_quantity}")
                if not wizard.cut_come_again and wizard.quantity_harvested <= wizard.current_quantity:
                    harvest_log = self.env['harvest.logs'].create({
                        'production_order_id': production_order.id,
                        'cultivar_profile_id': wizard.cultivar_profile_id.id,
                        'system_id': wizard.system_id.id,
                        'date_harvested': wizard.date_harvested,
                        'quantity_harvested': wizard.quantity_harvested,
                        'harvest_uom': wizard.harvest_unit,
                        'notes': wizard.notes,
                    })
                    production_order.write({'harvest_logs_id': [(4, harvest_log.id)]})
        return {'type': 'ir.actions.act_window_close'}
