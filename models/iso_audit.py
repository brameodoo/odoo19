# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class IsoAudit(models.Model):
    _name = 'iso.audit'
    _description = 'Auditoría Interna de Proceso'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Folio Auditoría', required=True, copy=False, readonly=True, default=lambda self: _('Nuevo'))
    format_code = fields.Char(string='Código de Formato', default='F-CAL-15_R01', readonly=True)
    cdo_id = fields.Many2one('audit.cdo', string='CDO / Estación', required=True, tracking=True)
    
    process_name = fields.Char(string='Proceso', required=True, tracking=True)
    procedure_name = fields.Char(string='Procedimiento', required=True, tracking=True)
    
    auditor_id = fields.Many2one('res.users', string='Auditor Líder', required=True, default=lambda self: self.env.user, tracking=True)
    audited_employee_id = fields.Many2one('hr.employee', string='Auditado(s)')
    audited_job_title = fields.Char(string='Puesto(s)')
    department_id = fields.Many2one('hr.department', string='Área')
    
    date = fields.Date(string='Fecha', default=fields.Date.context_today, required=True)
    time = fields.Char(string='Hora')
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Proceso'),
        ('done', 'Realizada / Cerrada'),
        ('cancel', 'Cancelada')
    ], string='Estado', default='draft', tracking=True)

    line_ids = fields.One2many('audit.checklist.line', 'audit_id', string='Líneas del Checklist')
    ncr_ids = fields.One2many('quality.ncr', 'audit_id', string='No Conformidades')
    ncr_count = fields.Integer(string='Núm. NCRs', compute='_compute_ncr_count')

    # Métricas y ponderaciones exactas del F-CAL-15_R01
    org_total_applicable = fields.Integer(string='Preguntas Aplicables (Org)', compute='_compute_audit_scores', store=True)
    org_total_compliant = fields.Integer(string='Cumple (Org)', compute='_compute_audit_scores', store=True)
    org_total_non_compliant = fields.Integer(string='No Cumple (Org)', compute='_compute_audit_scores', store=True)
    org_compliance_rate = fields.Float(string='% Cumplimiento Org (30%)', compute='_compute_audit_scores', store=True)

    op_total_applicable = fields.Integer(string='Preguntas Aplicables (Oper)', compute='_compute_audit_scores', store=True)
    op_total_compliant = fields.Integer(string='Cumple (Oper)', compute='_compute_audit_scores', store=True)
    op_total_non_compliant = fields.Integer(string='No Cumple (Oper)', compute='_compute_audit_scores', store=True)
    op_compliance_rate = fields.Float(string='% Cumplimiento Oper (70%)', compute='_compute_audit_scores', store=True)

    global_compliance_rate = fields.Float(string='Cumplimiento Global', compute='_compute_audit_scores', store=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('iso.audit.seq') or _('Nuevo')
        return super().create(vals_list)

    @api.depends('line_ids.result', 'line_ids.criteria_type')
    def _compute_audit_scores(self):
        for audit in self:
            org_lines = audit.line_ids.filtered(lambda l: l.criteria_type == 'organizational')
            op_lines = audit.line_ids.filtered(lambda l: l.criteria_type == 'operational')

            # Criterios Organizacionales
            org_app = org_lines.filtered(lambda l: l.result in ('compliant', 'non_compliant'))
            org_comp = org_lines.filtered(lambda l: l.result == 'compliant')
            org_non_comp = org_lines.filtered(lambda l: l.result == 'non_compliant')
            
            audit.org_total_applicable = len(org_app)
            audit.org_total_compliant = len(org_comp)
            audit.org_total_non_compliant = len(org_non_comp)
            audit.org_compliance_rate = (len(org_comp) / len(org_app) * 0.30) if org_app else 0.0

            # Criterios Operativos
            op_app = op_lines.filtered(lambda l: l.result in ('compliant', 'non_compliant'))
            op_comp = op_lines.filtered(lambda l: l.result == 'compliant')
            op_non_comp = op_lines.filtered(lambda l: l.result == 'non_compliant')
            
            audit.op_total_applicable = len(op_app)
            audit.op_total_compliant = len(op_comp)
            audit.op_total_non_compliant = len(op_non_comp)
            audit.op_compliance_rate = (len(op_comp) / len(op_app) * 0.70) if op_app else 0.0

            # Cumplimiento Global (Suma directa de contribuciones porcentuales)
            audit.global_compliance_rate = audit.org_compliance_rate + audit.op_compliance_rate

    @api.depends('ncr_ids')
    def _compute_ncr_count(self):
        for audit in self:
            audit.ncr_count = len(audit.ncr_ids)

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        # Candado: No cerrar si existen reactivos sin evaluar
        for audit in self:
            unscored = audit.line_ids.filtered(lambda l: not l.result or l.result == 'not_scored')
            if unscored:
                raise UserError(_("No es posible cerrar la auditoría. Hay %s preguntas sin evaluar.") % len(unscored))
        self.write({'state': 'done'})

    def action_view_ncrs(self):
        self.ensure_one()
        return {
            'name': _('No Conformidades'),
            'type': 'ir.actions.act_window',
            'res_model': 'quality.ncr',
            'view_mode': 'list,form',
            'domain': [('audit_id', '=', self.id)],
            'context': {'default_audit_id': self.id, 'default_cdo_id': self.cdo_id.id},
        }
