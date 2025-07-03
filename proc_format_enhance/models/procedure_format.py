from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MgmtsystemProcedureFormatNumber(models.Model):
    _inherit = 'mgmtsystem.procedure.format.number'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('released', 'Released'),
        ('canceled', 'Canceled'),
    ], string='Status', default='draft', tracking=True, stored=True)
    
    format_name = fields.Char(string='Format Name',  tracking=True, stored=True)
    
    approved_by = fields.Many2many(
        'res.users',
        relation='procedure_format_approved_by_rel',
        string='Approved By'
    )
    to_be_approved_by = fields.Many2many(
        'res.users',
        relation='procedure_format_to_be_approved_by_rel',
        string='To Be Approved By'
    )
    released_date = fields.Datetime(string='Released Date', stored=True)
    released_by = fields.Many2one('res.users', string='Released By', stored=True)
    revision_details = fields.Html(string='Revision Details')
    attachment = fields.Binary(string='Attachment')
    revision_ids = fields.One2many('mgmtsystem.procedure.format.revision', 'format_id', string='Revisions')
    current_revision_id = fields.Many2one('mgmtsystem.procedure.format.revision', string='Current Revision')

    @api.model
    def create(self, vals):
        # Set approvers from configuration
        config = self.env['procedure.format.approval.config'].search([], limit=1)
        if config:
            vals['to_be_approved_by'] = [(6, 0, config.approver_ids.ids)]
        else:
            vals['to_be_approved_by'] = [(6, 0, [])]
        # Create initial revision
        format_number = super().create(vals)
        self.env['mgmtsystem.procedure.format.revision'].create({
            'format_id': format_number.id,
            'revision_number': '1',
            'revision_date': fields.Date.today(),
            'revised_by': self.env.user.id,
        })
        return format_number

    def action_request_approval(self):
        self.ensure_one()
        self.write({
            'state': 'pending_approval',
            'approved_by': [(5, 0, 0)]
        })

    def action_approve(self):
        self.ensure_one()
        if self.env.user not in self.to_be_approved_by:
            raise UserError(_("You are not authorized to approve this format number."))
        if self.env.user in self.approved_by:
            raise UserError(_("You have already approved this format number."))
        self.write({'approved_by': [(4, self.env.user.id)]})
        if all(approver in self.approved_by for approver in self.to_be_approved_by):
            self.write({'state': 'approved'})

    def action_release(self):
        self.ensure_one()
        if self.revision_ids:
            latest_revision = max(self.revision_ids, key=lambda r: r.create_date)
            self.current_revision_id = latest_revision
        self.write({
            'state': 'released',
            'released_date': fields.Datetime.now(),
            'released_by': self.env.user
        })

    def action_add_revision(self):
        self.ensure_one()
        context = {
            'default_format_id': self.id,
            'default_revision_number': str(len(self.revision_ids) + 1),
        }
        if self.current_revision_id:
            context['default_previous_revision_ids'] = [(6, 0, [self.current_revision_id.id])]
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Revision',
            'res_model': 'mgmtsystem.procedure.format.revision',
            'view_mode': 'form',
            'target': 'new',
            'context': context
        }