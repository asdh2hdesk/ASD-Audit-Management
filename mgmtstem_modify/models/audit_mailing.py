from odoo import models, fields, api
from datetime import timedelta, date
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class AuditTargetNotification(models.Model):
    _name = 'audit.target.notification'
    _description = 'Audit Target Notification'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    audit_id = fields.Many2one('mgmtsystem.audit', string='Audit')
    reference = fields.Char(string='Reference', related='audit_id.reference', store=True)
    auditor_id = fields.Many2one('mgmtsystem.audit.auditor', string='Auditor Name', 
        domain="[('audit_id', '=', audit_id)]")
    target_date = fields.Date(string='Target Date', related='auditor_id.target_date', 
        store=True, readonly=True)
    user_ids = fields.Many2many('res.users', string='Users to Notify')
    days_before = fields.Integer(string='Days Before',
        help='Number of days before target date to send notification',
        default=4, required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    is_initial_mail_sent = fields.Boolean(string='Initial Mail Sent', default=False, tracking=True)
    is_reminder_mail_sent = fields.Boolean(string='Reminder Mail Sent', default=False, tracking=True)
    
    @api.depends('audit_id')
    def _compute_name(self):
        for record in self:
            if record.audit_id:
                record.name = f"{record.audit_id.name} | {record.audit_id.reference}"
            else:
                record.name = "New Target"
    
    def _get_email_recipients(self):
        """Collect email recipients from users and related employees"""
        email_list = []
        
        # Collect emails from users
        for user in self.user_ids:
            if user.partner_id and user.partner_id.email:
                email_list.append(user.partner_id.email)
        
        # Collect work emails from related employees
        for user in self.user_ids:
            employees = self.env['hr.employee'].search([('user_id', '=', user.id)])
            email_list.extend(
                employees.filtered(lambda e: e.work_email).mapped('work_email')
            )
        
        return list(set(email_list))  # Remove duplicates
    
    def send_initial_notification(self):
        """Send initial notification to users"""
        for record in self:
            # Existing code for getting email recipients
            email_list = record._get_email_recipients()
            print("----------- is_initial_mail_sent email_list -----------", email_list)
            
            if email_list:
                # Prepare email template
                template = self.env.ref('mgmtstem_modify.audit_initial_notification_template')
                
                # Set template values before sending
                template_values = {'auto_delete': False}
                template.write(template_values)
                
                # Unique user processing
                users = self.env['res.users'].search([('partner_id.email', 'in', email_list)])
                
                for user in users:
                    try:
                        # Generate email values
                        mail_values = template.generate_email(
                                record.id, 
                                fields=['subject', 'body_html', 'email_from', 'email_to']
                            )
                        
                        # Update mail values with custom body and additional details
                        mail_values.update({
                            'email_from': record.audit_id.company_id.email or self.env.user.email or '',
                            'email_to': user.partner_id.email,
                            # 'body_html': f"""
                            # <div>
                            #     <p>Dear Team,</p>
                            #     <p>Reminder: Audit is approaching in {record.days_before} days</p>
                            #     <p>Audit Name: {record.audit_id.name} </p>
                            #     <p>Audit Ref. : {record.audit_id.reference}</p>
                            #     <p>State : {record.audit_id.company_state}</p>
                            #     <p>Plant Code : {record.audit_id.plant_name}</p>
                            #     <p>System : {record.audit_id.system_id.name}</p>
                            #     <p>Auditor: {record.auditor_id.user_id.name}</p>
                            #     <p>Auditor Department: {record.auditor_id.department_id.name}</p>
                            #     <p>Department To Audit: {record.auditor_id.department_ids.mapped('name')}</p>
                            #     <p>Auditees: {', '.join(record.auditor_id.selected_user_ids.mapped('name'))}</p>
                            #     <p>Target Date: {record.target_date}</p>
                            #     <p>Please ensure all preparations are complete.</p>
                            # </div>
                            # """,
                        })
                        
                        # Send mail to each individual user
                        template.send_mail(
                            record.id, 
                            email_values=mail_values,
                            force_send=True
                        )
                        _logger.info(f"Initial notification email sent to {user.name}")
                    except Exception as e:
                        _logger.error(f"Failed to send initial notification email to {user.name}: {e}")
                    
                # Mark as initial mail sent
                record.is_initial_mail_sent = True

    # def send_initial_notification(self):
    #     """Send initial notification when audit is started"""
    #     for record in self:
    #         try:
    #             # Skip if already sent
    #             if record.is_initial_mail_sent:
    #                 continue
                
    #             # Get email recipients
    #             email_list = record._get_email_recipients()
    #             print("----------- is_initial_mail_sent email_list -----------", email_list)
    #             if email_list:
    #                 # Prepare email template
    #                 template = self.env.ref('mgmtstem_modify.audit_initial_notification_template')
                    
    #                 # Set template values before sending
    #                 template_values = {'auto_delete': False}
    #                 template.write(template_values)
                    
    #                 for email in email_list:
    #                     try:
    #                         # Create a mail.mail record directly
    #                         mail_values = template.generate_email(
    #                             record.id, 
    #                             fields=['subject', 'body_html', 'email_from', 'email_to']
    #                         )
                            
    #                         # Explicitly set email_to and other values
    #                         mail_values.update({
    #                             'email_from': record.company_id.email or self.env.user.email or '',
    #                             'email_to': email,
    #                             'body_html': f"""
    #                                 <div>
    #                                 <p>Dear Team,</p>
    #                         mail_values: dict[str, str] = template.generate_email(
    #                                 <p>Reminder: Audit is approaching in {record.days_before} days</p>
    #                                 <p>Audit Name: {record.audit_id.name} </p>
    #                                 <p>Audit Ref. : {record.audit_id.reference}</p>
    #                                 <p>State : {record.audit_id.company_state}</p>
    #                                 <p>Plant Code : {record.audit_id.plant_name}</p>
    #                                 <p>System : {record.audit_id.system_id.name}</p>
    #                                 <p>Auditor: {record.auditor_id.user_id.name}</p>
    #                                 <p>Auditor Department: {record.auditor_id.department_id.name}</p>
    #                                 <p>Department To Audit: {record.auditor_id.department_ids.name}</p>
    #                                 <p>Auditees {record.auditor_id.selected_user_ids.name}</p>
    #                                 <p>Target Date: {record.target_date}</p>
    #                                 <p>Please ensure all preparations are complete.</p>
    #                                 </div>
    #                                 """,
    #                         })
                            
    #                         # Create and send mail
    #                         mail = self.env['mail.mail'].create(mail_values)
    #                         mail.send(raise_exception=True)
                            
    #                         _logger.info(f"Initial email sent successfully to: {email}")
    #                     except Exception as email_error:
    #                         _logger.error(f"Email send error for {email}: {email_error}")
                    
    #                 # record.is_initial_mail_sent = True
    #                 # Log activity for tracking
    #                 record.activity_schedule(
    #                     'mail.mail_activity_data_todo',
    #                     summary='Initial Audit Notification Sent',
    #                     note=f'Initial notification sent for Audit: {record.audit_id.name}'
    #                 )
    #         except Exception as e:
    #             _logger.error(f"Error sending initial notification: {str(e)}")

    def send_reminder_notification(self):
        """Send reminder notification for each day before target date"""
        try:
            today = date.today()
            notifications = self.search([
                ('target_date', '!=', False),
                ('is_reminder_mail_sent', '=', False)
            ])
            
            for record in notifications:
                # Calculate days between today and target date
                days_until_target = (record.target_date - today).days
                
                # Check if we're within the reminder window
                if 0 < days_until_target <= record.days_before:
                    # Get email recipients
                    email_list = record._get_email_recipients()
                    print("----------- reminder email_list -----------", email_list)
                    if email_list:
                        # Prepare email template
                        template = self.env.ref('mgmtstem_modify.audit_reminder_notification_template')
                        
                        # Set template values before sending
                        template_values = {'auto_delete': False}
                        template.write(template_values)
                        
                        for email in email_list:
                            try:
                                # Create a mail.mail record directly
                                mail_values = template.generate_email(
                                    record.id, 
                                    fields=['subject', 'body_html', 'email_from', 'email_to']
                                )
                                
                                # Explicitly set email_to
                                mail_values['email_to'] = email
                                
                                # Add context values to mail_values
                                mail_values.update({
                                    'email_from': self.company_id.email or self.env.user.email or '',
                                    'email_to': email,
                                    # 'body_html': f"""
                                    # <div>
                                    # <p>Dear Team,</p>
                                    # <p>Reminder: Audit is approaching in {record.days_before} days</p>
                                    # <p>Audit Name: {record.audit_id.name} </p>
                                    # <p>Audit Ref. : {record.audit_id.reference}</p>
                                    # <p>State : {record.audit_id.company_state}</p>
                                    # <p>Plant Code : {record.audit_id.plant_name}</p>
                                    # <p>System : {record.audit_id.system_id.name}</p>
                                    # <p>Auditor: {record.auditor_id.user_id.name}</p>
                                    # <p>Auditor Department: {record.auditor_id.department_id.name}</p>
                                    # <p>Department To Audit: {record.auditor_id.department_ids.name}</p>
                                    # <p>Auditees {record.auditor_id.selected_user_ids.name}</p>
                                    # <p>Target Date: {record.target_date}</p>
                                    # <p>Please ensure all preparations are complete.</p>
                                    # </div>
                                    # """,
                                })
                                print("----------- email template -----------", template)
                                print("----------- email template senders mail id-----------", template.email_from)
                                # print("----------- email mail_values !!!-----------", mail_values)
                                # Create and send mail
                                mail = self.env['mail.mail'].create(mail_values)
                                mail.send(raise_exception=True)
                                
                                print("----------- email template -----------", template)
                                _logger.info(f"Reminder email sent {days_until_target} days before target to: {email}")
                            except Exception as email_error:
                                _logger.error(f"Email send error for {email}: {email_error}")
                            print("----------- reminder email sent to -----------", email)
                        
                        # Only mark as sent if target date is reached
                        if days_until_target == 0:
                            record.is_reminder_mail_sent = True
                        
                        # Log activity for tracking
                        record.activity_schedule(
                            'mail.mail_activity_data_todo',
                            summary=f'Audit Reminder Notification Sent ({days_until_target} days before)',
                            note=f'Reminder notification sent for Audit: {record.audit_id.name}'
                        )
        except Exception as e:
            _logger.error(f"Error in send_reminder_notification: {e}")

    def _cron_send_reminders(self):
        """Cron method to send reminders"""
        self.send_reminder_notification()
        
class MgmtsystemAudit(models.Model):
    _inherit = "mgmtsystem.audit"

    def _create_or_update_target_notifications(self, auditors):
        notifications = []
        for auditor in auditors:
            # Find existing notification for this audit and auditor
            existing_notification = self.env['audit.target.notification'].search([
                ('audit_id', '=', self.id),
                ('auditor_id', '=', auditor.id)
            ])

            # Collect users from various sources
            users = self.env['res.users']
            
            # Add users from selected_user_ids in auditor
            if auditor.selected_user_ids:
                users |= auditor.selected_user_ids
            
            # Add user_id from audit
            if self.user_id:
                users |= self.user_id
            
            # Add users from all auditors
            users |= self.auditors_user_ids.mapped('user_id')

            # If notification exists, update users
            if existing_notification:
                existing_notification.user_ids = [(6, 0, users.ids)]
                notifications.append(existing_notification)
            # If no existing notification, create new
            else:
                new_notification = self.env['audit.target.notification'].create({
                    'audit_id': self.id,
                    'auditor_id': auditor.id,
                    'user_ids': [(6, 0, users.ids)],
                })
                notifications.append(new_notification)
        
        # Send initial notifications
        for notification in notifications:
            notification.send_initial_notification()
        
        return notifications

    def action_start(self):
        """Move audit to in progress state and create/update notifications"""
        res = super().action_start()
        
        # Create or update target notifications only if not already done
        existing_notifications = self.env['audit.target.notification'].search([
            ('audit_id', '=', self.id),
            ('is_initial_mail_sent', '=', False)
        ])
        
        # Only create/update notifications if no previous initial mail was sent
        if existing_notifications:
            self._create_or_update_target_notifications(self.auditors_user_ids)
        
        return res
    
    def write(self, vals):
        res = super().write(vals)
        
        # Check if auditors_user_ids have been modified
        if 'auditors_user_ids' in vals:
            for audit in self:
                audit._create_or_update_target_notifications(audit.auditors_user_ids)
        
        return res
    
    
    def action_approve(self):
        """Extend approval action to send completion notifications"""
        # Call parent method first
        res = super().action_approve()
        
        # Collect recipients
        recipients = self.env['res.users']
        
        # Add audit manager
        if self.user_id:
            recipients |= self.user_id
        
        # Add auditors' users
        recipients |= self.auditors_user_ids.mapped('user_id')
        
        # Ensure unique recipients
        recipients = recipients.filtered(lambda r: r.partner_id.email)
        
        # Send email notifications
        if recipients:
            # Reference the pre-existing template
            template = self.env.ref('mgmtstem_modify.audit_completion_notification_template')
            
            # Send emails to recipients
            for recipient in recipients:
                try:
                    template.send_mail(
                        self.id, 
                        email_values={'email_to': recipient.partner_id.email},
                        force_send=True
                    )
                    _logger.info(f"Audit completion email sent to {recipient.name}")
                except Exception as e:
                    _logger.error(f"Failed to send audit completion email to {recipient.name}: {e}")
        
        return res
    
    # def action_approve(self):
    #     """Extend approval action to send completion notifications"""
    #     # Call parent method first
    #     res = super().action_approve()
        
    #     # Collect recipients
    #     recipients = self.env['res.users']
        
    #     # Add audit manager
    #     if self.user_id:
    #         recipients |= self.user_id
        
    #     # Add auditors' users
    #     recipients |= self.auditors_user_ids.mapped('user_id')
        
    #     # Ensure unique recipients
    #     recipients = recipients.filtered(lambda r: r.partner_id.email)
        
    #     # Send email notifications
    #     if recipients:
    #         # Create mail template
    #         template = self.env['mail.template'].create({
    #             'name': f'Audit Completion Notification - {self.reference}',
    #             'model_id': self.env['ir.model'].search([('model', '=', 'mgmtsystem.audit')]).id,
    #             'subject': f'Audit Successfully Completed - {self.reference}',
    #             'body_html': f"""
    #             <div>
    #                 <p>Dear Team,</p>
    #                 <p>We are pleased to inform you that the audit has been successfully completed.</p>
    #                 <p><strong>Audit Details:</strong></p>
    #                 <ul>
    #                     <li>Audit Reference: {self.reference}</li>
    #                     <li>Audit Name: {self.name}</li>
    #                     <li>Audit Planned date: {self.date}</li>
    #                     <li>System: {self.system_id.name}</li>
    #                     <li>State: Approved</li>
    #                 </ul>
    #                 <p>Congratulations on successfully completing all audit activities.</p>
    #                 <p>Best regards,<br/>Management System Team</p>
    #             </div>
    #             """,
    #             'email_from': self.company_id.email or self.env.user.email,
    #             'auto_delete': False,
    #         })
            
    #         # Send emails to recipients
    #         for recipient in recipients:
    #             try:
    #                 template.send_mail(
    #                     self.id, 
    #                     email_values={'email_to': recipient.partner_id.email},
    #                     force_send=True
    #                 )
    #                 _logger.info(f"Audit completion email sent to {recipient.name}")
    #             except Exception as e:
    #                 _logger.error(f"Failed to send audit completion email to {recipient.name}: {e}")
            
    #         # Optional: Clean up template after use
    #         template.unlink()
        
    #     return res

class MgmtsystemAuditAuditor(models.Model):
    _inherit = "mgmtsystem.audit.auditor"
    
    def action_start(self):
        """Move to in progress state and create/update notifications"""
        res = super().action_start()
        
        # Create or update target notifications
        if self.audit_id:
            self.audit_id._create_or_update_target_notifications(self)
            # Find existing notifications to prevent duplicate sending
            existing_notifications = self.env['audit.target.notification'].search([
                ('audit_id', '=', self.audit_id.id),
                ('auditor_id', '=', self.id),
                ('is_initial_mail_sent', '=', False)
            ])
            
            # Only create/update notifications if no previous initial mail was sent
            if existing_notifications:
                self.audit_id._create_or_update_target_notifications(self)
    
        return res
    
    
    def write(self, vals):
        res = super().write(vals)
        
        # If selected_user_ids are modified
        if 'selected_user_ids' in vals:
            for auditor in self:
                # Find related audit target notifications
                notifications = self.env['audit.target.notification'].search([
                    ('auditor_id', '=', auditor.id)
                ])
                
                for notification in notifications:
                    # Collect users from various sources
                    users = self.env['res.users']
                    
                    # Add users from selected_user_ids in auditor
                    if auditor.selected_user_ids:
                        users |= auditor.selected_user_ids
                    
                    # Add user_id from audit
                    if notification.audit_id.user_id:
                        users |= notification.audit_id.user_id
                    
                    # Add users from all auditors
                    users |= notification.audit_id.auditors_user_ids.mapped('user_id')
                    
                    # Ensure unique users
                    users = users.filtered(lambda r: r.partner_id.email)
                    
                    # Update users in notification
                    notification.user_ids = [(6, 0, users.ids)]
                    
                    # Send initial notification to new users if needed
                    if users:
                        notification.send_initial_notification()
        
        return res























    # def write(self, vals):
    #     res = super().write(vals)
        
    #     # If selected_user_ids are modified
    #     if 'selected_user_ids' in vals:
    #         for auditor in self:
    #             # Find related audit target notifications
    #             notifications = self.env['audit.target.notification'].search([
    #                 ('auditor_id', '=', auditor.id)
    #             ])
                
    #             for notification in notifications:
    #                 # Get the current users before update
    #                 current_user_ids = set(notification.user_ids.ids)
                    
    #                 # Collect users from various sources
    #                 users = self.env['res.users']
                    
    #                 # Add users from selected_user_ids in auditor
    #                 if auditor.selected_user_ids:
    #                     users |= auditor.selected_user_ids
                    
    #                 # Add user_id from audit
    #                 if notification.audit_id.user_id:
    #                     users |= notification.audit_id.user_id
                    
    #                 # Add users from all auditors
    #                 users |= notification.audit_id.auditors_user_ids.mapped('user_id')
                    
    #                 # Update users in notification
    #                 notification.user_ids = [(6, 0, users.ids)]
                    
    #                 # Identify new users
    #                 new_user_ids = set(users.ids) - current_user_ids
                    
    #                 # If there are new users, send initial notification to them
    #                 if new_user_ids:
    #                     # Filter notification's users to only new users
    #                     new_users = self.env['res.users'].browse(list(new_user_ids))
                        
    #                     # Temporarily modify user_ids to only include new users
    #                     original_users = notification.user_ids
    #                     notification.user_ids = [(6, 0, list(new_user_ids))]
                        
    #                     try:
    #                         # Send initial notification to new users
    #                         notification.send_initial_notification()
    #                     except Exception as e:
    #                         self.env.cr.rollback()
    #                         _logger.error(f"Error sending initial notification to new users: {e}")
    #                     finally:
    #                         # Restore original user list
    #                         notification.user_ids = original_users
        
    #     return res
    