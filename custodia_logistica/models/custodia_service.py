# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CustodiaService(models.Model):
    _name = 'custodia.service'
    _description = 'Servicio de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'sequence desc, create_date desc'

    # =========================
    # CAMPOS DE UBICACIÓN LIVE
    # =========================
    current_lat = fields.Float(string="Latitud Actual", tracking=True)
    current_lng = fields.Float(string="Longitud Actual", tracking=True)
    last_update = fields.Datetime(string="Última Actualización", tracking=True)

    # =========================
    # IDENTIFICADORES
    # =========================
    name = fields.Char(
        string='Folio del Servicio',
        required=True,
        copy=False,
        index=True,
        default='Nuevo'
    )

    sequence = fields.Char(
        string='Consecutivo',
        copy=False,
        readonly=True,
        default='Nuevo'
    )

    # =========================
    # RELACIONES
    # =========================
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

   # ruta_tipo = fields.Selection(
   #     [('local', 'Local'), ('foraneo', 'Foráneo')],
   #     string='Tipo de ruta',
   #     related='ruta_id.tipo',
   #     store=True
   # )

    ruta_tipo = fields.Selection(
        related='ruta_id.tipo',
        string='Tipo de ruta',
        store=True,
        readonly=True
    )

    planner_id = fields.Many2one(
        'res.users',
        string='Planeador',
        tracking=True
    )

    # =========================
    # DATOS OPERATIVOS
    # =========================
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



    tipo_unidad = fields.Char(string='Tipo de unidad', tracking=True)
    placas = fields.Char(string='Placas', tracking=True)
    transporte = fields.Char(string='Transporte', tracking=True)

    operador1_nombre = fields.Char(string='Operador 1', tracking=True)
    operador1_licencia = fields.Char(string='Licencia Operador 1', tracking=True)
    operador2_nombre = fields.Char(string='Operador 2', tracking=True)
    operador2_licencia = fields.Char(string='Licencia Operador 2', tracking=True)

    tel_monitoreo_1 = fields.Char(string='Teléfono Monitoreo 1', tracking=True)
    tel_monitoreo_2 = fields.Char(string='Teléfono Monitoreo 2', tracking=True)

    start_coords = fields.Char(string='Coordenadas de inicio', tracking=True)
    end_coords = fields.Char(string='Coordenadas de llegada', tracking=True)

    comentarios_cliente = fields.Text(
        string='Comentarios del Cliente',
        tracking=True
    )

    # =========================
    # RELACIONES HIJAS
    # =========================
    asignacion_ids = fields.One2many(
        'custodia.asignacion',
        'service_id',
        string='Asignaciones'
    )

    tracking_ids = fields.One2many(
        'custodia.service.tracking',
        'service_id',
        string='Historial de Ubicaciones'
    )

    # =========================
    # ESTADO
    # =========================
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

    # =========================
    # TIEMPOS REALES Y CONTROL
    # =========================
    
    hora_llegada = fields.Datetime(string='Hora de llegada custodio', tracking=True)
    hora_inicio_real = fields.Datetime(string='Hora de inicio real', tracking=True)
    
    diff_llegada_min = fields.Integer(
        string='Diferencia llegada (min)', 
        compute='_compute_diferencias'
    )
    diff_inicio_min = fields.Integer(
        string='Diferencia inicio (min)', 
        compute='_compute_diferencias'
    )

    @api.depends('start_datetime', 'hora_llegada', 'hora_inicio_real')
    def _compute_diferencias(self):
        for record in self:
            diff_llegada = 0
            diff_inicio = 0
            if record.start_datetime:
                if record.hora_llegada:
                    diff = (record.hora_llegada - record.start_datetime).total_seconds() / 60
                    diff_llegada = int(diff)
                if record.hora_inicio_real:
                    diff = (record.hora_inicio_real - record.start_datetime).total_seconds() / 60
                    diff_inicio = int(diff)
            record.diff_llegada_min = diff_llegada
            record.diff_inicio_min = diff_inicio

    # =========================
    # CREATE (SECUENCIA)
    # =========================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('sequence', 'Nuevo') == 'Nuevo':
                vals['sequence'] = self.env['ir.sequence'].next_by_code(
                    'custodia.service'
                ) or 'Nuevo'

            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = vals['sequence']

        return super().create(vals_list)

    # =========================
    # FLUJO DE ESTADOS
    # =========================
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

    # =========================
    # MÉTODO TIEMPO REAL
    # =========================
    def update_live_location(self, lat, lng):
        """Actualiza la ubicación en tiempo real del servicio"""
        self.ensure_one()

        now = fields.Datetime.now()

        # Actualiza ubicación actual
        self.write({
            'current_lat': lat,
            'current_lng': lng,
            'last_update': now
        })

        # Crear registro histórico
        self.env['custodia.service.tracking'].create({
            'service_id': self.id,
            'latitude': lat,
            'longitude': lng,
            'timestamp': now
        })

        return True
