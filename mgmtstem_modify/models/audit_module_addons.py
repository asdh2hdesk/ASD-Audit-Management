from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class AuditsystemStrongLine(models.Model):
    """Class to manage strong point's Line."""

    _name = "strong.point.line"
    _description = "Strong Point Line"
    _order = "seq"

    name = fields.Char("Name")
    seq = fields.Integer("Sequence")
    clause = fields.Char(
        string='Clause',
        help='Reference clause or section number'
    )

    checkpoints = fields.Text(
        string='Checkpoints',
        help='Verification checkpoints or requirements to be verified'
    )
    observations = fields.Text(
        string='Observations/Findings',
        help='Detailed observations and findings during verification'
    )
    audit_id = fields.Many2one('mgmtsystem.audit', string='Audit')
    
    
    
class AuditsystemToImproveLine(models.Model):
    """Class to manage point's to improve Line."""

    _name = "to.improve.point.line"
    _description = "To Improve Point Line"
    _order = "seq"

    name = fields.Char("Name")
    seq = fields.Integer("Sequence")
    clause = fields.Char(
        string='Clause',
        help='Reference clause or section number'
    )

    checkpoints = fields.Text(
        string='Checkpoints',
        help='Verification checkpoints or requirements to be verified'
    )
    observations = fields.Text(
        string='Observations/Findings',
        help='Detailed observations and findings during verification'
    )
    
    status =  fields.Selection(string='Status',
        selection=[
            ('to_be_started', 'To be started'),
            ('in_progress', 'In progress'),
            ('completed', 'Completed'),
        ],
        help='Current status of the verification line'
    )
    audit_id = fields.Many2one('mgmtsystem.audit', string='Audit')
    
    
class MgmtsystemAction(models.Model):
    _inherit = "mgmtsystem.action"

    type_action = fields.Selection(
        [
            ("none", " "),
            ("immediate", "Immediate Action"),
            ("correction", "Corrective Action"),
            ("prevention", "Preventive Action"),
            ("improvement", "Improvement Opportunity"),
        ],
        "Response Type",
        required=True,
        default="none",
    )
    
    audited_department_id = fields.Many2one(
        'hr.department',
        string='Audited Department',
        help="Department related to this action"
    )
    
    def get_action_url(self):
        """Return action url to be used in email templates."""
        base_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url") or "http://localhost:8069"
        )
        url = ("{}/web#db={}&id={}&model={}").format(
            base_url, self.env.cr.dbname, self.id, self._name
        )
        return url
    
    
class MgmtsystemNonconformity(models.Model):
    _inherit = "mgmtsystem.nonconformity"

    description = fields.Html()
    audited_department_id = fields.Many2one(
        'hr.department',
        string='Audited Department',
        help="Department where the nonconformity was identified"
    )

class MgmtsystemAudit(models.Model):
    """Model class that manage audit."""

    _inherit = "mgmtsystem.audit"
    
    date = fields.Datetime("Date", default=fields.Datetime.now)
    line_ids = fields.One2many(
        "mgmtsystem.verification.line", "audit_id", "Verification List"
    )

    strong_points_ids = fields.One2many(
        "strong.point.line", "audit_id", "Strong Points"
    )
    
    to_improve_points_ids = fields.One2many(
        "to.improve.point.line", "audit_id", "To Improve Points"
    )
    
    auditors_user_ids = fields.One2many(
        'mgmtsystem.audit.auditor',
        'audit_id',
        string='Auditors'
    )
    state = fields.Selection([
        ('open', 'To Be Started'),
        ('in_progress', 'In Progress'),
        ('waiting_approval', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('done', 'Closed')
    ], default='open', required=True, string='Status')
    
    revision_date = fields.Date(string="Revision Date")
    
    revision_data = fields.Text(string="Revision Data", store=True)

    @api.model
    def create(self, vals):
        """Override create method"""
        res = super(MgmtsystemAudit, self).create(vals)
        if vals.get('line_ids'):
            # self._sync_new_lines_to_system(res)
            self._handle_verification_data(res, vals)
        return res

    def write(self, vals):
        """Override write method"""
        res = super(MgmtsystemAudit, self).write(vals)
        if vals.get('line_ids'):
            # self._sync_new_lines_to_system(self)
            self._handle_verification_data(self, vals)
        return res

    def _handle_verification_data(self, record, vals):
        """Handle all verification line related operations"""
        if vals.get('line_ids'):
            self._sync_strong_points(record)
            self._sync_improve_points(record)
            self._sync_nonconformities(record)

    def _sync_nonconformities(self, audit):
        """Sync nonconformities from verification lines"""
        for line in audit.line_ids:
            if line.criteria in ['major_nc', 'minor_nc']:
                # Check if nonconformity already exists for this verification line
                existing_nc = self.env['mgmtsystem.nonconformity'].search([
                    ('name', '=', audit.reference),
                    ('description', 'ilike', f'Clause: {line.clause}'),
                    ('description', 'ilike', f'Checkpoints: {line.checkpoints}'),
                    ('description', 'ilike', f'Observations: {line.observations}')
                ], limit=1)
                
                # Determine nc_type based on criteria
                    
                if not existing_nc:
                    # Prepare description without HTML tags
                    description = f"""
                    <p><strong>Clause:</strong> {line.clause or ''}</p>
                    <p><strong>Checkpoints:</strong> {line.checkpoints or ''}</p>
                    <p><strong>Department:</strong> {line.department_id.name if line.department_id else ''}</p>
                    <p><strong>Observations/Findings:</strong> {line.observations or ''}</p>
                    <p><strong>Procedure:</strong> {line.procedure_id.name if line.procedure_id else ''}</p>
                    <p><strong>Format Number:</strong> {line.format_number_ids.format_number if line.format_number_ids else ''}</p>
                    <p><strong>Type:</strong> {dict(line._fields['criteria'].selection).get(line.criteria)}</p>
                    """
                    
                    
                    nc_type = 'major' if line.criteria == 'major_nc' else 'minor'

                    # Create nonconformity
                    nc_vals = {
                        'name': audit.reference,
                        'description': description,
                        'nc_type': nc_type,
                        'system_id': audit.system_id.id if audit.system_id else False,  # Get system_id from audit
                        'user_id': self.env.user.id,
                        'manager_user_id': audit.user_id.id if audit.user_id else self.env.user.id,
                        'responsible_user_id': audit.user_id.id if audit.user_id else self.env.user.id,
                        'partner_id': self.env.company.partner_id.id,
                        'audit_id': audit.id,
                        'audited_department_id': line.department_id.id if line.department_id else False,
                        # 'audit_ids': [(4, audit.id)],
                    }

                    # Add procedure if specified
                    if line.procedure_id:
                        nc_vals['procedure_ids'] = [(4, line.procedure_id.id)]

                    # Create nonconformity record
                    self.env['mgmtsystem.nonconformity'].create(nc_vals)
                        
    def _sync_strong_points(self, audit):
        """Sync strong points from verification lines"""
        for line in audit.line_ids:
            if line.criteria == 'strong_point':
                existing_strong_point = audit.strong_points_ids.filtered(
                    lambda x: x.clause == line.clause and 
                                x.checkpoints == line.checkpoints and
                                x.observations == line.observations
                )
                if not existing_strong_point:
                    self.env['strong.point.line'].create({
                        'name': f"Strong Point - {line.clause or ''}", 
                        'seq': len(audit.strong_points_ids) + 1,
                        'clause': line.clause,
                        'checkpoints': line.checkpoints,
                        'observations': line.observations,
                        'audit_id': audit.id,
                    })

    def _sync_improve_points(self, audit):
        """Sync points to improve from verification lines"""
        for line in audit.line_ids:
            if line.criteria == 'to_improve_points':
                existing_improve_point = audit.to_improve_points_ids.filtered(
                    lambda x: x.clause == line.clause and 
                            x.checkpoints == line.checkpoints and
                            x.observations == line.observations
                )
                if not existing_improve_point:
                    # Create to improve point
                    improve_point = self.env['to.improve.point.line'].create({
                        'name': f"To Improve Point - {line.clause or ''}", 
                        'seq': len(audit.to_improve_points_ids) + 1,
                        'clause': line.clause,
                        'checkpoints': line.checkpoints,
                        'observations': line.observations,
                        'status': line.status,
                        'audit_id': audit.id,
                    })
                    
                    # Generate action reference
                    action_reference = self.env['ir.sequence'].next_by_code('mgmtsystem.action') or 'New'
                    # Create action name in the format: reference - audit_reference - audit_id
                    action_name = f"{action_reference} - {audit.reference} - {audit.name}"
                    
                    # Check if action already exists for this observation
                    existing_action = self.env['mgmtsystem.action'].search([
                        ('name', '=', action_name),
                        ('type_action', '=', 'improvement')
                    ], limit=1)
                    
                    # Create action only if it doesn't exist
                    if not existing_action:
                        self.env['mgmtsystem.action'].create({
                            'name': action_name,
                            'type_action': 'improvement',
                            'description': f"""
                                <p><strong>Clause:</strong> {line.clause or ''}</p>
                                <p><strong>Checkpoints:</strong> {line.checkpoints or ''}</p>
                                <p><strong>Observations:</strong> {line.observations or ''}</p>
                            """,
                            'reference': action_reference,
                            'system_id': audit.system_id.id if hasattr(audit, 'system_id') else False,
                            'audit_id': audit.id,
                            'audited_department_id': line.department_id.id if line.department_id else False,
                        })


    
class MgmtsystemAuditAuditor(models.Model):
    """Model to manage audit auditors."""
    _name = "mgmtsystem.audit.auditor"
    _description = "Audit Auditor"

    audit_id = fields.Many2one('mgmtsystem.audit', string='Audit')
    audit_ref = fields.Char(related='audit_id.reference', string='Audit Reference', store=True)
    user_id = fields.Many2one('res.users', string='User')
    target_date = fields.Date(string='Target Date For Audit')
    name = fields.Char(related='user_id.name', string='Name', store=True)
    login = fields.Char(related='user_id.login', string='Login', store=True)
    lang = fields.Selection(related='user_id.lang', string='Language', store=True)
    login_date = fields.Datetime(related='user_id.login_date', string='Latest Connection', store=True)
    department_ids = fields.Many2many('hr.department', string='Department to Audit')

    department_id = fields.Many2one(
        'hr.department',
        string='User Department',
        help="Department the auditor belongs to"
    )

    certified_date = fields.Date(
        string='Certification Date',
        help="Date when the auditor was certified"
    )
    expiry_date = fields.Date(
        string='Certification Expiry Date',
        help="Date when the auditor certification expires"
    )
    
    deprtmnt_id = fields.Many2one(
        'hr.department',
        string='Select Department',
        help="Show Department Wise Verification Lists for the auditor belongs to",
        domain="[('id', 'in', department_ids)]",
        readonly=False,
    )

    filtered_line_ids = fields.One2many(
        'mgmtsystem.verification.line','auditor_id',
        compute='_compute_filtered_line_ids',
        string='Department Verification Lines',
        readonly=False, 
    )
    
    # Add boolean field to track if filter is active
    is_department_filtered = fields.Boolean(
        string='Department Filter Active',
        default=False,
        help='Shows if department filter is currently active'
    )
    
    auditee_ids = fields.Many2many(
        'mgmtsystem.audit.auditee',
        'auditor_auditee_rel',
        'auditor_id',
        'auditee_id',
        string='Auditees',
        compute='_compute_auditee_ids',
        store=True,
    )
    
    last_tuv_audit_obs = fields.Text(string='Last TUV Audit Observations/NC', store=True )
    last_customer_audit_obs = fields.Text(string='Last Customer Audit Observations/NC', store=True)
    last_internal_ims_audit_obs = fields.Text(string='Last Internal IMS Audit Observations/NC', store=True)

    @api.model
    def _get_lang(self):
        return self.env['res.lang'].get_installed()
    
    
    @api.constrains('target_date')
    def _check_target_date(self):
        """Ensure target date is not in the past"""
        today = fields.Date.today()
        for record in self:
            if record.target_date and record.target_date < today:
                raise ValidationError(_('Target Date cannot be in the past.'))

    @api.onchange('target_date')
    def _onchange_target_date(self):
        """Warning if target date is in the past"""
        today = fields.Date.today()
        if self.target_date and self.target_date < today:
            return {
                'warning': {
                    'title': _('Invalid Date'),
                    'message': _('Target Date cannot be in the past.')
                }
            }
    
    @api.constrains('department_ids')
    def _check_single_department(self):
        for record in self:
            if len(record.department_ids) > 1:
                raise ValidationError(_('You can only select one department at a time. (In Department to Audit) '))
    
    @api.depends('audit_id')
    def _compute_auditee_ids(self):
        """Compute method to get auditees from the audit"""
        for record in self:
            if record.audit_id:
                record.auditee_ids = record.audit_id.auditees_user_ids
            else:
                record.auditee_ids = [(5, 0, 0)]
    
    def _sync_strong_points(self, line):
        """Sync strong points from verification lines"""
        if line.criteria == 'strong_point':
            existing_strong_point = self.audit_id.strong_points_ids.filtered(
                lambda x: x.clause == line.clause and 
                        x.checkpoints == line.checkpoints and
                        x.observations == line.observations
            )
            if not existing_strong_point:
                self.env['strong.point.line'].create({
                    'name': f"Strong Point - {line.clause or ''}", 
                    'seq': len(self.audit_id.strong_points_ids) + 1,
                    'clause': line.clause,
                    'checkpoints': line.checkpoints,
                    'observations': line.observations,
                    'audit_id': self.audit_id.id,
                })

    def _sync_improve_points(self, line):
        """Sync points to improve from verification lines"""
        if line.criteria == 'to_improve_points':
            existing_improve_point = self.audit_id.to_improve_points_ids.filtered(
                lambda x: x.clause == line.clause and 
                        x.checkpoints == line.checkpoints and
                        x.observations == line.observations
            )
            if not existing_improve_point:
                # Create to improve point
                improve_point = self.env['to.improve.point.line'].create({
                    'name': f"To Improve Point - {line.clause or ''}", 
                    'seq': len(self.audit_id.to_improve_points_ids) + 1,
                    'clause': line.clause,
                    'checkpoints': line.checkpoints,
                    'observations': line.observations,
                    'status': line.status,
                    'audit_id': self.audit_id.id,
                })
                
                # Generate action reference
                action_reference = self.env['ir.sequence'].next_by_code('mgmtsystem.action') or 'New'
                # Create action name in the format: reference - audit_reference - audit_id
                action_name = f"{action_reference} - {self.audit_id.reference} - {self.audit_id.name}"
                
                # Check if action already exists for this observation
                existing_action = self.env['mgmtsystem.action'].search([
                    ('name', '=', action_name),
                    ('type_action', '=', 'improvement')
                ], limit=1)
                
                # Create action only if it doesn't exist
                if not existing_action:
                    self.env['mgmtsystem.action'].create({
                        'name': action_name,
                        'type_action': 'improvement',
                        'description': f"""
                            <p><strong>Clause:</strong> {line.clause or ''}</p>
                            <p><strong>Checkpoints:</strong> {line.checkpoints or ''}</p>
                            <p><strong>Observations:</strong> {line.observations or ''}</p>
                        """,
                        'reference': action_reference,
                        'system_id': self.audit_id.system_id.id if hasattr(self.audit_id, 'system_id') else False,
                        'audit_id': self.audit_id.id,
                        'audited_department_id': line.department_id.id if line.department_id else False,
                    })

    def _sync_nonconformities(self, line):
        """Sync nonconformities from verification lines"""
        if line.criteria in ['major_nc', 'minor_nc']:
            # Check if nonconformity already exists for this verification line
            existing_nc = self.env['mgmtsystem.nonconformity'].search([
                ('name', '=', self.audit_id.reference),
                ('description', 'ilike', f'Clause: {line.clause}'),
                ('description', 'ilike', f'Checkpoints: {line.checkpoints}'),
                ('description', 'ilike', f'Observations: {line.observations}')
            ], limit=1)
            
            if not existing_nc:
                # Prepare description without HTML tags
                description = f"""
                <p><strong>Clause:</strong> {line.clause or ''}</p>
                <p><strong>Checkpoints:</strong> {line.checkpoints or ''}</p>
                <p><strong>Department:</strong> {line.department_id.name if line.department_id else ''}</p>
                <p><strong>Observations/Findings:</strong> {line.observations or ''}</p>
                <p><strong>Procedure:</strong> {line.procedure_id.name if line.procedure_id else ''}</p>
                <p><strong>Format Number:</strong> {line.format_number_ids.format_number if line.format_number_ids else ''}</p>
                <p><strong>Type:</strong> {dict(line._fields['criteria'].selection).get(line.criteria)}</p>
                """
                
                nc_type = 'major' if line.criteria == 'major_nc' else 'minor'
                
                # Create nonconformity
                nc_vals = {
                    'name': self.audit_id.reference,
                    'description': description,
                    'nc_type': nc_type,
                    'system_id': self.audit_id.system_id.id if self.audit_id.system_id else False,
                    'user_id': self.env.user.id,
                    'manager_user_id': self.audit_id.user_id.id if self.audit_id.user_id else self.env.user.id,
                    'responsible_user_id': self.audit_id.user_id.id if self.audit_id.user_id else self.env.user.id,
                    'partner_id': self.env.company.partner_id.id,
                    'audit_id': self.audit_id.id,
                    'audited_department_id': line.department_id.id if line.department_id else False,
                    
                }

                # Add procedure if specified
                if line.procedure_id:
                    nc_vals['procedure_ids'] = [(4, line.procedure_id.id)]

                # Create nonconformity record
                self.env['mgmtsystem.nonconformity'].create(nc_vals)

    def _handle_verification_data(self, line):
        """Handle verification line related operations"""
        self._sync_strong_points(line)
        self._sync_improve_points(line)
        self._sync_nonconformities(line)
    

    def action_filter_department_lines(self):
        """Button action to toggle department filter"""
        for record in self:
            record.is_department_filtered = not record.is_department_filtered
            record._compute_filtered_line_ids()
        return True 

    @api.depends('audit_id.line_ids', 'deprtmnt_id', 'is_department_filtered')
    def _compute_filtered_line_ids(self):
        """Compute filtered verification lines based on department"""
        VerificationLine = self.env['mgmtsystem.verification.line']
        for record in self:
            if record.is_department_filtered and record.deprtmnt_id:
                # Get filtered lines
                filtered_lines = record.audit_id.line_ids.filtered(
                    lambda line: line.department_id.id == record.deprtmnt_id.id
                )
                
                # Update auditor_id for filtered lines
                filtered_lines.write({'auditor_id': record.id})
                
                # Set filtered lines
                record.filtered_line_ids = filtered_lines
            else:
                # When filter is off, show all lines assigned to this auditor
                record.filtered_line_ids = VerificationLine.browse([])
                # assigned_lines = VerificationLine.search([
                #     ('auditor_id', '=', record.id)
                # ])
                # record.filtered_line_ids = assigned_lines

    @api.onchange('department_ids')
    def _onchange_department_ids(self):
        """Clear deprtmnt_id if it's not in department_ids anymore"""
        if self.deprtmnt_id and self.deprtmnt_id not in self.department_ids:
            self.deprtmnt_id = False

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

    @api.constrains('certified_date', 'expiry_date')
    def _check_dates(self):
        """Validate certification dates"""
        for record in self:
            if record.certified_date and record.expiry_date:
                if record.expiry_date <= record.certified_date:
                    raise ValidationError(_("Expiry date must be after certification date"))

    @api.constrains('department_id', 'department_ids')
    def _check_departments(self):
        """Ensure user's department is not in departments to audit"""
        for record in self:
            if record.department_id and record.department_ids:
                if record.department_id.id in record.department_ids.ids:
                    raise ValidationError(_("Auditor cannot audit their own department"))

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