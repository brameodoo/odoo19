# -*- coding: utf-8 -*-
import base64
import io
import openpyxl
from datetime import datetime, time
from odoo import models, fields, _
from odoo.exceptions import UserError

class AuditExcelImportWizard(models.TransientModel):
    _name = 'audit.excel.import.wizard'
    _description = 'Asistente de Ingesta Masiva de Auditorías Excel'

    excel_file = fields.Binary(string='Archivo Excel (F-CAL-15_R01)', required=True)
    filename = fields.Char(string='Nombre del Archivo')

    def action_import_excel(self):
        self.ensure_one()
        if not self.excel_file:
            raise UserError(_("Cargue un archivo .xlsx válido."))

        file_data = base64.b64decode(self.excel_file)
        wb = openpyxl.load_workbook(io.BytesIO(file_data), data_only=True)
        sheet = wb.active

        # 1. Extracción de Metadatos del Encabezado
        auditor_str = sheet.cell(7, 3).value or ''
        process_str = sheet.cell(8, 3).value or ''
        procedure_str = sheet.cell(9, 3).value or ''
        audited_str = sheet.cell(10, 3).value or ''
        job_str = sheet.cell(11, 3).value or ''
        
        date_val = sheet.cell(8, 6).value
        time_val = sheet.cell(9, 6).value
        cdo_raw = sheet.cell(10, 6).value or 'CDO Desconocido'
        department_str = sheet.cell(11, 6).value or ''

        # Resolución / Creación Automática de CDO
        cdo = self.env['audit.cdo'].search([('code', '=', str(cdo_raw).strip())], limit=1)
        if not cdo:
            cdo = self.env['audit.cdo'].create({
                'code': str(cdo_raw).strip(),
                'name': str(cdo_raw).strip(),
            })

        # Auditor líder (fallback al usuario activo)
        auditor_user = self.env['res.users'].search([('name', 'ilike', auditor_str)], limit=1) or self.env.user

        audit_date = fields.Date.context_today(self)
        if isinstance(date_val, datetime):
            audit_date = date_val.date()

        audit_vals = {
            'cdo_id': cdo.id,
            'process_name': process_str,
            'procedure_name': procedure_str,
            'auditor_id': auditor_user.id,
            'audited_job_title': job_str,
            'date': audit_date,
            'time': str(time_val) if time_val else '',
            'state': 'in_progress',
        }
        audit = self.env['iso.audit'].create(audit_vals)

        # 2. Lectura e Inserción de Reactivos
        checklist_lines = []
        current_criteria = 'organizational'

        result_mapping = {
            'cumple': 'compliant',
            'no cumple': 'non_compliant',
            'no aplica': 'not_applicable'
        }

        for r in range(14, sheet.max_row + 1):
            cell_a = sheet.cell(r, 1).value
            if cell_a and 'criterios operativos' in str(cell_a).lower():
                current_criteria = 'operational'
                continue

            # Si la columna A contiene el ID numérico
            if isinstance(cell_a, int) or (cell_a and str(cell_a).strip().isdigit()):
                item_no = int(cell_a)
                iso_clause = sheet.cell(r, 2).value or ''
                question = sheet.cell(r, 4).value or ''
                context = sheet.cell(r, 7).value or ''
                expected_ev = sheet.cell(r, 9).value or ''
                raw_res = str(sheet.cell(r, 12).value or '').strip().lower()
                obj_ev = sheet.cell(r, 13).value or ''
                breached = sheet.cell(r, 14).value or ''
                risk = sheet.cell(r, 15).value or ''
                comments = sheet.cell(r, 16).value or ''

                norm_result = result_mapping.get(raw_res, 'not_scored')

                checklist_lines.append((0, 0, {
                    'item_number': item_no,
                    'criteria_type': current_criteria,
                    'iso_clause': iso_clause,
                    'question': question,
                    'context': context,
                    'expected_evidence': expected_ev,
                    'result': norm_result,
                    'objective_evidence': obj_ev,
                    'breached_requirement': breached,
                    'risk_impact': risk,
                    'comments': comments,
                }))

        if checklist_lines:
            audit.write({'line_ids': checklist_lines})

        # 3. Disparo Automático de NCRs para desviaciones encontradas
        for line in audit.line_ids.filtered(lambda l: l.result == 'non_compliant'):
            line.action_create_ncr()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Auditoría Importada'),
            'res_model': 'iso.audit',
            'res_id': audit.id,
            'view_mode': 'form',
            'target': 'current',
        }
