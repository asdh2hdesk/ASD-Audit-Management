# models/verification_line_wizard.py
from odoo import api, fields, models

class VerificationLineWizard(models.TransientModel):
    _name = 'verification.line.wizard'
    _description = 'Verification Line Wizard'

    audit_id = fields.Many2one('mgmtsystem.audit', string='Audit')
    
    seq = fields.Integer(string='Sequence')
    clause = fields.Char(string='Clause')
    checkpoints = fields.Char(string='Checkpoints')
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Department being verified'
    )
    observations = fields.Text(string='Observations')
    criteria = fields.Selection(
        string='Criteria',
        selection=[
            ('major_nc', 'Major Nonconformity'),
            ('minor_nc', 'Minor Nonconformity'),
            ('strong_point', 'Strong Point'),
            ('to_improve_points', 'To Improve Points'),
        ]
    )
    objective_evidence = fields.Text(string='Objective Evidence')
    status =  fields.Selection(string='Status',
        selection=[
            ('to_be_started', 'To be started'),
            ('in_progress', 'In progress'),
            ('completed', 'Completed'),
        ],
        help='Current status of the verification line'
    )

    def action_add_line(self):
        self.ensure_one()
        verification_line = self.env['mgmtsystem.verification.line'].create({
            # 'audit_id': self.audit_id.id,
            'seq': self.seq,
            'clause': self.clause,
            'checkpoints': self.checkpoints,
            'department_id': self.department_id.id,
            'observations': self.observations,
            'criteria': self.criteria,
            'objective_evidence': self.objective_evidence,
            'status': self.status,
        })
        return {'type': 'ir.actions.act_window_close'}
    
    def action_save_lines(self):
        self.ensure_one()
        audit = self.audit_id
        # Delete existing lines
        # audit.line_ids.unlink()
        
        # Create new lines from wizard
        wizard_lines = self.search([('audit_id', '=', audit.id)])
        for line in wizard_lines:
            self.env['mgmtsystem.verification.line'].create({
                # 'audit_id': audit.id,
                'seq': line.seq,
                'clause': line.clause,
                'checkpoints': line.checkpoints,
                'department_id': line.department_id.id,
                'observations': line.observations,
                'criteria': line.criteria,
                'objective_evidence': line.objective_evidence,
                'status': line.status,
            })
        return {'type': 'ir.actions.act_window_close'}