from odoo import fields, models, api, _
from odoo.osv import expression
from odoo.exceptions import ValidationError, UserError


class MgmtsystemAudit(models.Model):
    """Model class that manage audit."""

    _inherit = "mgmtsystem.audit"
    
    state = fields.Selection([
        ('open', 'To Be Started'),
        ('in_progress', 'In Progress'),
        ('waiting_approval', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('done', 'Closed'),
        ('cancel', 'Cancelled')
    ], default='open', required=True, string='Status')
    
    def action_start(self):
        """Move audit to in progress state and update auditors"""
        self.write({'state': 'in_progress'})
        # Update all related auditors to in_progress state
        self.env['mgmtsystem.audit.auditor'].search([
            ('audit_id', '=', self.id)
        ]).write({'state': 'in_progress'})
        return True
    
    def action_back_to_start(self):
        """Move audit back to open state"""
        return self.write({'state': 'open'})

    def action_approve(self):
        """Move audit to approved state only if all auditors have completed their audits"""
        # Get all auditors for this audit
        auditors = self.env['mgmtsystem.audit.auditor'].search([
            ('audit_id', '=', self.id)
        ])
        
        # Check if any auditor is not in 'completed' state
        incomplete_auditors = auditors.filtered(lambda a: a.state != 'sent_approval')
        
        if incomplete_auditors:
            # Create a list of auditor names and their departments
            pending_details = []
            for auditor in incomplete_auditors:
                dept_name = auditor.department_ids.name or 'No Department'
                user_name = auditor.user_id.name or 'No User'
                pending_details.append(f"• Auditor: {user_name}  |  Pending department: {dept_name}")
            
            error_msg = "Cannot approve audit. Please ensure all department audits are Sent for Approval."
            if pending_details:
                error_msg += f"\n\nPending Audits:\n{chr(10).join(pending_details)}"
                
            raise UserError(_(error_msg))
        
        # If all auditors are completed, proceed with approval
        self.write({'state': 'approved'})
        # Update all related auditors to completed state
        auditors.write({'state': 'completed'})
        return True
    
    # def action_approve(self):
    #     """Move audit to approved state"""
    #     self.write({'state': 'approved'})
    #     # Update all related auditors to completed state
    #     self.env['mgmtsystem.audit.auditor'].search([
    #         ('audit_id', '=', self.id)
    #     ]).write({'state': 'completed'})
    #     return True

    def button_close(self):
        """Move audit to done state"""
        return self.write({'state': 'done'})
    
    def action_cancel(self):
        """Move audit to cancel state"""
        self.write({'state': 'cancel'})
        # Update all related auditors to completed cancel state
        self.env['mgmtsystem.audit.auditor'].search([
            ('audit_id', '=', self.id)
        ]).write({'state': 'cancel'})
        return True
    
    def action_undo(self):
        """Move audit back to in progress state"""
        self.action_start()
        # Update all related auditors back to in_progress state
        self.env['mgmtsystem.audit.auditor'].search([
            ('audit_id', '=', self.id)
        ]).write({'state': 'in_progress'})
        return True

    # def action_undo(self):
    #     """Move audit back to in progress state"""
    #     return self.action_start()
        # return self.write({'state': 'in_progress'})
    

class MgmtsystemAuditAuditor(models.Model):
    _inherit = "mgmtsystem.audit.auditor"
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('sent_approval', 'Sent for Approval'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled')
    ], default='draft', required=True, string='Status')

    def action_start(self):
        """Move to in progress state and start related audit"""
        # Call the audit's action_start method if it exists
        if self.audit_id:
            self.audit_id.action_start()
        
        # Set the auditor's state to in progress
        return self.write({'state': 'in_progress'})

    def action_send_approval(self):
        """Move to sent for approval state and update audit"""
        self.write({'state': 'sent_approval'})
        # Update the related audit to waiting_approval state
        if self.audit_id:
            self.audit_id.write({'state': 'waiting_approval'})
        return True

    def action_undo(self):
        """Move back to in progress state"""
        return self.action_start()
        # return self.write({'state': 'in_progress'})
        
    def action_cancel(self):
        """Move to cancel state"""
        return self.write({'state': 'cancel'})
        
    @api.model
    def create(self, vals):
        """Override create to sync state with audit"""
        record = super(MgmtsystemAuditAuditor, self).create(vals)
        if record.audit_id and record.audit_id.state != 'open':
            # Set auditor state based on audit state
            if record.audit_id.state in ['in_progress', 'waiting_approval']:
                record.write({'state': 'in_progress'})
            elif record.audit_id.state in ['approved', 'done']:
                record.write({'state': 'completed'})
        return record
    