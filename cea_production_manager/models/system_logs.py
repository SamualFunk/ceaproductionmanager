from odoo import api, fields, models


class SystemLogs(models.Model):
    _name = "system.logs"
    _description = "System Logs"

    ref = fields.Char('Reference')
    name = fields.Char('System Name')
    date_created = fields.Datetime('Date')
    ph = fields.Float('pH')
    ec = fields.Float('EC (mS/cm)')
    tan = fields.Float('TAN (mg/L)')
    nitrite = fields.Float("Nitrite (mg/L)")
    nitrate = fields.Float("Nitrate (mg/L)")
    water_temp = fields.Float('Water Temperature (C)')
    notes = fields.Char('Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['ref'] = self.env['ir.sequence'].next_by_code('system.logs')
        return super(SystemLogs, self).create(vals_list)
