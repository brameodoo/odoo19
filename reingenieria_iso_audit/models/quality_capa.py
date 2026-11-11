# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class QualityCAPA(models.Model):
    _name = 'quality.capa'
    _description = 'Acción Correctiva / Preventiva (CAPA)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Folio CAPA',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo'),
    )
    ncr_id = fields.Many2one(
        'quality.ncr', string='NCR Relacionada', required=True, ondelete='cascade'
    )
    description = fields.Text(string='Plan de Acción', required=True)
    responsible_user_id = fields.Many2one(
        'res.users', string='Responsable Ejecución', required=True
    )

    date_implemented = fields.Date(string='Fecha de Implementación')
    effectiveness_due_date = fields.Date(string='Fecha Programada Verificación')
    effectiveness_evidence = fields.Text(string='Evidencia de Eficacia')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Ejecución'),
        ('pending_verification', 'Pendiente Verificación'),
        ('verified_effective', 'Eficacia Verificada'),
        ('ineffective', 'No Eficaz'),
    ], string='Estado', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('quality.capa.seq') or _('Nuevo')
                )
        return super().create(vals_list)

    def action_mark_implemented(self):
        today = fields.Date.context_today(self)
        self.write({
            'state': 'pending_verification',
            'date_implemented': today,
            'effectiveness_due_date': today + timedelta(days=30),
        })
        self.ncr_id.write({'state': 'verifying'})

    def action_verify_effective(self):
        if not self.effectiveness_evidence:
            raise UserError(
                _("Debe documentar la 'Evidencia de Eficacia' antes de validar este paso.")
            )
        self.write({'state': 'verified_effective'})
