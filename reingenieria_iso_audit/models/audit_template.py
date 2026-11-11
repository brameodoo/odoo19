# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AuditTemplate(models.Model):
    _name = 'audit.template'
    _description = 'Plantilla de Lista de Verificación / Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre de la Plantilla', required=True, tracking=True)
    code = fields.Char(string='Código de Control / Versión', default='F-CAL-15_R01', tracking=True)
    standard = fields.Selection([
        ('iso9001_2015', 'ISO 9001:2015'),
        ('iso14001', 'ISO 14001:2015'),
        ('iso45001', 'ISO 45001:2018'),
        ('internal', 'Procedimiento Interno / Operativo'),
    ], string='Norma / Alcance', default='iso9001_2015', required=True)

    description = fields.Text(string='Descripción / Objetivo')
    active = fields.Boolean(string='Activo', default=True)
    line_ids = fields.One2many('audit.template.line', 'template_id', string='Reactivos de la Plantilla')
    line_count = fields.Integer(string='Total de Reactivos', compute='_compute_line_count')

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    def action_generate_audit_lines(self, audit):
        """Genera las líneas de verificación dentro de una auditoría a partir de esta plantilla."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("La plantilla seleccionada no cuenta con reactivos configurados."))

        lines_to_create = []
        for line in self.line_ids:
            lines_to_create.append((0, 0, {
                'item_number': line.sequence,
                'criteria_type': line.criteria_type,
                'iso_clause': line.iso_clause,
                'question': line.question,
                'context': line.context,
                'expected_evidence': line.expected_evidence,
                'result': 'not_scored',
            }))
        audit.write({'line_ids': lines_to_create})


class AuditTemplateLine(models.Model):
    _name = 'audit.template.line'
    _description = 'Reactivo Base de Plantilla'
    _order = 'sequence asc, id asc'

    template_id = fields.Many2one('audit.template', string='Plantilla', ondelete='cascade', required=True)
    sequence = fields.Integer(string='Secuencia / ID', default=10)
    criteria_type = fields.Selection([
        ('organizational', 'Criterio Organizacional (Ponderación 30%)'),
        ('operational', 'Criterio Operativo (Ponderación 70%)')
    ], string='Tipo de Criterio', required=True, default='organizational')

    iso_clause = fields.Char(string='Cláusula ISO / Requisito')
    question = fields.Text(string='Pregunta de Auditoría', required=True)
    context = fields.Text(string='Contexto / Objetivo de Evaluación')
    expected_evidence = fields.Text(string='Evidencia Esperada / Registros Solicitados')
