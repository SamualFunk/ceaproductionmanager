from odoo import api, fields, models


class HarvestLogs(models.Model):
    _name = "harvest.logs"
    _description = "Harvest Logs"

    production_order_id = fields.Many2one('production.model')
    cultivar_profile_id = fields.Many2one('cultivar.bom', 'Cultivar Profile')
    system_id = fields.Many2one('system.specifications')
    date_harvested = fields.Datetime('Date')
    quantity_harvested = fields.Integer('Quantity Harvested')
    harvest_uom = fields.Char('Harvest Unit')
    notes = fields.Text('Notes')


