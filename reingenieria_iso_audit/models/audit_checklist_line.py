# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AuditChecklistLine(models.Model):
    _name = 'audit.checklist.line'
    _description = 'Reactivo de Auditoría'
    _order = 'item_number asc, id asc'

    audit_id = fields.Many2one('iso.audit', string='Auditoría', ondelete='cascade', required=True)
    item_number = fields.Integer(string='ID')
    criteria_type = fields.Selection([
        ('organizational', 'Criterio Organizacional'),
        ('operational', 'Criterio Operativo')
    ], string='Tipo de Criterio', required=True)
    
    iso_clause = fields.Char(string='Norma ISO y Requisitos Internos')
    question = fields.Text(string='Pregunta', required=True)
    context = fields.Text(string='Contexto')
    expected_evidence = fields.Text(string='Evidencia Esperada')

    result = fields.Selection([
        ('not_scored', 'Sin Evaluar'),
        ('compliant', 'Cumple'),
        ('non_compliant', 'No Cumple'),
        ('not_applicable', 'No Aplica')
    ], string='Resultado', default='not_scored', required=True)

    objective_evidence = fields.Text(string='Evidencia Objetiva Encontrada')
    breached_requirement = fields.Char(string='Requisito Incumplido')
    risk_impact = fields.Text(string='Riesgo o Impacto')
    comments = fields.Text(string='Comentarios / Observaciones')
    
    finding_description = fields.Text(string='Descripción del Hallazgo', compute='_compute_finding_description', store=True)
    evidence_attachment_ids = fields.Many2many('ir.attachment', string='Archivos de Evidencia')
    ncr_id = fields.Many2one('quality.ncr', string='NCR Generada', readonly=True)

    @api.depends('result', 'objective_evidence', 'breached_requirement', 'risk_impact', 'audit_id.procedure_name', 'audit_id.process_name')
    def _compute_finding_description(self):
        for line in self:
            if line.result == 'non_compliant':
                audit = line.audit_id
                proc = audit.procedure_name or ''
                proc_base = audit.process_name or ''
                evid = line.objective_evidence or ''
                req = line.breached_requirement or line.iso_clause or ''
                risk = line.risk_impact or ''
                line.finding_description = (
                    f"Durante la auditoría realizada al procedimiento '{proc}' del proceso '{proc_base}', "
                    f"se identificó como evidencia objetiva que '{evid}'. Esta situación evidencia el incumplimiento "
                    f"del requisito '{req}'. La condición identificada puede generar el siguiente riesgo o impacto: {risk}."
                )
            else:
                line.finding_description = False

    def action_create_ncr(self):
        self.ensure_one()
        if self.ncr_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'quality.ncr',
                'res_id': self.ncr_id.id,
                'view_mode': 'form',
            }
        
        ncr_vals = {
            'audit_id': self.audit_id.id,
            'checklist_line_id': self.id,
            'cdo_id': self.audit_id.cdo_id.id,
            'clause': self.iso_clause or self.breached_requirement,
            'description': self.finding_description or self.question,
            'immediate_containment': 'Segregación y notificación inmediata a la jefatura de área.',
        }
        ncr = self.env['quality.ncr'].create(ncr_vals)
        self.ncr_id = ncr.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'quality.ncr',
            'res_id': ncr.id,
            'view_mode': 'form',
        }
