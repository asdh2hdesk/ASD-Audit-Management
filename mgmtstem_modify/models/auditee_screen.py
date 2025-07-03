from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MgmtsystemAuditAuditee(models.Model):
    """Model to manage audit auditees."""
    _name = "mgmtsystem.audit.auditee"
    _description = "Audit Auditee"

    audit_id = fields.Many2one('mgmtsystem.audit', string='Audit')
    user_id = fields.Many2one('res.users', string='User')
    name = fields.Char(related='user_id.name', string='Name', store=True)
    login = fields.Char(related='user_id.login', string='Login', store=True)
    lang = fields.Selection(related='user_id.lang', string='Language', store=True)
    login_date = fields.Datetime(related='user_id.login_date', string='Latest Connection', store=True)
    department_ids = fields.Many2many('hr.department', string='Department to Audit')

    department_id = fields.Many2one(
        'hr.department',
        string='User Department',
        help="Department the auditee belongs to"
    )

    @api.model
    def _get_lang(self):
        return self.env['res.lang'].get_installed()

    @api.onchange('user_id')
    def _onchange_user_id(self):
        """Update fields when user is selected"""
        if self.user_id:
            self.name = self.user_id.name
            self.login = self.user_id.login
            self.lang = self.user_id.lang
            self.login_date = self.user_id.login_date
            
            # Get department from employee record
            employee = self.env['hr.employee'].sudo().search([
                ('user_id', '=', self.user_id.id)
            ], limit=1)
            
            if employee and employee.department_id:
                self.department_id = employee.department_id.id
                # Clear any selected departments that match the user's department
                if self.department_ids:
                    self.department_ids = self.department_ids.filtered(
                        lambda d: d.id != self.department_id.id
                    )

    @api.onchange('department_id')
    def _onchange_department_id(self):
        """Remove user's department from department_ids if selected"""
        if self.department_id and self.department_ids:
            self.department_ids = self.department_ids.filtered(
                lambda d: d.id != self.department_id.id
            )

    @api.constrains('department_id', 'department_ids')
    def _check_departments(self):
        """Ensure user's department is not in departments to audit"""
        for record in self:
            if record.department_id and record.department_ids:
                if record.department_id.id in record.department_ids.ids:
                    raise ValidationError(_("Auditee cannot be audited in their own department"))

    def write(self, vals):
        """Override write to sync changes to res.users"""
        res = super().write(vals)
        
        # Fields to sync with res.users
        fields_to_sync = ['name', 'login', 'lang']
        
        # Prepare values to update in res.users
        user_vals = {}
        for field in fields_to_sync:
            if field in vals:
                user_vals[field] = vals[field]
        
        # Update the corresponding user if there are values to sync
        if user_vals:
            for record in self:
                if record.user_id:
                    record.user_id.sudo().write(user_vals)
        
        return res

    @api.model
    def create(self, vals):
        """Override create to sync values to res.users"""
        record = super().create(vals)
        
        # Fields to sync with res.users
        fields_to_sync = ['name', 'login', 'lang']
        
        # Prepare values to update in res.users
        user_vals = {}
        for field in fields_to_sync:
            if field in vals:
                user_vals[field] = vals[field]
        
        # Update the corresponding user if there are values to sync
        if user_vals and record.user_id:
            record.user_id.sudo().write(user_vals)
            
        # Set department from employee if not already set
        if record.user_id and not record.department_id:
            employee = record.env['hr.employee'].sudo().search([
                ('user_id', '=', record.user_id.id)
            ], limit=1)
            
            if employee and employee.department_id:
                record.department_id = employee.department_id.id
            
        return record
    
class MgmtsystemAudit(models.Model):
    _inherit = "mgmtsystem.audit"

    auditees_user_ids = fields.One2many(
        'mgmtsystem.audit.auditee',
        'audit_id',
        string='Auditees'
    )
    
    
class MgmtsystemAuditAuditor(models.Model):
    _inherit = "mgmtsystem.audit.auditor"
    
    selected_user_ids = fields.Many2many(
        'res.users',
        'auditor_selected_users_rel',
        'auditor_id',
        'user_id',
        string='Select Auditees',
        domain=lambda self: [('id', '!=', self.env.uid)],
        store=True
    )
    
    certified_date = fields.Date(
        string='Certification Date',
        help="Date when the auditor was certified",
        compute='_compute_certification_dates',
        store=True,
        inverse='_inverse_certification_dates'
    )
    expiry_date = fields.Date(
        string='Certification Expiry Date',
        help="Date when the auditor certification expires",
        compute='_compute_certification_dates',
        store=True,
        inverse='_inverse_certification_dates'
    )
    
    @api.depends('user_id')
    def _compute_certification_dates(self):
        """Compute certification dates from employee record"""
        for record in self:
            employee = self.env['hr.employee'].sudo().search([
                ('user_id', '=', record.user_id.id)
            ], limit=1)
            
            if employee:
                record.certified_date = employee.certification_date
                record.expiry_date = employee.certification_expiry_date
            else:
                record.certified_date = False
                record.expiry_date = False

    def _inverse_certification_dates(self):
        """Update employee record when certification dates change"""
        for record in self:
            employee = self.env['hr.employee'].sudo().search([
                ('user_id', '=', record.user_id.id)
            ], limit=1)
            
            if employee:
                employee.sudo().write({
                    'certification_date': record.certified_date,
                    'certification_expiry_date': record.expiry_date,
                })

    @api.onchange('user_id')
    def _onchange_user_id(self):
        """Update certification dates when user changes"""
        super()._onchange_user_id()  # Call existing onchange
        
        if self.user_id:
            employee = self.env['hr.employee'].sudo().search([
                ('user_id', '=', self.user_id.id)
            ], limit=1)
            
            if employee:
                self.certified_date = employee.certification_date
                self.expiry_date = employee.certification_expiry_date

    @api.constrains('selected_user_ids', 'user_id')
    def _check_selected_users(self):
        """Ensure users cannot select themselves as auditees"""
        for record in self:
            if record.user_id.id in record.selected_user_ids.ids:
                raise ValidationError("You cannot select yourself as an auditee.")
    @api.model
    def create(self, vals):
        """Override create to sync selected users to audit"""
        record = super(MgmtsystemAuditAuditor, self).create(vals)
        if record.selected_user_ids:
            record._sync_users_to_audit()
        return record

    def write(self, vals):
        """Override write to sync selected users to audit"""
        res = super(MgmtsystemAuditAuditor, self).write(vals)
        if 'selected_user_ids' in vals:
            for record in self:
                record._sync_users_to_audit()
        return res

    def _sync_users_to_audit(self):
        """Sync selected users to the audit's auditees_user_ids"""
        for record in self:
            if record.audit_id and record.selected_user_ids:
                existing_auditees = record.audit_id.auditees_user_ids.mapped('user_id')
                
                # Create new auditee records for selected users
                for user in record.selected_user_ids:
                    if user not in existing_auditees:
                        # Get employee record to fetch department
                        employee = self.env['hr.employee'].sudo().search([
                            ('user_id', '=', user.id)
                        ], limit=1)
                        
                        # Create new auditee record
                        self.env['mgmtsystem.audit.auditee'].create({
                            'audit_id': record.audit_id.id,
                            'user_id': user.id,
                            'department_id': employee.department_id.id if employee else False,
                        })