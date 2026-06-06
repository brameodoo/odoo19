# -*- coding: utf-8 -*-
import base64
import json
import logging
import requests
import io
from PIL import Image
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class SgsFiscalReceipt(models.Model):
    _name = 'sgs.fiscal.receipt'
    _description = 'Comprobante fiscal SGS'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char('Referencia', compute='_compute_name', store=True)
    custodian_id = fields.Many2one('sgs.custodian', string='Custodio', required=True, ondelete='cascade', tracking=True)
    company_id = fields.Many2one(related='custodian_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='custodian_id.currency_id', readonly=True)
    date = fields.Date('Fecha factura', required=True, default=fields.Date.context_today)
    amount = fields.Monetary('Monto', currency_field='currency_id', required=True, tracking=True)
    description = fields.Char('Concepto / descripción', required=True)
    provider = fields.Char('Proveedor / razón social')
    provider_vat = fields.Char('RFC proveedor')
    image = fields.Binary('Foto factura')
    image_filename = fields.Char('Archivo')

    ocr_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('success', 'Exitoso'),
        ('failed', 'Fallido')
    ], string='Estado OCR', default='pending', tracking=True)
    ocr_raw_data = fields.Text('Datos crudos OCR')
    ocr_error_message = fields.Text('Error OCR')
    is_fiscal = fields.Boolean('Es comprobante fiscal', default=False)
    rfc_emitter = fields.Char('RFC Emisor (OCR)')
    emitter_name = fields.Char('Nombre Emisor (OCR)')
    ocr_date = fields.Date('Fecha (OCR)')
    ocr_amount = fields.Monetary('Monto (OCR)', currency_field='currency_id')

    @api.depends('custodian_id', 'date', 'description')
    def _compute_name(self):
        for rec in self:
            rec.name = '%s · %s · %s' % (rec.custodian_id.name or 'Custodio', rec.date or '', rec.description or 'Factura')

    @api.constrains('amount', 'ocr_status')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0 and rec.ocr_status == 'success':
                raise ValidationError(_('El monto del comprobante fiscal debe ser mayor a cero.'))

    def action_process_ocr(self):
        for rec in self:
            if not rec.image: continue
            rec.write({'ocr_status': 'processing', 'ocr_error_message': False})
            rec._process_ocr_with_openai()

    def _process_ocr_with_openai(self):
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('sgs.openai_api_key')
        if not api_key:
            self.write({
                'ocr_status': 'failed',
                'ocr_error_message': 'No se ha configurado la API Key de OpenAI en los parámetros del sistema (sgs.openai_api_key).'
            })
            return
        # Lógica simulada de OCR por API de Visión Artificial (OpenAI / Gemini)
        # En producción envía el archivo b64 y recupera el JSON con el RFC, fecha, emisor y monto.
        self.write({
            'ocr_status': 'success',
            'is_fiscal': True,
            'rfc_emitter': 'XAXX010101000',
            'emitter_name': 'Casetas y Gasolineras del Norte S.A.',
            'ocr_date': self.date,
            'ocr_amount': self.amount,
        })
