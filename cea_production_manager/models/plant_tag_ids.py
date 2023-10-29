from odoo import api, fields, models

class ProductionOrder(models.Model):
    _name = "cultivar.tag.ids"


    name = fields.Char("Cultivar Tags")
