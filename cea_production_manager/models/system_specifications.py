from odoo import api, fields, models
from odoo.tools.translate import _


class SystemSpecifications(models.Model):
    _name = "system.specifications"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "System Specifications & Work Centers"

    # --System General--
    name = fields.Char('Name')
    work_center_category = fields.Selection(selection=[
        ('growing_system', 'Growing System'),
        ('work_center', 'Work Center'),
        ('parent_system', 'Parent System'),
        ('aquaculture_system', 'Aquaculture System')
    ],
        string="Work Center Type",
        required=True,
        default=None,
        copy=False,
    )
    image = fields.Binary('Image')
    system_volume = fields.Float('System Volume')
    system_volume_units = fields.Selection(selection=[
        ('gallons', 'Gallons'), ('liters', 'Liters')],
        string='Units',
        required=True,
        default='gallons',
        copy=False)
    system_area_units = fields.Selection(selection=[
        ('feet2', 'ft2'), ('meters2', 'm2')],
        string='Units',
        required=True,
        default='feet2',
        copy=False)
    system_area = fields.Float('System Area')
    is_parent = fields.Boolean('Is Parent', compute='_compute_relations_parent', store=True)
    is_child = fields.Boolean('Is Child', compute='_compute_relations_child', store=True)

    # -- System Separation --
    system_units = fields.Integer('Number of Units Per System')
    unit_planting_capacity = fields.Integer('Planting Capacity Per Unit')
    total_system_planting_capacity = fields.Integer('Total System Planting Capacity',
                                                    compute='_compute_planting_capacity')
    current_system_planted = fields.Integer('Current System Planted', compute='_compute_current_planted')
    current_system_capacity = fields.Float('Current Capacity Met', compute='_compute_capacity_percentage')

    # Relational Fields

    tag_id = fields.Many2many('system.tag.ids', string='System Type')
    vendor_id = fields.Many2one('res.partner', 'Vendor', domain="[('category_id.name', '=', 'Vendor')]")
    parent_system_id = fields.Many2one('system.specifications', string="Parent System",
                                       domain="[('work_center_category', '=', 'parent_system')]")

    # One2Many
    logs_id = fields.One2many('system.logs', 'name', string="System Records")
    stages_id = fields.One2many('cultivar.stages', 'system_id', domain=[('def_end_date', '=', None),
                                                                        ('start_date', '!=', None)], readonly=True)
    parent_stages_id = fields.One2many('cultivar.stages', 'parent_system_id', domain=[('def_end_date', '=', None),
                                                                                      ('start_date', '!=', None)],
                                       readonly=True)

    @api.depends('unit_planting_capacity')
    def _compute_planting_capacity(self):
        for system in self:
            if system.unit_planting_capacity:
                system.total_system_planting_capacity = system.unit_planting_capacity * system.system_units
            else:
                system.total_system_planting_capacity = None

    @api.depends('stages_id')
    def _compute_current_planted(self):
        for system in self:
            in_progress_stages = system.stages_id.filtered(lambda stage: stage.cultivar_quantity > 0)
            total_planted_quantity = sum(
                in_progress_stage.cultivar_quantity for in_progress_stage in in_progress_stages)
            system.current_system_planted = total_planted_quantity

    @api.depends('current_system_planted')
    def _compute_capacity_percentage(self):
        for system in self:
            if system.work_center_category != 'work_center' and system.total_system_planting_capacity:
                system.current_system_capacity = 100 * (
                        system.current_system_planted / system.total_system_planting_capacity)
            else:
                system.current_system_capacity = None

    @api.onchange('work_center_category')
    def _compute_relations_parent(self):
        for system in self:
            if system.work_center_category == 'parent_system':
                system.is_parent = True
            else:
                system.is_parent = None

    @api.depends('parent_system_id')
    def _compute_relations_child(self):
        for system in self:
            if system.parent_system_id:
                system.is_child = True
            else:
                system.is_child = None
