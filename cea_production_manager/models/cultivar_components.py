import datetime
from odoo import api, fields, models, _


class CultivarStages(models.Model):
    _name = "cultivar.components"
    _description = "Cultivar Components"

#Relational
    production_order_id = fields.One2many('production.model', 'cultivar_bom_id')