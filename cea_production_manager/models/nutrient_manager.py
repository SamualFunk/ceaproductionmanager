from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class additives_manager(models.Model):
    _name = "additives.manager"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Additives & Fertilizer Manager"

    # ---Core Fields---

    name = fields.Char('Recipe Name')
    date = fields.Datetime('Date Created')
    symbol = fields.Char('Symbol')
    atomic_weight = fields.Float('Atomic Weight', readonly=False, related='element_relation_id.total_atomic_mass')
    molecular_weight = fields.Float('Molecular Weight', related='fertilizer_salt_profile_id.molecular_weight')
    formula = fields.Char('Formula', related='fertilizer_salt_profile_id.formula')
    target_ppm = fields.Float('Target PPM')
    mg_liter = fields.Float('mg/L')
    ppm = fields.Float('ppm')
    purity = fields.Float('Purity', related='fertilizer_salt_profile_id.purity')
    solve_mg_liter = fields.Boolean('Solve For mg/l', compute='_compute_mg_liter_boolean', readonly=False, default=True,
                                    stored=True)
    solve_ppm = fields.Boolean('Solve For PPM', compute='_compute_ppm_boolean', readonly=False, stored=True)
    element_name = fields.Char('Element Symbol', related='element_relation_id.symbol')
    concentration = fields.Integer('Concentration(x)')
    water_quantity = fields.Integer('Water Quantity')
    water_units = fields.Selection([
        ('gallons', 'Gallons'),
        ('liters', 'Liters'),
    ],
        string='Units')

    # --Relational--

    salt_id = fields.One2many('salt.consumption', 'recipe_id')
    element_quantity_id = fields.One2many('element.quantity', 'recipe_id')
    fertilizer_salt_profile_id = fields.Many2one('fertilizer.salt.profile')
    element_relation_id = fields.Many2one(
        'element.profile',
        compute='_compute_element_relation',
        string='Element Relation',
        readonly=False,
        store=True,
        domain="[('used_in_id', '=', fertilizer_salt_profile_id)]"
    )

    # --Computation--

    @api.depends('fertilizer_salt_profile_id')
    def _compute_element_relation(self):
        for rec in self:
            if rec.fertilizer_salt_profile_id:
                domain = [('used_in_id', '=', rec.fertilizer_salt_profile_id.id)]
                rec.element_relation_id = self.env['element.profile'].search(domain, limit=1)
            else:
                rec.element_relation_id = False

    @api.onchange('solve_mg_liter')
    def _compute_mg_liter_boolean(self):
        for rec in self:
            if rec.solve_mg_liter:
                rec.solve_ppm = False

    @api.onchange('solve_ppm')
    def _compute_ppm_boolean(self):
        for rec in self:
            if rec.solve_ppm:
                rec.solve_mg_liter = False

    # --Button Actions--
    @api.model
    def create(self, vals):
        if 'fertilizer_salt_profile_id' in vals:
            profile_id = vals['fertilizer_salt_profile_id']
            profile = self.env['fertilizer.salt.profile'].browse(profile_id)
            if profile.elements_id:
                vals['element_relation_id'] = profile.elements_id[0].id
        return super(additives_manager, self).create(vals)

    def action_compute_mg_liter(self):
        for rec in self:
            rec.mg_liter = (rec.molecular_weight * rec.ppm) / rec.atomic_weight

    def action_compute_ppm(self):
        for rec in self:
            rec.ppm = (rec.atomic_weight * rec.mg_liter) / rec.molecular_weight

    def action_log_additions(self):
        for rec in self:
            if rec.name:
                existing_record = rec.element_quantity_id.filtered(lambda eq: eq.name == rec.element_name)
                if existing_record:
                    existing_record.mg_added += rec.mg_liter
                    existing_record.ppm_added += rec.ppm
                else:
                    element_data = {
                        'name': rec.element_relation_id.element_selection,
                        'symbol': rec.element_name,
                        'salt': rec.fertilizer_salt_profile_id.formula,
                        'target_ppm': rec.target_ppm,
                        'mg_added': rec.mg_liter,
                        'ppm_added': rec.ppm,
                        'recipe_id': rec.id,
                        'purity': rec.purity,
                    }
                    rec.element_quantity_id.create(element_data)


class salt_consumption(models.Model):
    _name = 'salt.consumption'
    _description = 'Fertilizer Recipe Listing & Consumption'

    # --Core--

    quantity = fields.Float('mg/Liter')
    formula = fields.Char('Formula', related='salt_id.formula')
    molecular_weight = fields.Float('Molecular Weight', related='salt_id.molecular_weight')
    adjusted_quantity = fields.Float('Adjusted Quantity', compute='_compute_final_quantity')
    unit_of_measure = fields.Selection(selection=[
        ('g', 'g'),
        ('mg', 'mg'),
        ('kg', 'kg'),
    ],
        string='Unit',
    )
    concentration = fields.Integer('Concentration', related='recipe_id.concentration')
    water_quantity = fields.Integer('Water Quantity', related='recipe_id.water_quantity')
    water_units = fields.Selection([
        ('gallons', 'Gallons'),
        ('liters', 'Liters'),
    ],
        string='Units',
        related='recipe_id.water_units',
        default='gallons')
    solubility = fields.Float('Solubility g/100ml', related='salt_id.solubility')
    solubility_levels = fields.Float('Quantity g/100ml', compute='_compute_solubility_levels')


    # --Relational--

    salt_id = fields.Many2one('fertilizer.salt.profile', required=True)
    recipe_id = fields.Many2one('additives.manager', 'salt_id')

    @api.depends('quantity')
    def _compute_final_quantity(self):
        for rec in self:
            if rec.quantity:
                if rec.water_units == 'gallons':
                    rec.adjusted_quantity = (rec.quantity * rec.concentration) * 3.785 * rec.water_quantity
                elif rec.water_units == 'liters':
                    rec.adjusted_quantity = (rec.quantity * rec.concentration) * rec.water_quantity
                if rec.adjusted_quantity >= 1000000:
                    rec.adjusted_quantity = rec.adjusted_quantity / 1000000
                    rec.unit_of_measure = 'kg'
                elif rec.adjusted_quantity >= 1000:
                    rec.adjusted_quantity = rec.adjusted_quantity / 1000
                    rec.unit_of_measure = 'g'
                else:
                    rec.unit_of_measure = 'mg'
            else:
                rec.adjusted_quantity = None

    @api.depends('quantity')
    def _compute_solubility_levels(self):
        for rec in self:
            if rec.quantity:
                rec.solubility_levels = rec.quantity * rec.concentration / 10000
            else:
                rec.solubility_levels = None


class fertilizer_salt_profile(models.Model):
    _name = 'fertilizer.salt.profile'
    _inherit = 'mail.thread'
    _description = 'Fertilizer Salt Profile'

    # --Core--

    description = fields.Text('Description')
    molecular_weight = fields.Float('Molecular Weight', compute='_compute_molecular_weight', readonly=False)
    molecular_weight_override = fields.Float('Molecular Weight')
    formula = fields.Char('Formula')
    override = fields.Boolean('Molecular Weight Override')
    purity = fields.Float('Purity')
    solubility = fields.Float('Solubility')

    # --Relational--

    vendor = fields.Many2one('res.partner')
    elements_id = fields.One2many('element.profile', 'used_in_id')
    product_id = fields.Many2one('product.product', 'Product')

    def name_get(self):
        result = []
        for rec in self:
            name = rec.product_id.name
            result.append((rec.id, name))
        return result

    @api.depends('override', 'elements_id')
    def _compute_molecular_weight(self):
        for rec in self:
            if not rec.override:
                total_weight = 0.0
                for element in rec.elements_id:
                    total_weight += element.total_atomic_mass
                rec.molecular_weight = total_weight
            elif rec.override:
                rec.molecular_weight = rec.molecular_weight_override


class element_profile(models.Model):
    _name = 'element.profile'
    _description = 'Element List With Amounts & Atomic Weight'

    # --Core--

    element_selection = fields.Selection(selection=[
        ('hydrogen', 'Hydrogen'),
        ('oxygen', 'Oxygen'),
        ('nitrogen', 'Nitrogen'),
        ('phosphorus', 'Phosphorus'),
        ('potassium', 'Potassium'),
        ('calcium', 'Calcium'),
        ('magnesium', 'Magnesium'),
        ('sulfur', 'Sulfur'),
        ('iron', 'Iron'),
        ('manganese', 'Manganese'),
        ('zinc', 'Zinc'),
        ('copper', 'Copper'),
        ('boron', 'Boron'),
        ('molybdenum', 'Molybdenum'),
        ('chlorine', 'Chlorine'),
        ('nickel', 'Nickel'),
        ('silicon', 'Silicon'),
        ('cobalt', 'Cobalt'),
        ('selenium', 'Selenium'),
        ('vanadium', 'Vanadium'),
        ('sodium', 'Sodium'),
        ('carbon', 'Carbon'),
    ],
        string='Elements', )

    ref = fields.Char('Reference', default=lambda self: _('New'), readonly=True)
    name = fields.Char('Name', compute='_compute_name')
    symbol = fields.Char('Element Symbol', compute='_compute_element_symbol_weight')
    atomic_weight = fields.Float('Atomic Weight', compute='_compute_element_symbol_weight')
    total_atomic_mass = fields.Float('Total Atomic Weight', compute='_compute_total_atomic_mass')
    amount_present = fields.Integer('Amount Present')

    # --Relational--

    used_in_id = fields.Many2one('fertilizer.salt.profile')

    @api.depends('amount_present')
    def _compute_total_atomic_mass(self):
        for rec in self:
            if rec.amount_present:
                rec.total_atomic_mass = rec.atomic_weight * rec.amount_present
            else:
                rec.total_atomic_mass = None

    @api.depends('element_selection')
    def _compute_element_symbol_weight(self):

        element_data = {
            'hydrogen': ['Hydrogen', 1.00, 'H'],
            'oxygen': ['Oxygen', 15.99, 'O'],
            'nitrogen': ['Nitrogen', 14.00, 'N'],
            'phosphorus': ['Phosphorus', 30.97, 'P'],
            'potassium': ['Potassium', 39.10, 'K'],
            'calcium': ['Calcium', 40.08, 'Ca'],
            'magnesium': ['Magnesium', 24.31, 'Mg'],
            'sulfur': ['Sulfur', 32.07, 'S'],
            'iron': ['Iron', 55.85, 'Fe'],
            'manganese': ['Manganese', 54.94, 'Mn'],
            'zinc': ['Zinc', 65.38, 'Zn'],
            'copper': ['Copper', 63.55, 'Cu'],
            'boron': ['Boron', 10.81, 'B'],
            'molybdenum': ['Molybdenum', 95.95, 'Mo'],
            'chlorine': ['Chlorine', 35.45, 'Cl'],
            'nickel': ['Nickel', 58.69, 'Ni'],
            'silicon': ['Silicon', 28.09, 'Si'],
            'cobalt': ['Cobalt', 58.93, 'Co'],
            'selenium': ['Selenium', 78.96, 'Se'],
            'vanadium': ['Vanadium', 50.94, 'V'],
            'sodium': ['Sodium', 22.99, 'Na'],
            'carbon': ['Carbon', 12.01, 'C'],
        }

        for rec in self:
            if rec.element_selection in element_data:
                selected_element = element_data[rec.element_selection]
                rec.symbol = selected_element[2]
                rec.atomic_weight = selected_element[1]
            else:
                rec.symbol = None
                rec.atomic_weight = None

    @api.depends('element_selection')
    def _compute_name(self):
        for rec in self:
            if rec.element_selection:
                rec.name = rec.element_selection
            else:
                rec.name = None

    def name_get(self):
        result = []
        for rec in self:
            name = rec.element_selection[0].upper() + rec.element_selection[1:]
            result.append((rec.id, name))
        return result


class element_quantity(models.Model):
    _name = 'element.quantity'
    _description = 'Notepad List For Element Additions & Adjustments'

    # --Core--
    name = fields.Char('Name')
    salt = fields.Char('Salt')
    symbol = fields.Char('Symbol')
    target_ppm = fields.Float('PPM Required')
    ppm_added = fields.Float('PPM')
    mg_added = fields.Float('mg/L')
    ppm_needed = fields.Float('PPM Remaining', compute='_compute_ppm_needed', readonly=False)
    purity = fields.Float('Purity')
    purity_adjustment = fields.Float('Adjustment For Purity', compute='_compute_purity_adjustment')

    # --Relational--

    recipe_id = fields.Many2one('additives.manager')

    # --Computation--

    @api.depends('ppm_added', 'target_ppm')
    def _compute_ppm_needed(self):
        for rec in self:
            if rec.ppm_added:
                rec.ppm_needed = rec.target_ppm - rec.ppm_added
            else:
                rec.ppm_needed = None

    @api.onchange('purity')
    def _compute_purity_adjustment(self):
        for rec in self:
            if rec.purity:
                rec.purity_adjustment = rec.mg_added / rec.purity
            else:
                rec.purity_adjustment = None
