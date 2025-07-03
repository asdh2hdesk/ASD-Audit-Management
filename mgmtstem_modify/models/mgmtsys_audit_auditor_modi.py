from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MgmtsystemAudit(models.Model):
    """Model class that manage audit."""
    _inherit = "mgmtsystem.audit"

    auditors_user_ids = fields.One2many(
        'mgmtsystem.audit.auditor',
        'audit_id',
        string='Auditors'
    )
    
    
    @api.constrains('auditors_user_ids')
    def _check_auditor_certification(self):
        """
        Validate auditors' certification status:
        1. Check if all auditors have certification dates
        2. Check if auditors' certifications are not expired
        """
        for audit in self:
            for auditor in audit.auditors_user_ids:
                # Check if certification date is empty
                if not auditor.certified_date:
                    raise ValidationError(f"Auditor {auditor.user_id.name} is not certified. You cannot add non-certified users.")
                elif not auditor.expiry_date:
                    raise ValidationError(f"Auditor {auditor.user_id.name} does not have an expiry date. Please set one.")
                    
                # Check if certification is expired
                if auditor.expiry_date and auditor.expiry_date < fields.Date.today():
                    raise ValidationError(f"Auditor {auditor.user_id.name}'s Certification has expired. Please renew.")

    def write(self, vals):
        result = super().write(vals)
        if 'auditors_user_ids' in vals:
            self._create_auditor_certifications()
        return result

    def _create_auditor_certifications(self):
        """Create auditor certification records for new auditors."""
        AuditorCert = self.env['auditor.certification']
        for audit in self:
            for auditor_line in audit.auditors_user_ids:
                # Skip if user already has a certification record
                existing_cert = AuditorCert.search([
                    ('user_id', '=', auditor_line.user_id.id)
                ], limit=1)
                
                if not existing_cert and auditor_line.user_id:
                    # Find employee record for the user
                    employee = self.env['hr.employee'].search([
                        ('user_id', '=', auditor_line.user_id.id)
                    ], limit=1)
                    
                    if employee:
                        AuditorCert.create({
                            'employee_id': employee.id,
                            'certified_date': auditor_line.certified_date,
                            'expiry_date': auditor_line.expiry_date,
                        })
                        

class MgmtsystemAuditAuditor(models.Model):
    _inherit = "mgmtsystem.audit.auditor"
    
    def _get_department_users_domain(self):
        """Get users from selected departments"""
        if not self.department_ids:
            return []
        
        employees = self.env['hr.employee'].sudo().search([
            ('department_id', 'in', self.department_ids.ids)
        ])
        user_ids = employees.mapped('user_id').ids
        
        # Remove current user from the list
        if self.env.uid in user_ids:
            user_ids.remove(self.env.uid)
            
        return [('id', 'in', user_ids)]
    
    selected_user_ids = fields.Many2many(
        'res.users',
        'auditor_selected_users_rel',
        'auditor_id',
        'user_id',
        string='Select Auditees',
        domain=lambda self: self._get_department_users_domain()
    )
    
    department_ids = fields.Many2many(
        'hr.department',
        string='Department to Audit',
        help="Only users from these departments will be available for selection"
    )

    @api.onchange('department_ids')
    def _onchange_department_ids(self):
        """Clear selected users if they're not in the selected departments"""
        if self.department_ids and self.selected_user_ids:
            employees = self.env['hr.employee'].sudo().search([
                ('department_id', 'in', self.department_ids.ids)
            ])
            valid_user_ids = employees.mapped('user_id').ids
            
            if self.env.uid in valid_user_ids:
                valid_user_ids.remove(self.env.uid)
            
            self.selected_user_ids = self.selected_user_ids.filtered(
                lambda u: u.id in valid_user_ids
            )

    @api.constrains('department_ids', 'selected_user_ids')
    def _check_users_department(self):
        """Ensure selected users belong to chosen departments"""
        for record in self:
            if record.department_ids and record.selected_user_ids:
                employees = self.env['hr.employee'].sudo().search([
                    ('user_id', 'in', record.selected_user_ids.ids)
                ])
                
                for employee in employees:
                    if employee.department_id.id not in record.department_ids.ids:
                        raise ValidationError(_(
                            "User '%s' does not belong to any of the selected departments."
                        ) % employee.name)