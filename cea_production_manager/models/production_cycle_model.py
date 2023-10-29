import datetime
from odoo import api, fields, models, _
from odoo.tools import config
from odoo.exceptions import ValidationError


class ProductionOrder(models.Model):
    _name = "production.model"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Production Order"

    # --Profile Fields--

    name = fields.Char("Order Reference", required=False, copy=False, readonly=True)
    ref = fields.Char('Reference', default=lambda self: _('New'), readonly=True)
    lot = fields.Char("LOT Number", readonly=True)
    cultivar_image = fields.Binary('Cultivar Image', related='cultivar_bom_id.image')
    cultivar_tags = fields.Many2many(string='Cultivar Tags', related='cultivar_bom_id.cultivar_tag_ids')

    # --Quantity Fields--

    quantity_ordered = fields.Integer('Cultivar Ordered')
    quantity_current = fields.Integer('Current Cultivar Quantity', default=0, readonly=True,
                                      compute='_compute_cultivar_quantity_current')
    quantity_lost = fields.Integer('Lost', readonly=True, compute='_compute_quantity_lost')
    quantity_harvested = fields.Integer('Quantity Harvested', readonly=True, compute='_compute_quantity_harvested')
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
        related='cultivar_bom_id.harvest_unit'
    )

    # --Scheduling Fields--

    scheduled_date = fields.Datetime('Date Scheduled')
    estimated_harvest_date = fields.Datetime('Estimated Harvest Date', compute='_compute_harvest_date')
    stage_end_date = fields.Datetime('Estimated Stage End Date', compute='_compute_stage_end_date')
    status = fields.Char(string="Operation", compute='_onchange_order_state')
    days_to_maturity = fields.Integer('Days To Maturity', related='cultivar_bom_id.days_to_maturity')
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("closed", "Closed"),
            ("canceled", "Canceled"),

        ],
        string="Status",
        required=True,
        default='draft',
        copy=False,
    )
    #  --Relational Fields--

    cultivar_bom_id = fields.Many2one('cultivar.bom', string='Cultivar', required=True)
    cultivar_id = fields.Many2one('cultivar.stages', 'Product')
    current_system_id = fields.Many2one('system.specifications', 'Current System Location',
                                        compute='_compute_system_location_cultivar_quantity')
    final_system_id = fields.Many2one('system.specifications', 'Final System Location',
                                      compute="_compute_final_system_location")
    next_system_id = fields.Many2one('system.specifications', 'Next System Location')
    stages_id = fields.One2many("cultivar.stages", "production_order_id", readonly=True,
                                states={'draft': [('readonly', False)]})
    harvest_logs_id = fields.One2many('harvest.logs', 'production_order_id', readonly=True)
    loss_logs_id = fields.One2many('loss.logs', 'production_order_id', readonly=True)

    # -- Default Domain --

    confirmed_order_domain = fields.Char(compute='_compute_confirmed_order_domain')

    # ---api calls--

    @api.onchange('cultivar_bom_id')
    def _compute_stages_id(self):
        for order in self:
            stages = []
            bom = order.cultivar_bom_id
            if bom:
                for stage in bom.cultivar_lifecycle_id:
                    stage_vals = {
                        'stage': stage.stage[0].upper() + stage.stage[1:],
                        'cultivar_profile_id': stage.cultivar_bom_id,
                        'description': stage.description,
                        'days': stage.days,
                        'minutes': stage.minutes,
                        'system_id': stage.system_id,
                        'parent_system_id': stage.system_id.parent_system_id,

                    }
                    stages.append((0, 0, stage_vals))
            order.stages_id = stages

    @api.depends('scheduled_date')
    def _compute_harvest_date(self):
        for order in self:
            if order.scheduled_date:
                order.estimated_harvest_date = order.scheduled_date + datetime.timedelta(days=order.days_to_maturity)
            else:
                order.estimated_harvest_date = None

    @api.depends('stages_id')
    def _compute_stage_end_date(self):
        for order in self:
            in_progress_stages = order.stages_id.filtered(lambda stage: stage.state == "in_progress")
            if order.stages_id:
                order.stage_end_date = in_progress_stages.est_end_date
            else:
                order.stage_end_date = None

    @api.onchange('stages_id')
    def _onchange_order_state(self):
        for order in self:
            in_progress_stages = order.stages_id.filtered(lambda stage: stage.state == "in_progress")
            if in_progress_stages:
                order.status = in_progress_stages[0].stage
            elif order.state == 'closed':
                order.status = "Closed"
            else:
                order.status = 'No Active Operations'

    @api.depends('quantity_ordered')
    def _compute_cultivar_quantity_current(self):
        for order in self:
            if order.state != 'draft' and not order.cultivar_bom_id.cut_come_again:
                order.quantity_current = order.quantity_ordered - order.quantity_harvested - order.quantity_lost
            if order.quantity_current == order.quantity_harvested and not order.cultivar_bom_id.cut_come_again:
                order.quantity_current = 0
            if order.state != 'draft' and order.cultivar_bom_id.cut_come_again:
                order.quantity_current = order.quantity_ordered - order.quantity_lost

    @api.depends('harvest_logs_id')
    def _compute_quantity_harvested(self):
        for rec in self:
            harvest_logs = rec.harvest_logs_id
            if not harvest_logs:
                rec.quantity_harvested = None
            else:
                total_harvest_quantity = sum(harvest_log.quantity_harvested for harvest_log in harvest_logs)
                rec.quantity_harvested = total_harvest_quantity

    @api.depends('loss_logs_id')
    def _compute_quantity_lost(self):
        for rec in self:
            loss_logs = rec.loss_logs_id
            if not loss_logs:
                rec.quantity_lost = None
            else:
                total_loss_quantity = sum(loss_log.quantity_lost for loss_log in loss_logs)
                rec.quantity_lost = total_loss_quantity

    @api.depends('stages_id')
    def _compute_system_location_cultivar_quantity(self):
        for order in self:
            in_progress_stages = order.stages_id.filtered(lambda stage: stage.state == "in_progress")
            if in_progress_stages:
                order.current_system_id = in_progress_stages.system_id
                in_progress_stages.cultivar_quantity = order.quantity_current
            else:
                order.current_system_id = None
                in_progress_stages.cultivar_quantity = None

    @api.depends('stages_id')
    def _compute_final_system_location(self):
        for order in self:
            stage = order.stages_id.filtered(lambda stage: stage.stage == "Growout")
            if stage:
                last_stage = stage[-1]
                order.final_system_id = last_stage.system_id
            else:
                order.final_system_id = False

    @api.model
    def _generate_sequence(self):
        sequence = self.env['ir.sequence'].next_by_code('production.order')
        return sequence

    @api.model_create_multi
    def create(self, vals_list):
        orders = []
        for vals in vals_list:
            vals['ref'] = self._generate_sequence()
            if 'stages_id' in vals:
                stages = vals.pop('stages_id')
                order = super(ProductionOrder, self).create(vals)
                order.write({'stages_id': stages})
                orders.append(order.id)
        return self.browse(orders)

    @api.onchange('cultivar_bom_id')
    def _clear_stages_id(self):
        self.stages_id = False

    def name_get(self):
        result = []
        for rec in self:
            name = '[' + rec.ref + ']'
            result.append((rec.id, name))

        return result

    def stage_state_validation_error(self, vals):
        if self.state in ['canceled', 'completed'] and 'stages_id' in vals:
            raise ValidationError("Cannot modify stages when the order is canceled or completed.")

        return super(ProductionOrder, self).write(vals)

    def button_confirm(self):
        for rec in self:
            if rec.scheduled_date and rec.quantity_ordered:
                rec.state = "confirmed"
            elif rec.quantity_ordered == 0:
                raise ValidationError("Quantity Must Be Greater Than Zero")
            elif rec.scheduled_date != True:
                raise ValidationError("Order Must Be Scheduled")
        return True

    def button_cancel(self):
        for rec in self:
            rec.state = "canceled"
            rec.stages_id.state = "canceled"
        return True

    def button_register_harvest(self):
        for rec in self:
            return {
                'name': 'Register Harvest Quantities',
                'type': 'ir.actions.act_window',
                'res_model': 'register.harvest.quantities',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_production_order_id': rec.id,
                },
            }

    def button_register_loss(self):
        for rec in self:
            return {
                'name': 'Register Loss Quantities',
                'type': 'ir.actions.act_window',
                'res_model': 'register.loss',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_production_order_id': rec.id,
                },
            }

    def button_close_order(self):
        for rec in self:
            return {
                'name': 'Order Close Confirmation',
                'type': 'ir.actions.act_window',
                'res_model': 'close.confirmation',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_production_order_id': rec.id,
                },
            }

    def _compute_confirmed_order_domain(self):
        default_domain = [('state', '=', 'confirmed')]
        self.confirmed_order_domain = default_domain
