from odoo import api, fields, models, _


class CultivarStages(models.Model):
    _name = "cultivar.lifecycle"
    _description = "Cultivar Lifecycle"

    # Standard fields

    stage = fields.Selection(selection=[
        ('seeding', 'Seeding'),
        ('germination', 'Germination'),
        ('growout', 'Growout'),
        ('transfer', 'Transfer'),
        ('harvest', 'Harvest'),
    ],
        string="Operation Type",
        required=True,
        default='seeding',
        copy=False,
    )

    duration_category = fields.Selection(
        selection=[
            ("passive", "Passive"),
            ("labor", "Task"),
            ("harvest", "Harvest")

        ],
        string="Operation Category",
        required=True,
        default=None,
        copy=False,
        compute='_compute_duration_category'

    )
    description = fields.Char('Stage Description', compute='_compute_operation_description', readonly=False)
    days = fields.Integer('Expected Duration (Days)')
    minutes = fields.Float('Expected Duration (Minutes)')
    notes = fields.Text('Procedural Notes')


    # Relational Fields

    cultivar_bom_id = fields.Many2one('cultivar.bom', 'Cultivar Profile', readonly=True)
    cultivar_stages = fields.Many2one('cultivar.stages', 'Cultivar Stages', readonly=True)
    system_parent_id = fields.Many2one('system.specifications', 'Parent System', readonly=True)
    system_id = fields.Many2one('system.specifications', 'Location', required=True)
    users_id = fields.Many2one('res.users', 'User')

    @api.onchange('stage')
    def _compute_duration_category(self):
        for rec in self:
            if rec.stage == 'growout':
                rec.duration_category = 'passive'
            elif rec.stage == 'germination':
                rec.duration_category = 'passive'
            elif rec.stage == 'harvest':
                rec.duration_category = 'harvest'
            elif rec.stage != 'growout' or 'harvest':
                rec.duration_category = 'labor'
            elif rec.stage == False:
                rec.duration_category = False

    @api.depends('stage')
    def _compute_operation_description(self):
        for rec in self:
            if rec.stage == 'germination':
                rec.description = 'Keep Seeds Covered & Soaked'
            elif rec.stage == 'growout':
                rec.description = "Passive grow period for the cultivar"
            elif rec.stage != 'growout' or 'harvest':
                rec.description = 'Employee Task'


