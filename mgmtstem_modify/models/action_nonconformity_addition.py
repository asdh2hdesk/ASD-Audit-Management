from odoo import fields, models, api

class MgmtsystemNonconformity(models.Model):
    _inherit = "mgmtsystem.nonconformity"
    
    audit_id = fields.Many2one('mgmtsystem.audit', string='Audit')
    closing_date = fields.Datetime(readonly=True, string="Actual Closed Date")
    department_id = fields.Many2one(
        'hr.department',
        string='User Department',
        help="Department the auditor belongs to"
    )
    target_date = fields.Date(
        string='Target Date',
        help="Target date for the nonconformity resolution"
    )
    number_of_days_to_open = fields.Integer(
        "# of days to open",
        compute="_compute_number_of_days_to_open",
        store=True,
        readonly=True,
    )
    
    nc_type = fields.Selection(
        selection=[
            ('major', 'Major Nonconformity'),
            ('minor', 'Minor Nonconformity'),
        ],
        string='Nonconformity Type',
        help='Type of nonconformity identified'
    )

    @api.depends('create_date', 'target_date')
    def _compute_number_of_days_to_open(self):
        for record in self:
            if record.create_date and record.target_date:
                record.number_of_days_to_open = (record.target_date - record.create_date.date()).days
            else:
                record.number_of_days_to_open = 0
                
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            responsible_user = self.env['res.users'].browse(vals.get('responsible_user_id'))
            vals['department_id'] = responsible_user.department_id.id if responsible_user.department_id else False
        return super().create(vals_list)

    def write(self, vals):
        if 'responsible_user_id' in vals:
            responsible_user = self.env['res.users'].browse(vals.get('responsible_user_id'))
            vals['department_id'] = responsible_user.department_id.id if responsible_user.department_id else False
        return super().write(vals)
    

class MgmtsystemAction(models.Model):
    _inherit = "mgmtsystem.action"
    
    audit_id = fields.Many2one('mgmtsystem.audit', string='Audit')
    date_closed = fields.Datetime(readonly=True, string="Actual Closed Date")
    department_id = fields.Many2one(
        'hr.department',
        string='User Department',
        compute="_compute_department_id",
        store=True,
        help="Department the auditor belongs to"
    )
    target_date = fields.Date(
        string='Target Date',
        help="Target date for the nonconformity resolution"
    )
    
    @api.depends('user_id')
    def _compute_department_id(self):
        for record in self:
            user = self.env['res.users'].browse(record.user_id.id)
            record.department_id = user.department_id.id if user.department_id else False
            
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            user = self.env['res.users'].browse(vals.get('user_id'))
            vals['department_id'] = user.department_id.id if user.department_id else False
        return super().create(vals_list)

    def write(self, vals):
        if 'user_id' in vals:
            user = self.env['res.users'].browse(vals.get('user_id'))
            vals['department_id'] = user.department_id.id if user.department_id else False
        return super().write(vals)