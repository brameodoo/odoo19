# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

class QualityNCR(models.Model):
    _name = 'quality.ncr'
    _description = 'Reporte de No Conformidad'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Folio NCR', required=True, copy=False, readonly=True, default=lambda self: _('Nuevo'))
    audit_id = fields.Many2one('iso.audit', string='Auditoría de Origen', readonly=True)
    checklist_line_id = fields.Many2one('audit.checklist.line', string='Reactivo Origen', readonly=True)
    cdo_id = fields.Many2one('audit.cdo', string='CDO', required=True)
    
    clause = fields.Char(string='Cláusula / Requisito')
    severity = fields.Selection([
        ('minor', 'Menor'),
        ('major', 'Mayor'),
        ('critical', 'Crítica')
    ], string='Severidad', default='minor', required=True, tracking=True)
    
    responsible_user_id = fields.Many2one('res.users', string='Responsable de Atención', tracking=True)
    deadline_date = fields.Date(string='Fecha Límite')
    
    description = fields.Text(string='Descripción de la Desviación', required=True)
    immediate_containment = fields.Text(string='Acción de Contención Inmediata')

    # Metodología de Causa Raíz: 5 Porqués
    why_1 = fields.Char(string='1er Por qué')
    why_2 = fields.Char(string='2do Por qué')
    why_3 = fields.Char(string='3er Por qué')
    why_4 = fields.Char(string='4to Por qué')
    why_5 = fields.Char(string='5to Por qué')
    root_cause_conclusion = fields.Text(string='Conclusión de Causa Raíz', tracking=True)

    state = fields.Selection([
        ('open', 'Abierta'),
        ('investigating', 'En Análisis (5 Porqués)'),
        ('action_planned', 'CAPA Planificada'),
        ('verifying', 'Verificación de Eficacia'),
        ('closed', 'Cerrada')
    ], string='Estado', default='open', tracking=True)

    capa_ids = fields.One2many('quality.capa', 'ncr_id', string='Acciones Correctivas (CAPA)')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('quality.ncr.seq') or _('Nuevo')
        return super().create(vals_list)

    def action_close(self):
        # Candado ISO: No cerrar si existen CAPAs pendientes de eficacia
        for ncr in self:
            open_capas = ncr.capa_ids.filtered(lambda c: c.state != 'verified_effective')
            if open_capas:
                raise UserError(_("No puede cerrar la NCR. Todas las CAPAs vinculadas deben estar en estado 'Eficacia Verificada'."))
        self.write({'state': 'closed'})


class QualityCAPA(models.Model):
    _name = 'quality.capa'
    _description = 'Acción Correctiva / Preventiva (CAPA)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Folio CAPA', required=True, copy=False, readonly=True, default=lambda self: _('Nuevo'))
    ncr_id = fields.Many2one('quality.ncr', string='NCR Relacionada', required=True, ondelete='cascade')
    description = fields.Text(string='Plan de Acción', required=True)
    responsible_user_id = fields.Many2one('res.users', string='Responsable Ejecución', required=True)
    
    date_implemented = fields.Date(string='Fecha de Implementación')
    effectiveness_due_date = fields.Date(string='Fecha Programada Verificación')
    effectiveness_evidence = fields.Text(string='Evidencia de Eficacia')
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Ejecución'),
        ('pending_verification', 'Pendiente Verificación'),
        ('verified_effective', 'Eficacia Verificada'),
        ('ineffective', 'No Eficaz')
    ], string='Estado', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('quality.capa.seq') or _('Nuevo')
        return super().create(vals_list)

    def action_mark_implemented(self):
        # Programa automáticamente la verificación a 30 días
        today = fields.Date.context_today(self)
        self.write({
            'state': 'pending_verification',
            'date_implemented': today,
            'effectiveness_due_date': today + timedelta(days=30)
        })
        self.ncr_id.write({'state': 'verifying'})

    def action_verify_effective(self):
        if not self.effectiveness_evidence:
            raise UserError(_("Debe documentar la 'Evidencia de Eficacia' antes de validar este paso."))
        self.write({'state': 'verified_effective'})
