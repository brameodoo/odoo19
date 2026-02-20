# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustodiaService(models.Model):
    _name = 'custodia.service'
    _description = 'Servicio de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'sequence desc, create_date desc'
    current_lat = fields.Float(tracking=True)
    current_lng = fields.Float(tracking=True)
    last_update = fields.Datetime(tracking=True)

    # Identificador legible
    name = fields.Char(
        string='Folio del Servicio',
        required=True,
        copy=False,
        index=True,
        default='Nuevo'
    )

    # Consecutivo interno
    sequence = fields.Char(
        string='Consecutivo',
        copy=False,
        readonly=True,
        default='Nuevo'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        domain=[('is_company', '=', True)],
        tracking=True
    )
    contact_id = fields.Many2one(
        'res.partner',
        string='Persona solicitante',
        required=True,
        domain="[('parent_id','=',partner_id)]",
        tracking=True
    )

    carrier_id = fields.Many2one(
        'custodia.carrier',
        string='Carrier',
        required=True,
        tracking=True
    )
    ruta_id = fields.Many2one(
        'custodia.ruta',
        string='Ruta',
        required=True,
        tracking=True
    )
    ruta_tipo = fields.Selection(
        [('local', 'Local'), ('foraneo', 'Foráneo')],
        string='Tipo de ruta',
        related='ruta_id.tipo',
        store=True
    )

    start_datetime = fields.Datetime(
        string='Inicio del servicio',
        required=True,
        tracking=True
    )
    nivel_seguridad = fields.Selection(
        [
            ('1', 'Nivel 1'),
            ('2', 'Nivel 2'),
            ('3', 'Nivel 3'),
            ('4', 'Nivel 4'),
            ('4x', 'Excepción + Nivel 4'),
        ],
        string='Nivel de seguridad',
        required=True,
        tracking=True
    )
    load_id = fields.Char(
        string='Load ID',
        required=True,
        index=True,
        tracking=True
    )

    tipo_unidad = fields.Char(
        string='Tipo de unidad',
        tracking=True
    )
    placas = fields.Char(
        string='Placas',
        tracking=True
    )
    transporte = fields.Char(
        string='Transporte',
        tracking=True
    )
    operador1_nombre = fields.Char(
        string='Operador 1',
        tracking=True
    )
    operador1_licencia = fields.Char(
        string='Licencia Operador 1',
        tracking=True
    )
    operador2_nombre = fields.Char(
        string='Operador 2',
        tracking=True
    )
    operador2_licencia = fields.Char(
        string='Licencia Operador 2',
        tracking=True
    )
    tel_monitoreo_1 = fields.Char(
        string='Teléfono Monitoreo 1',
        tracking=True
    )
    tel_monitoreo_2 = fields.Char(
        string='Teléfono Monitoreo 2',
        tracking=True
    )
    start_coords = fields.Char(
        string='Coordenadas de inicio',
        tracking=True
    )
    end_coords = fields.Char(
        string='Coordenadas de llegada',
        tracking=True
    )
    comentarios_cliente = fields.Text(
        string='Comentarios del Cliente',
        tracking=True
    )

    # Relación hijo
    asignacion_ids = fields.One2many(
        'custodia.asignacion',
        'service_id',
        string='Asignaciones'
    )

    state = fields.Selection(
        [
            ('solicitado', 'Solicitado'),
            ('aprobado', 'Aprobado'),
            ('asignado', 'Asignado'),
            ('en_ejecucion', 'En ejecución'),
            ('finalizado', 'Finalizado'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado',
        default='solicitado',
        tracking=True,
        index=True
    )

    planner_id = fields.Many2one(
        'res.users',
        string='Planeador',
        tracking=True
    )

    tracking_ids = fields.One2many(
        'custodia.service.tracking',
        'service_id'
    )

    # Autogenerar nombre y secuencia
    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if vals.get('sequence', 'Nuevo') == 'Nuevo':
                vals['sequence'] = self.env['ir.sequence'].next_by_code('custodia.service') or 'Nuevo'
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = vals['sequence']

        return super(CustodiaService, self).create(vals_list)

    # Botones de acción para flujo de estados
    def action_aprobar(self):
        self.write({'state': 'aprobado'})

    def action_asignar(self):
        self.write({'state': 'asignado'})

    def action_ejecutar(self):
        self.write({'state': 'en_ejecucion'})

    def action_finalizar(self):
        self.write({'state': 'finalizado'})

    def action_cancelar(self):
        self.write({'state': 'cancelado'})

    # --- MÉTODO PARA TIEMPO REAL ---
