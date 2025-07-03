from odoo import fields, models, api, _
from odoo.exceptions import ValidationError



class ResCompany(models.Model):
    """Extend company model to add plant name."""
    _inherit = 'res.company'

    plant_name = fields.Char(
        string='Plant Code',
        help="Name of the company's plant"
    )
    
class MandateTrainingType(models.Model):
    _name = 'mandate.training.type'
    _description = 'Mandate Training Type'

    name = fields.Char(string='Training Type')
    
    
class EmployeeCertification(models.Model):
    """Model to manage employee certifications."""
    _name = "employee.certification"
    _description = "Employee Certification"

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade'
    )
    serial_no = fields.Integer(
        string='Sr. No.',
        readonly=True
    )
    description_id = fields.Many2one(
        'mandate.training.type',
        string='Description'
    )
    category = fields.Selection(
        [('mandate', 'Mandate'), ('non_mandate', 'Non-mandate')],
        string='Category', store=True, tracking=True
    )
    training_date = fields.Date(
        string='Training Date', store=True, tracking=True
    )
    certification_date = fields.Date(
        string='Certification Date', store=True, tracking=True
    )
    renewal_date = fields.Date(
        string='Renewal Date', store=True, tracking=True
    )
    attachment = fields.Binary(
        string='Attachment'
    )
    additional_renewal_date = fields.Date(
        string='Additional Renewal Date', store=True, tracking=True
    )
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    
    @api.model
    def create(self, vals):
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            max_serial = self.search([('employee_id', '=', employee.id)], order='serial_no desc', limit=1).serial_no
            vals['serial_no'] = (max_serial or 0) + 1
        return super(EmployeeCertification, self).create(vals)

    def unlink(self):
        employees = self.mapped('employee_id')
        res = super(EmployeeCertification, self).unlink()
        for employee in employees:
            self._renumber_certifications(employee)
        return res

    @api.model
    def _renumber_certifications(self, employee):
        certifications = self.search([('employee_id', '=', employee.id)], order='serial_no')
        for index, cert in enumerate(certifications, start=1):
            if cert.serial_no != index:
                cert.write({'serial_no': index})

    @api.constrains('certification_date', 'renewal_date')
    def _check_dates(self):
        for record in self:
            if record.renewal_date and record.certification_date and record.renewal_date < record.certification_date:
                raise ValidationError(_("Renewal date cannot be before certification date."))

    _sql_constraints = [
        ('employee_serial_uniq',
         'unique(employee_id, serial_no)',
         'Serial number must be unique per employee!')
    ]

    
class HrEmployee(models.Model):
    """Extend employee model to add certification dates."""
    _inherit = 'hr.employee'

    certification_date = fields.Date(
        string='Certification Date',
        help="Date when the employee was certified as an auditor", tracking=True
    )
    certification_expiry_date = fields.Date(
        string='Certification Expiry Date',
        help="Date when the employee's auditor certification expires", tracking=True
    )
    
    certification_ids = fields.One2many(
        'employee.certification',
        'employee_id',
        string='Certifications',
        help="List of certifications for the employee", tracking=True
    )
    
    @api.constrains('certification_date', 'certification_expiry_date')
    def _check_employee_dates(self):
        for record in self:
            if record.certification_expiry_date and record.certification_date and record.certification_expiry_date < record.certification_date:
                raise ValidationError(_("Certification expiry date cannot be before certification date."))

    @api.onchange('certification_ids')
    def _onchange_certification_ids(self):
        if self.certification_ids:
            cert_dates = [date for date in self.certification_ids.mapped('certification_date') if date]
            renewal_dates = [date for date in self.certification_ids.mapped('renewal_date') if date]
            if cert_dates:
                self.certification_date = min(cert_dates)
            if renewal_dates:
                self.certification_expiry_date = max(renewal_dates)
    
class AuditorCertification(models.Model):
    """Model to manage auditor certifications."""
    _name = "auditor.certification"
    _description = "Auditor Certification"
    _rec_name = 'employee_id'
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        help="Employee whose certification is being managed"
    )
    user_id = fields.Many2one(
        'res.users',
        related='employee_id.user_id',
        string='Employee User Name',
        store=True,
    )
    certified_date = fields.Date(
        string='Certification Date',
        help="Date when the certification was issued"
    )
    expiry_date = fields.Date(
        string='Certification Expiry Date',
        help="Date when the certification expires"
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, the certification record will be hidden"
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
    ], string='Status', default='active', compute='_compute_state', store=True)

    _sql_constraints = [
        ('user_unique',
         'UNIQUE(user_id)',
         'This user already has a certification record!')
    ]

    @api.depends('expiry_date')
    def _compute_state(self):
        today = fields.Date.today()
        for record in self:
            if record.expiry_date and record.expiry_date < today:
                record.state = 'expired'
            else:
                record.state = 'active'

    def write(self, vals):
        """Override write to update related records."""
        result = super().write(vals)
        
        # If certification dates are changed, sync with other models
        if 'certified_date' in vals or 'expiry_date' in vals:
            for record in self:
                # Update employee record
                if record.employee_id:
                    record.employee_id.write({
                        'certification_date': record.certified_date,
                        'certification_expiry_date': record.expiry_date,
                    })
                
                # Update all auditor records for this user
                if record.user_id:
                    auditor_records = self.env['mgmtsystem.audit.auditor'].search([
                        ('user_id', '=', record.user_id.id)
                    ])
                    auditor_records.write({
                        'certified_date': record.certified_date,
                        'expiry_date': record.expiry_date,
                    })
        
        return result

    @api.model
    def create(self, vals):
        """Override create to update related records."""
        record = super().create(vals)
        
        # Update employee and auditor records upon creation
        if record.certified_date or record.expiry_date:
            if record.employee_id:
                record.employee_id.write({
                    'certification_date': record.certified_date,
                    'certification_expiry_date': record.expiry_date,
                })
            
            if record.user_id:
                auditor_records = self.env['mgmtsystem.audit.auditor'].search([
                    ('user_id', '=', record.user_id.id)
                ])
                auditor_records.write({
                    'certified_date': record.certified_date,
                    'expiry_date': record.expiry_date,
                })
        
        return record


class MgmtsystemProcedureFormatNumber(models.Model):
    """Model to manage procedure format number."""
    _name = "mgmtsystem.procedure.format.number"
    _description = "Procedure Format Number"
    _rec_name = "format_number"
    
    name = fields.Char(string='Name')
    format_number = fields.Char(string='Format Number', required=True)
    procedure_ids = fields.Many2many(
        'document.page',
        'doc_format_rel',
        'format_id',
        'doc_id',
        string='Procedures'
    )
    
class DocumentPage(models.Model):
    """This class is use to manage Document."""
    _inherit = "document.page"

    format_number_ids = fields.Many2many(
        'mgmtsystem.procedure.format.number',
        'doc_format_rel',
        'doc_id',
        'format_id',
        string='Format Numbers',
        help="Format numbers associated with this procedure"
    )

class AuditRevisonData(models.Model):
    """This class is use to manage Revision data of Audits."""
    _name = "audit.revision.data"
    _description = "Audit Revision Data"
    
    audit_id = fields.Many2one('mgmtsystem.audit', string='Audit')
    reference = fields.Char(string='Reference', related='audit_id.reference', store=True)
    revision_data = fields.Text(string="Revision Data", store=True)
    create_date = fields.Datetime(string='Created On', readonly=True)
    create_uid = fields.Many2one('res.users', string='Created By', readonly=True)
    
    _sql_constraints = [
        ('audit_create_date_uniq', 
         'unique(audit_id,create_date)',
         'Only one revision record can exist per audit at a given time!')
        ]
    
    
class MgmtsystemAudit(models.Model):
    """Model class that manage audit."""
    _inherit = "mgmtsystem.audit"
    
    company_id = fields.Many2one(
        "res.company", 
        "Company", 
        default=lambda self: self.env.company
    )
    
    company_state = fields.Char(related='company_id.city', string='City', store=True)
    
    plant_name = fields.Char(
        related='company_id.plant_name',
        string='Plant Code',
        store=True,
        help="Plant name from the related company"
    )
    
    def write(self, vals):
        """Override write to store revision data"""
        result = super(MgmtsystemAudit, self).write(vals)
        
        for record in self:
            # Get latest revision record for this audit
            latest_revision = self.env['audit.revision.data'].search([
                ('audit_id', '=', record.id)
            ], order='create_date DESC', limit=1)
            
            if 'revision_date' in vals and 'revision_data' in vals:
                # Create new revision when both date and data change
                self.env['audit.revision.data'].create({
                    'audit_id': record.id,
                    'revision_data': vals['revision_data']
                })
            elif 'revision_data' in vals and latest_revision:
                # Only update revision data in latest record
                latest_revision.write({
                    'revision_data': vals['revision_data']
                })
            
        return result

