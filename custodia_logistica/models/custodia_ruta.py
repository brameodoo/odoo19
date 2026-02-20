# -*- coding: utf-8 -*-
from odoo import models, fields

class CustodiaRuta(models.Model):
    _name = 'custodia.ruta'
    _description = 'Ruta de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre de la Ruta', required=True, tracking=True, help="Ejemplo: CDMX - Nuevo Laredo")
    origen = fields.Char(string='Origen', required=True, tracking=True)
    destino = fields.Char(string='Destino', required=True, tracking=True)
    distancia_km = fields.Float(string='Distancia (km)', help="Distancia estimada de la ruta.", tracking=True)
    tiempo_estimado = fields.Float(string='Tiempo Estimado (Hrs)', help="Tiempo estimado de recorrido.")
    # Clasificación para validación de tiempos
    tipo = fields.Selection([('local','Local'), ('foraneo','Foráneo')], string='Tipo de ruta', required=True, default='local')

    tiene_peajes = fields.Boolean(string='Incluye Casetas/Peajes', default=False)
    costo_peaje_estimado = fields.Monetary(string='Costo Estimado Peajes', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id.id)

    active = fields.Boolean(string='Activa', default=True)
    descripcion = fields.Text(string='Descripción / Detalles de la Ruta')
