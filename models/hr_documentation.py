# -*- coding: utf-8 -*-

import logging
import itertools
from werkzeug import url_encode
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError
from odoo.modules.module import get_module_resource
from odoo.addons.resource.models.resource_mixin import timezone_datetime


#flow configuration class
_logger = logging.getLogger(__name__)
class HrDocumentation(models.Model):
    _name = 'hr.documentation'
    _description = 'Documentation Flow config'
    
    name = fields.Char(string="Flow name")
    description = fields.Text(string="Description")
    o2m_flow_objects = fields.One2many("hr.documentation.objects", "m2o_documentation", string="Objects")
    

#class for objects/steps of configuration  
class HrDocumentationObjets(models.Model):
    _name = 'hr.documentation.objects'
    _description = 'Documentation Flow config objects'
    
    name = fields.Char(string="Flow name")
    m2o_documentation = fields.Many2one("hr.documentation", string="Docuemntation", index=True)
    description = fields.Text(string="Description")
    flow_type = fields.Selection([
        ('manager', 'Manager'),
        ('department_head', 'Dep. Manager'),
        ('employee', 'Employee')], string="Type")
    m2o_employee = fields.Many2one('hr.employee', string='Employee')
    m2o_departments = fields.Many2one('hr.department', string="departmetns")
    
#class where document is created and moving by configured flow
class HrDocumentationFlow(models.Model):
    _name = 'hr.documentation.flow'
    _description = "Documentation flow"
    
    name = fields.Char(string = "Name/identifier")
    description = fields.Text(string="Description")
    m2o_documentation = fields.Many2one("hr.documentation", string="Docuemntation")
    m2o_employee = fields.Many2one('hr.employee', string='Initator')

    o2m_flow_objects = fields.One2many('hr.documentation.flow.objects', 'm2o_flow', string='Flow')
    m2o_validator_employee = fields.Many2one('hr.employee', string='Validator')
    m2o_validator_user = fields.Many2one('res.users', string='Validator user')
    enable_to_validate = fields.Boolean(compute = '_compute_enable_to_validate', string="Validate enabled")
    attach_document = fields.Binary(string="Attachment", attachment=True, help="Attach file on which this record is based on")
    attach_doc_name = fields.Char("File name")
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('canceled', 'Canceled')
    ], string="state", default='new')
    cancel_reason = fields.Text("Cancelation Reason")
    
    
    def _compute_enable_to_validate(self):
        for record in self:
            try: record.enable_to_validate = True if self.env.uid == record.m2o_validator_user.id else False
            except:
                record.enable_to_validate = False
                _logger.exception("no enough data")
    
    
    def cancel(self):
        if self.m2o_validator_user.id == self.env.uid:
            action_id = self.env.ref('hr_documentation_flow.view_documenation_flow_action_popup')
            needed_context = {'default_record_id':self.id, 'default_action_type':'cancel'}
            return {
                'name': action_id.name,
                'type': 'ir.actions.act_window',
                'res_model': 'hr.documentation.popups',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': needed_context,
            }
           
    def validate(self):
        if self.m2o_validator_user.id == self.env.uid:
            action_id = self.env.ref('hr_documentation_flow.view_documenation_flow_action_popup')
            needed_context = {'default_record_id':self.id, 'default_action_type':'validate'}
            return {
                'name': action_id.name,
                'type': 'ir.actions.act_window',
                'res_model': 'hr.documentation.popups',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': needed_context,
            }
            
        else:
            raise ValidationError(_("This record need not your validation yet"))
    
    @api.model
    def create(self, vals):
        flow_objects = []
        employee_id = None
        if vals.get('m2o_documentation'):
            predefined_flow_id = vals.get('m2o_documentation')
            flow_objects = self.env['hr.documentation.objects'].sudo().search(
                [('m2o_documentation','=', predefined_flow_id)])
            flow_objects = [obj for obj in flow_objects]
            
        document = super(HrDocumentationFlow, self).create(vals)
        #define employee
        if not vals.get('m2o_employee'):
            created_record = self.env['hr.documentation.flow'].sudo().browse(document.id)
            uid = created_record.create_uid
            employee_id = self.env['hr.employee'].sudo().search([('user_id','=', int(uid))])
            created_record.write({'m2o_employee':employee_id.id})

        else:
            employee_id = self.env['hr.employee'].sudo().search([('id','=',vals.get('m2o_employee'))])
            
        # create records for flow
        if len(flow_objects):
            last_employee_id = employee_id
            #create record for the first stage, initiators stage
            self.env['hr.documentation.flow.objects'].create(
                        {'m2o_flow':document.id, 'm2o_employee':last_employee_id.id, 'in_out':'in'})
            document.write({'m2o_validator_employee':last_employee_id.id,
                            'm2o_validator_user':last_employee_id.user_id.id})
            
            # loop through predefined stages
            for record in flow_objects:
                #create record by type of flow object
                if record.flow_type == 'manager':
                    new_employee_id = last_employee_id.parent_id if last_employee_id.parent_id else last_employee_id
                    in_out = 'waiting'
                    # create record
                    self.env['hr.documentation.flow.objects'].create(
                        {'m2o_flow':document.id, 'm2o_employee':new_employee_id.id, 'in_out':in_out})
                    last_employee_id = new_employee_id
                    
                elif record.flow_type == 'department_head':
                    new_employee_id = record.m2o_departments.manager_id if record.m2o_departments else last_employee_id
                    in_out = 'waiting'
                    # create record
                    self.env['hr.documentation.flow.objects'].create(
                        {'m2o_flow':document.id, 'm2o_employee':new_employee_id.id, 'in_out':in_out})
                    last_employee_id = new_employee_id
                    
                elif record.flow_type == 'employee':
                    new_employee_id = record.m2o_employee 
                    in_out = 'waiting'
                    # create record
                    self.env['hr.documentation.flow.objects'].create(
                        {'m2o_flow':document.id, 'm2o_employee':new_employee_id.id, 'in_out':in_out})
                    last_employee_id = new_employee_id
            
        return document
    
#documentation flow of employees
class HrDocumentationFlowObject(models.Model):
    _name = 'hr.documentation.flow.objects'
    _description = "Flow objects"
    _rec_name = "m2o_employee"
    
    m2o_flow = fields.Many2one('hr.documentation.flow', string='m2o to flow', index=True)
    m2o_employee = fields.Many2one('hr.employee', string='Employee', index=True)
    comment = fields.Text(string="Comment")

    in_out = fields.Selection([('waiting','waiting'), ('in','in'),('out','out')], string='position', default='out')



#class for popup records when we need nnot to save any data, just using them as temporary info holders
class HrDocumentationPopUps(models.TransientModel):
    _name = 'hr.documentation.popups'
    _descrtiption = 'Documentation popups'
    
    record_id = fields.Char(string = "Id", help="field where we store id from the record it was initated")
    comment = fields.Text(string="Comment")
    action_type = fields.Selection([('cancel','Cancel'),('validate','Validate')])
    
    def validate(self):
        # raise AccessError(_(self))
        flow_record = self.env['hr.documentation.flow'].search([('id','=',int(self.record_id))])
        flow_objs = self.env['hr.documentation.flow.objects']
        current_stage = flow_objs.search([('m2o_flow','=',flow_record.id),('in_out','=','in')])
        next_stages = flow_objs.search([('m2o_flow','=',flow_record.id),('in_out','=','waiting')])
        if current_stage.m2o_employee.user_id.id == self.env.uid:
            current_stage.write({'in_out':'out','comment':self.comment})
            enable_to_validate = False
            if next_stages:
                next_stage = next_stages[0]
                next_stage.write({'in_out':'in'})
                flow_record.m2o_validator_employee = next_stage.m2o_employee.id
                flow_record.m2o_validator_user = next_stage.m2o_employee.user_id.id
                if flow_record.state != '':
                    flow_record.write({'state':'in_progress'})
                    
            else:
                current_stage.write({'in_out':'out','comment':self.comment})
                flow_record.write({'state':'done'})
                
                
        else:
            raise ValidationError(_("This record need not your validation yet"))

    def cancel(self):
        flow_record = self.env['hr.documentation.flow'].search([('id','=',int(self.record_id))])
        flow_objs = self.env['hr.documentation.flow.objects'].search([('m2o_flow','=',flow_record.id)]).write({'in_out':'waiting'})
        flow_record.write({'state':'canceled','cancel_reason':self.comment})
        







