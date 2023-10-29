from odoo import api, fields, models


class LossLogs(models.Model):
    _name = "loss.logs"
    _description = "Loss Logs"

    production_order_id = fields.Many2one('production.model')
    cultivar_profile_id = fields.Many2one('cultivar.bom', 'Cultivar Profile')
    system_id = fields.Many2one('system.specifications')
    date_lost = fields.Datetime('Date')
    quantity_lost = fields.Integer('Quantity Lost')
    notes = fields.Text('Notes')