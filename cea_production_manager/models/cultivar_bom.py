from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class cultivar_bom(models.Model):
    _name = "cultivar.bom"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Cultivar Profile"

    # Generic

    ref = fields.Char(string='Reference', default='Cultivar Overview')
    image = fields.Binary('Cultivar Image')
    description = fields.Text('Description')
    seed_lot = fields.Char('Current Seed Lot Number')
    target_dli = fields.Integer('Target DLI')
    days_to_maturity = fields.Integer(string='Days To Maturity', compute='_compute_days_to_maturity')
    product_url = fields.Char('Product URL')
    planting_density = fields.Float('Planting Density')
    cut_come_again = fields.Boolean("Cut & Come Again?")
    harvest_unit = fields.Selection(selection=[
        ('lbs', 'Pounds'),
        ('g', 'Grams'),
        ('kg', 'Kilograms'),
        ('units', 'Units'),
    ],
        string='Harvest Unit of Measure',
        required='True',
        default='units',
        copy=False,
    )

    # Relational

    product_id = fields.Many2one('product.product', 'Product', required=True)
    cultivar_lifecycle_id = fields.One2many('cultivar.lifecycle', 'cultivar_bom_id')
    cultivar_tag_ids = fields.Many2many('cultivar.tag.ids')
    vendor = fields.Many2one('res.partner', 'Vendor', domain="[('category_id.name', '=', 'Vendor')]")
    cultivar_stages = fields.One2many('cultivar.stages', 'cultivar_profile_id',
                                      domain=[('def_end_date', '=', None),
                                              ('start_date', '!=', None)],
                                      readonly=True)
    cultivar_profile_product_line = fields.One2many('cultivar.profile.line', 'cultivar_profile_id')

    def name_get(self):
        result = []
        for rec in self:
            name = rec.product_id.name
            result.append((rec.id, name))
        return result

    #    def write(self, vals):
    #        for rec in self:
    #            if rec.cultivar_lifecycle_id:
    #                last_stage = rec.cultivar_lifecycle_id[-1]
    #                if last_stage.stage and last_stage.stage != 'harvest':
    #                    raise ValidationError("Don't forget to add a 'Harvest' operation in the Production Scheduler!")
    #
    #        return super(cultivar_bom, self).write(vals)

    @api.onchange('cultivar_stages')
    def _compute_days_to_maturity(self):
        for cultivar in self:
            total_days_to_maturity = 0
            for stage in cultivar.cultivar_lifecycle_id:
                if stage.days and stage.stage != 'harvest':
                    total_days_to_maturity += stage.days
            cultivar.days_to_maturity = total_days_to_maturity


class cultivar_profile_line(models.Model):
    _name = 'cultivar.profile.line'
    _description = 'Cultivar Components Line'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    cultivar_profile_id = fields.Many2one('cultivar.bom', 'Cultivar Profile', readonly=True)
    production_order = fields.Many2one('production.order', 'Production Order')
    product_qty = fields.Integer('Product Quantity')
    operation_id = fields.Many2one('cultivar.stages', 'Consumed in Operation')
