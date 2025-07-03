from odoo import models, fields, api

class MgmtsystemProcedureFormatRevision(models.Model):
    _name = 'mgmtsystem.procedure.format.revision'
    _description = 'Procedure Format Revision'
    _rec_name = 'revision_number'

    format_id = fields.Many2one('mgmtsystem.procedure.format.number', string='Format Number', required=True, ondelete='cascade')
    revision_number = fields.Char(string='Revision Number', required=True)
    revision_date = fields.Date(string='Revision Date', default=fields.Date.today)
    revised_by = fields.Many2one('res.users', string='Revised By', default=lambda self: self.env.user, stored=True)
    attachment = fields.Binary(string='Attachment')
    description = fields.Text(string='Description')
    previous_revision_ids = fields.Many2many(
        'mgmtsystem.procedure.format.revision',
        relation='procedure_format_revision_previous_revision_rel',
        column1='current_revision_id',
        column2='previous_revision_id',
        string='Previous Revisions',
    )
    revision_html = fields.Html(string='Revision Details')

    @api.model
    def create(self, vals):
        revision = super().create(vals)
        format_number = revision.format_id
        if format_number.state == 'released':
            format_number.write({'state': 'draft'})
        return revision