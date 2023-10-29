import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class CultivarStages(models.Model):
    _name = "cultivar.stages"
    _description = "Cultivar Stages"

    # Standard fields

    stage = fields.Char('Stage', readonly=True)
    days = fields.Integer('Duration(Days)')
    minutes = fields.Float('Duration(Minutes)')
    description = fields.Char('Stage Description', readonly=True)
    is_harvest_stage = fields.Boolean('Harvest Stage', readonly=True)
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("canceled", "Canceled"),
            ("harvested", "Harvested"),
            ("closed", "Closed"),

        ],
        string="Status",
        required=True,
        default='pending',
        copy=False,
    )

    # Computed fields
    start_date = fields.Datetime('Start Date', copy=False)
    est_end_date = fields.Datetime('Estimated End Date', compute='_compute_est_end_date')
    def_end_date = fields.Datetime('Actual End Date')
    cultivar_quantity = fields.Integer('Cultivar Quantity', readonly=True)

    # Relational fields
    cultivar_profile_id = fields.Many2one('cultivar.bom', 'Cultivar Profile', readonly=True)
    production_order_id = fields.Many2one('production.model', 'Production Order ID', readonly=True)
    system_id = fields.Many2one('system.specifications', 'Location')
    users_id = fields.Many2one('res.users', 'User')
    cultivar_lifecycle_id = fields.One2many('cultivar.lifecycle', 'cultivar_stages', readonly=True)
    parent_system_id = fields.Many2one('system.specifications', related='system_id.parent_system_id')


    def action_start(self):
        for rec in self:
            if rec.production_order_id.state != 'draft':
                rec.start_date = datetime.datetime.now()
                rec.state = 'in_progress'
            else:
                raise ValidationError("Order Must Be Confirmed")


    def action_set_done(self):
        for rec in self:
            rec.def_end_date = datetime.datetime.now()
            rec.state = 'completed'

    def action_set_harvest(self):
        for rec in self:
            rec.def_end_date = datetime.datetime.now()
            rec.state = 'completed'

    def action_cancel(self):
        for rec in self:
            if rec.production_order_id.state == 'canceled':
                rec.state = 'canceled'

    def action_closed(self):
        for rec in self:
            if rec.production_order_id.state == 'closed':
                rec.state = 'closed'

    @api.depends('start_date', 'days')
    def _compute_est_end_date(self):
        for rec in self:
            if rec.start_date:
                rec.est_end_date = rec.start_date + datetime.timedelta(days=rec.days, minutes=rec.minutes)
            else:
                rec.est_end_date = None
