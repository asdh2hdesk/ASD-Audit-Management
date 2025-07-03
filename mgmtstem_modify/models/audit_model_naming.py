from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MgmtsystemAudit(models.Model):
    """Model class that manage audit."""
    _inherit = "mgmtsystem.audit"
    
    company_id = fields.Many2one(
        "res.company", 
        "Company", 
        default=lambda self: self.env.company,
    )
    reference = fields.Char(
        size=64, 
        required=True, 
        default="NEW",
        copy=False
    )
    
    @api.model_create_multi
    def create(self, vals):
        """Audit creation."""
        for value in vals:
            value.update(
                {"reference": self.env["ir.sequence"].next_by_code("mgmtsystem.audit")}
            )
        audit_id = super(MgmtsystemAudit, self).create(vals)
        return audit_id
