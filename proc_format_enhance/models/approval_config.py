from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProcedureFormatApprovalConfig(models.Model):
    _name = 'procedure.format.approval.config'
    _description = 'Procedure Format Approval Configuration'

    approver_ids = fields.Many2many('res.users', string='Approvers')
    config_key = fields.Char(default='singleton', readonly=True)

    _sql_constraints = [
        ('unique_config', 'unique(config_key)', 'Only one configuration record is allowed!')
    ]

    @api.model
    def create(self, vals):
        if self.search([]):
            raise UserError(_("Approval configuration already exists. Please edit the existing one."))
        return super().create(vals)