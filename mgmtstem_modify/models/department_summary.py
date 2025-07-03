from odoo import fields, models, api

class DepartmentAuditSummary(models.Model):
    _name = "department.audit.summary"
    _description = "Department Audit Summary"
    _order = "major_nc_count desc, minor_nc_count desc, action_count desc"
    
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help="The department for which the summary is calculated"
    )
    
    major_nc_count = fields.Integer(
        string='Major Nonconformities',
        compute='_compute_counts',
        store=True,
        help="Count of major nonconformities in this department"
    )
    
    minor_nc_count = fields.Integer(
        string='Minor Nonconformities',
        compute='_compute_counts',
        store=True,
        help="Count of minor nonconformities in this department"
    )
    
    action_count = fields.Integer(
        string='Improvement Points',
        compute='_compute_counts',
        store=True,
        help="Count of actions related to this department"
    )
    
    last_update = fields.Datetime(
        string="Last Update",
        default=fields.Datetime.now,
        help="Timestamp of the last update to trigger recomputation"
    )
    
    @api.depends('department_id', 'last_update')
    def _compute_counts(self):
        """
        Compute the counts of major nonconformities, minor nonconformities, and actions
        based on the audited_department_id.
        """
        for record in self:
            # Count major nonconformities
            major_nc_count = self.env['mgmtsystem.nonconformity'].search_count([
                ('audited_department_id', '=', record.department_id.id),
                ('nc_type', '=', 'major')
            ])
            # Count minor nonconformities
            minor_nc_count = self.env['mgmtsystem.nonconformity'].search_count([
                ('audited_department_id', '=', record.department_id.id),
                ('nc_type', '=', 'minor')
            ])
            # Count actions
            action_count = self.env['mgmtsystem.action'].search_count([
                ('audited_department_id', '=', record.department_id.id)
            ])
            # Assign computed values
            record.major_nc_count = major_nc_count
            record.minor_nc_count = minor_nc_count
            record.action_count = action_count

class HrDepartment(models.Model):
    _inherit = 'hr.department'
    
    def create(self, vals):
        """Override create to automatically generate a summary record."""
        dept = super(HrDepartment, self).create(vals)
        self.env['department.audit.summary'].create({'department_id': dept.id})
        return dept

class MgmtsystemNonconformity(models.Model):
    _inherit = "mgmtsystem.nonconformity"

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.audited_department_id:
            summary = self.env['department.audit.summary'].search([
                ('department_id', '=', record.audited_department_id.id)
            ], limit=1)
            if not summary:
                summary = self.env['department.audit.summary'].create({
                    'department_id': record.audited_department_id.id
                })
            summary.write({'last_update': fields.Datetime.now()})
        return record

    def write(self, vals):
        # Store old departments before update
        old_departments = {record.id: record.audited_department_id.id for record in self}
        result = super().write(vals)
        
        departments_to_update = set()
        
        for record in self:
            old_dept_id = old_departments.get(record.id)
            new_dept_id = record.audited_department_id.id if record.audited_department_id else False
            
            if 'audited_department_id' in vals:
                if old_dept_id:
                    departments_to_update.add(old_dept_id)
                if new_dept_id:
                    departments_to_update.add(new_dept_id)
            elif 'nc_type' in vals and new_dept_id:
                departments_to_update.add(new_dept_id)
        
        for dept_id in departments_to_update:
            summary = self.env['department.audit.summary'].search([
                ('department_id', '=', dept_id)
            ], limit=1)
            if not summary:
                summary = self.env['department.audit.summary'].create({
                    'department_id': dept_id
                })
            summary.write({'last_update': fields.Datetime.now()})
        
        return result

    def unlink(self):
        departments = set(record.audited_department_id.id for record in self if record.audited_department_id)
        result = super().unlink()
        for dept_id in departments:
            summary = self.env['department.audit.summary'].search([
                ('department_id', '=', dept_id)
            ], limit=1)
            if summary:
                summary.write({'last_update': fields.Datetime.now()})
        return result

class MgmtsystemAction(models.Model):
    _inherit = "mgmtsystem.action"

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.audited_department_id:
            summary = self.env['department.audit.summary'].search([
                ('department_id', '=', record.audited_department_id.id)
            ], limit=1)
            if not summary:
                summary = self.env['department.audit.summary'].create({
                    'department_id': record.audited_department_id.id
                })
            summary.write({'last_update': fields.Datetime.now()})
        return record

    def write(self, vals):
        old_departments = {record.id: record.audited_department_id.id for record in self}
        result = super().write(vals)
        
        departments_to_update = set()
        
        for record in self:
            old_dept_id = old_departments.get(record.id)
            new_dept_id = record.audited_department_id.id if record.audited_department_id else False
            
            if 'audited_department_id' in vals:
                if old_dept_id:
                    departments_to_update.add(old_dept_id)
                if new_dept_id:
                    departments_to_update.add(new_dept_id)
        
        for dept_id in departments_to_update:
            summary = self.env['department.audit.summary'].search([
                ('department_id', '=', dept_id)
            ], limit=1)
            if not summary:
                summary = self.env['department.audit.summary'].create({
                    'department_id': dept_id
                })
            summary.write({'last_update': fields.Datetime.now()})
        
        return result

    def unlink(self):
        departments = set(record.audited_department_id.id for record in self if record.audited_department_id)
        result = super().unlink()
        for dept_id in departments:
            summary = self.env['department.audit.summary'].search([
                ('department_id', '=', dept_id)
            ], limit=1)
            if summary:
                summary.write({'last_update': fields.Datetime.now()})
        return result