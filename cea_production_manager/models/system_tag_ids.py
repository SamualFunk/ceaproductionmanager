from odoo import api, fields, models

class ProductionOrder(models.Model):
    _name = "system.tag.ids"


    name = fields.Char("System Type")

