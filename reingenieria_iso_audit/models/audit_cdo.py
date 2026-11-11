# -*- coding: utf-8 -*-
from odoo import models, fields

class AuditCDO(models.Model):
    _name = 'audit.cdo'
    _description = 'Centro de Operaciones (CDO)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(string='Código CDO', required=True, tracking=True)  # Ej. "1. Corporativo SF" o "CDO-01"
    name = fields.Char(string='Nombre de Estación', required=True, tracking=True)
    state_id = fields.Many2one('res.country.state', string='Estado / Entidad Federativa')
    city = fields.Char(string='Ciudad / Plaza')
    responsible_user_id = fields.Many2one('res.users', string='Responsable Operativo CDO')
    active = fields.Boolean(default=True)
    audit_ids = fields.One2many('iso.audit', 'cdo_id', string='Auditorías Realizadas')
    ncr_count = fields.Integer(string='Total NCRs', compute='_compute_ncr_count')

    def _compute_ncr_count(self):
        for rec in self:
            rec.ncr_count = self.env['quality.ncr'].search_count([('cdo_id', '=', rec.id)])
