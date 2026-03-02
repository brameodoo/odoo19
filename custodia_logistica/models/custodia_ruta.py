# -*- coding: utf-8 -*-

from odoo import models, fields


class CustodiaRuta(models.Model):
    _name = 'custodia.ruta'
    _description = 'Ruta Comercial de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # =========================
    # INFORMACIÓN GENERAL
    # =========================

    name = fields.Char(
        string='Nombre de la Ruta',
        required=True,
        tracking=True,
        help="Ejemplo: GDL - Ciudad Juárez"
    )

    tipo = fields.Selection(
        [
            ('local', 'Local'),
            ('foraneo', 'Foráneo')
        ],
        string='Tipo de ruta',
        required=True,
        default='local',
        tracking=True
    )

    active = fields.Boolean(
        string='Activa',
        default=True
    )

    descripcion = fields.Text(
        string='Descripción / Detalles de la Ruta'
    )

    # =========================
    # INFORMACIÓN DEL TRAYECTO
    # =========================

    origen = fields.Char(
        string='Origen',
        tracking=True
    )

    destino = fields.Char(
        string='Destino',
        tracking=True
    )

    distancia_km = fields.Float(
        string='Distancia (km)',
        tracking=True
    )

    tiempo_estimado = fields.Float(
        string='Tiempo Estimado (horas)',
        tracking=True,
        help="Tiempo estimado en horas"
    )

    # Coordenadas Origen
    origin_latitude = fields.Float(
        string='Latitud Origen',
        digits=(10, 6)
    )

    origin_longitude = fields.Float(
        string='Longitud Origen',
        digits=(10, 6)
    )

    # Coordenadas Destino
    destination_latitude = fields.Float(
        string='Latitud Destino',
        digits=(10, 6)
    )

    destination_longitude = fields.Float(
        string='Longitud Destino',
        digits=(10, 6)
    )

    # =========================
    # RELACIONES
    # =========================

    node_ids = fields.One2many(
        comodel_name='custodia.ruta.nodo',
        inverse_name='ruta_id',
        string='Nodos Intermedios'
    )

    # =========================
    # COSTOS
    # =========================

    tiene_peajes = fields.Boolean(
        string='Incluye Casetas/Peajes',
        default=False
    )

    costo_peaje_estimado = fields.Monetary(
        string='Costo Estimado Peajes',
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # =========================
    # MÉTODOS
    # =========================

    def get_route_coordinates(self):
        """
        Devuelve la ruta completa ordenada:
        Origen -> Nodos (sequence) -> Destino
        """
        self.ensure_one()
        points = []

        # Origen
        if self.origin_latitude and self.origin_longitude:
            points.append({
                'lat': self.origin_latitude,
                'lng': self.origin_longitude,
                'type': 'origin'
            })

        # Nodos ordenados por sequence
        for node in self.node_ids.sorted(key=lambda n: n.sequence):
            if node.latitude and node.longitude:
                points.append({
                    'lat': node.latitude,
                    'lng': node.longitude,
                    'type': 'node'
                })

        # Destino
        if self.destination_latitude and self.destination_longitude:
            points.append({
                'lat': self.destination_latitude,
                'lng': self.destination_longitude,
                'type': 'destination'
            })

        return points

class CustodiaRutaNodo(models.Model):
    _name = 'custodia.ruta.nodo'
    _description = 'Nodo Intermedio de Ruta'
    _order = 'sequence'

    ruta_id = fields.Many2one('custodia.ruta', string='Ruta', ondelete='cascade')
    sequence = fields.Integer(string='Orden', default=10)
    name = fields.Char(string='Referencia (Punto de parada)')
    latitude = fields.Float(string='Latitud', digits=(10, 6), required=True)
    longitude = fields.Float(string='Longitud', digits=(10, 6), required=True)

