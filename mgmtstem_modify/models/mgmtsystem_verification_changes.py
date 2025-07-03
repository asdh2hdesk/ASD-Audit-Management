from odoo import fields, models, api


class MgmtsystemVerificationLine(models.Model):
    """Class to manage verification's Line."""

    _inherit = "mgmtsystem.verification.line"
    _description = "Verification Line"
    _order = "seq"


    clause = fields.Char(
        string='Clause',
        help='Reference clause or section number'
    )

    checkpoints = fields.Text(
        string='Checkpoints',
        help='Verification checkpoints or requirements to be verified'
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Department being verified'
    )

    observations = fields.Text(
        string='Observations/Findings',
        help='Detailed observations and findings during verification'
    )
    
    criteria = fields.Selection(
        string='Criteria',
        selection=[
            ('major_nc', 'Major Nonconformity'),
            ('minor_nc', 'Minor Nonconformity'),
            ('strong_point', 'Strong Point'),
            ('to_improve_points', 'To Improve Points'),
        ]
    )

    objective_evidence = fields.Text(
        string='Objective Evidence',
        help='Documentary or physical evidence supporting the verification'
    )

    status =  fields.Selection(string='Status',
        selection=[
            ('to_be_started', 'To be started'),
            ('in_progress', 'In progress'),
            ('completed', 'Completed'),
        ],
        help='Current status of the verification line'
    )
    
    system_id = fields.Many2one(
        'mgmtsystem.system',
        string='System',
        help='System this verification line belongs to'
    )
    procedure_id = fields.Many2one(
        "document.page", "Procedure", ondelete="restrict", index=True
    )
    format_number = fields.Char(string="Format Number")
    name = fields.Char("Question", required=False)
    
    auditor_id = fields.Many2one(
        'mgmtsystem.audit.auditor',
        string='Assigned Auditor',
        help='Auditor assigned to this verification line',
        ondelete='set null'
    )
    
    evidence_images_ids = fields.Many2many(
        'ir.attachment',
        'verification_line_attachment_rel',
        'line_id',
        'attachment_id',
        string='Evidence Images',
        help='Multiple images as evidence supporting the verification'
    )
    
    format_number_ids = fields.Many2many(
        'mgmtsystem.procedure.format.number',
        'verif_format_rel',  # Short relation table name
        'verif_id',          # Short column name
        'format_id',         # Short column name
        string='Format Number',
        domain="[('id', 'in', available_format_numbers)]"
    )
    
    available_format_numbers = fields.Many2many(
        'mgmtsystem.procedure.format.number',
        'verif_format_avail_rel',
        'verif_id',
        'format_id',
        compute='_compute_available_format_numbers',
        string='Available Format Numbers'
    )
    
    @api.depends('procedure_id')
    def _compute_available_format_numbers(self):
        """Compute available format numbers based on selected procedure"""
        for record in self:
            if record.procedure_id and record.procedure_id.format_number_ids:
                record.available_format_numbers = record.procedure_id.format_number_ids.ids
            else:
                record.available_format_numbers = False

    @api.onchange('procedure_id')
    def _onchange_procedure_id(self):
        """Clear format number when procedure changes"""
        self.format_number_ids = False

    @api.onchange('format_number_ids')
    def _onchange_format_number_ids(self):
        """Update procedure_ids in format numbers when format_number_ids changes"""
        if self.procedure_id and self.format_number_ids:
            for format_number in self.format_number_ids:
                if self.procedure_id.id not in format_number.procedure_ids.ids:
                    format_number.procedure_ids = [(4, self.procedure_id.id)]

    def write(self, vals):
        """Override write method to update procedure_ids in format numbers"""
        result = super().write(vals)
        if 'format_number_ids' in vals:
            for record in self:
                if record.procedure_id and record.format_number_ids:
                    for format_number in record.format_number_ids:
                        if record.procedure_id.id not in format_number.procedure_ids.ids:
                            format_number.procedure_ids = [(4, record.procedure_id.id)]
        return result
    
    # @api.onchange('criteria')
    # def _onchange_criteria(self):
    #     """Handle changes to criteria field"""
    #     if self.criteria == 'strong_point' and self.audit_id:
    #         # Create strong point line only if it doesn't exist already
    #         existing_strong_point = self.audit_id.strong_points_ids.filtered(
    #             lambda x: x.clause == self.clause and 
    #                      x.checkpoints == self.checkpoints and
    #                      x.observations == self.observations
    #         )
    #         if not existing_strong_point:
    #             self.env['strong.point.line'].create({
    #                 'name': f"Strong Point - {self.clause or ''}", 
    #                 'seq': len(self.audit_id.strong_points_ids) + 1,
    #                 'clause': self.clause,
    #                 'checkpoints': self.checkpoints,
    #                 'observations': self.observations,
    #                 'audit_id': self.audit_id.id,
    #             })
        
    #     elif self.criteria == 'to_improve_points' and self.audit_id:
    #         # Create to improve point line only if it doesn't exist already
    #         existing_improve_point = self.audit_id.to_improve_points_ids.filtered(
    #             lambda x: x.clause == self.clause and 
    #                      x.checkpoints == self.checkpoints and
    #                      x.observations == self.observations
    #         )
    #         if not existing_improve_point:
    #             self.env['to.improve.point.line'].create({
    #                 'name': f"To Improve Point - {self.clause or ''}", 
    #                 'seq': len(self.audit_id.to_improve_points_ids) + 1,
    #                 'clause': self.clause,
    #                 'checkpoints': self.checkpoints,
    #                 'observations': self.observations,
    #                 'status': self.status,
    #                 'audit_id': self.audit_id.id,
    #             })
    
    @api.onchange('criteria')
    def _onchange_criteria(self):
        """Handle changes to criteria field"""
        # Check if this line belongs to an auditor's filtered lines
        if self.auditor_id:
            self.auditor_id._handle_verification_data(self)
        # Original functionality for audit
        elif self.audit_id:
            if self.criteria == 'strong_point':
                existing_strong_point = self.audit_id.strong_points_ids.filtered(
                    lambda x: x.clause == self.clause and 
                             x.checkpoints == self.checkpoints and
                             x.observations == self.observations
                )
                if not existing_strong_point:
                    self.env['strong.point.line'].create({
                        'name': f"Strong Point - {self.clause or ''}", 
                        'seq': len(self.audit_id.strong_points_ids) + 1,
                        'clause': self.clause,
                        'checkpoints': self.checkpoints,
                        'observations': self.observations,
                        'audit_id': self.audit_id.id,
                    })
            
            elif self.criteria == 'to_improve_points':
                existing_improve_point = self.audit_id.to_improve_points_ids.filtered(
                    lambda x: x.clause == self.clause and 
                             x.checkpoints == self.checkpoints and
                             x.observations == self.observations
                )
                if not existing_improve_point:
                    self.env['to.improve.point.line'].create({
                        'name': f"To Improve Point - {self.clause or ''}", 
                        'seq': len(self.audit_id.to_improve_points_ids) + 1,
                        'clause': self.clause,
                        'checkpoints': self.checkpoints,
                        'observations': self.observations,
                        'status': self.status,
                        'audit_id': self.audit_id.id,
                    })


class SystemVerificationLine(models.Model):
    """Model to store system verification lines separately."""
    
    _name = "system.verification.line"
    _description = "System Verification Line"
    
    seq = fields.Integer("Sequence")
    
    clause = fields.Char(
        string='Clause',
        help='Reference clause or section number'
    )
    checkpoints = fields.Text(
        string='Checkpoints',
        help='Verification checkpoints or requirements to be verified'
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Department being verified'
    )
    system_id = fields.Many2one(
        'mgmtsystem.system',
        string='System',
        required=True
    )

class MgmtSystemSystem(models.Model):
    _inherit = "mgmtsystem.system"

    verification_lines_ids = fields.One2many(
        'system.verification.line',
        'system_id',
        string='Verification Lines'
    )
    
class MgmtsystemAudit(models.Model):
    _inherit = "mgmtsystem.audit"
    
    
    def get_action_url(self):
        """
        Return a short link to the audit form view
        eg. http://localhost:8069/?db=prod#id=1&model=mgmtsystem.audit
        """

        base_url = self.env["ir.config_parameter"].sudo().get_param(
            "web.base.url"
        )
        base_url = base_url or "http://localhost:8069"
        url = ("{}/web#db={}&id={}&model={}").format(
            base_url, self.env.cr.dbname, self.id, self._name
        )
        return url

    @api.onchange('system_id')
    def _onchange_system_id(self):
        """Populate verification lines when system is selected"""
        # Always clear existing lines first
        self.line_ids = [(5, 0, 0)]

        # Return if no system selected
        if not self.system_id:
            return

        # Get lines from system
        system_lines = self.system_id.verification_lines_ids
        if not system_lines:
            return  # No lines to add

        # Track existing clauses to prevent duplicates
        existing_clauses = set()

        new_lines = []
        for line in system_lines:
            # Skip if we already have this clause
            if line.clause in existing_clauses:
                continue
                
            new_lines.append((0, 0, {
                'clause': line.clause,
                'checkpoints': line.checkpoints,
                'department_id': line.department_id.id if line.department_id else False,
            }))
            existing_clauses.add(line.clause)
            
        self.line_ids = new_lines

    def write(self, vals):
        """Override write to sync verification lines to system"""
        res = super().write(vals)
        if vals.get('line_ids'):
            self._sync_lines_to_system()
        return res

    @api.model
    def create(self, vals):
        """Override create to sync verification lines to system"""
        record = super().create(vals)
        if vals.get('line_ids'):
            record._sync_lines_to_system()
        return record

    def _sync_lines_to_system(self):
        """Sync verification lines to system model"""
        if not self.system_id:
            return

        SystemLine = self.env['system.verification.line']
        
        # Get existing system lines
        existing_lines = self.system_id.verification_lines_ids

        # Track processed system lines to handle deletions
        processed_system_lines = self.env['system.verification.line']

        for line in self.line_ids:
            # First try to find exact match using clause
            matching_line = existing_lines.filtered(
                lambda x: x.clause == line.clause
            )
            
            if matching_line:
                # Update existing line instead of creating new one
                matching_line.write({
                    'checkpoints': line.checkpoints,
                    'department_id': line.department_id.id if line.department_id else False,
                })
                processed_system_lines |= matching_line
            else:
                # Create new line only if no match found
                new_line = SystemLine.create({
                    'clause': line.clause,
                    'checkpoints': line.checkpoints,
                    'department_id': line.department_id.id if line.department_id else False,
                    'system_id': self.system_id.id,
                })
                processed_system_lines |= new_line