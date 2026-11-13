# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api


class AuditDashboard(models.AbstractModel):
    _name = 'audit.dashboard'
    _description = 'Datos del Tablero Ejecutivo ISO & CDO'

    @api.model
    def get_dashboard_data(self, period='6m'):
        today = fields.Date.context_today(self)
        domain_date = []
        if period == '1m':
            domain_date = [('create_date', '>=', today - timedelta(days=30))]
        elif period == '3m':
            domain_date = [('create_date', '>=', today - timedelta(days=90))]
        elif period == '6m':
            domain_date = [('create_date', '>=', today - timedelta(days=180))]
        elif period == '12m':
            domain_date = [('create_date', '>=', today - timedelta(days=365))]

        NCR = self.env['quality.ncr']
        CAPA = self.env['quality.capa']
        Audit = self.env['iso.audit']
        CDO = self.env['audit.cdo']

        # 1. Tarjetas KPI
        open_ncrs = NCR.search_count([('state', '!=', 'closed')] + domain_date)
        critical_ncrs = NCR.search_count([('state', '!=', 'closed'), ('severity', '=', 'critical')] + domain_date)
        total_ncrs_period = NCR.search_count(domain_date)
        closed_ncrs_period = NCR.search_count([('state', '=', 'closed')] + domain_date)
        ncr_closure_rate = round((closed_ncrs_period / total_ncrs_period * 100), 1) if total_ncrs_period else 0.0

        overdue_capas = CAPA.search_count([
            ('state', '=', 'pending_verification'),
            ('effectiveness_due_date', '<', today)
        ])

        audits_in_progress = Audit.search_count([('state', '=', 'in_progress')])
        all_audits = Audit.search([('state', '!=', 'cancel')] + domain_date)
        avg_compliance = round(
            (sum(all_audits.mapped('global_compliance_rate')) / len(all_audits) * 100), 1
        ) if all_audits else 0.0

        # 2. Barra de Estatus por CDO (Cobertura Territorial)
        cdos = CDO.search([])
        cdo_green = cdo_yellow = cdo_red = 0
        for cdo in cdos:
            audits_cdo = cdo.audit_ids.filtered(lambda a: a.state != 'cancel')
            if not audits_cdo:
                cdo_red += 1
                continue
            avg_cdo = sum(audits_cdo.mapped('global_compliance_rate')) / len(audits_cdo)
            if avg_cdo >= 0.80:
                cdo_green += 1
            elif avg_cdo >= 0.60:
                cdo_yellow += 1
            else:
                cdo_red += 1

        total_cdos = len(cdos) or 1
        cdo_readiness_pct = round((cdo_green / total_cdos) * 100)

        # 3. Gráfica de Dona: NCRs Abiertas por Severidad
        open_ncr_recs = NCR.search([('state', '!=', 'closed')] + domain_date)
        severity_counts = {
            'minor': len(open_ncr_recs.filtered(lambda n: n.severity == 'minor')),
            'major': len(open_ncr_recs.filtered(lambda n: n.severity == 'major')),
            'critical': len(open_ncr_recs.filtered(lambda n: n.severity == 'critical')),
        }

        # 4. Gráfica de Tendencia: NCRs por Mes
        ncr_recs = NCR.search(domain_date, order='create_date asc')
        trend_map = {}
        for n in ncr_recs:
            month_key = n.create_date.strftime('%Y-%m')
            trend_map[month_key] = trend_map.get(month_key, 0) + 1

        # 5. Tabla de No Conformidades Recientes
        recent_ncrs = []
        for n in NCR.search([], order='id desc', limit=6):
            recent_ncrs.append({
                'id': n.id,
                'name': n.name,
                'cdo': n.cdo_id.name,
                'description': (n.description or '')[:95] + ('...' if len(n.description or '') > 95 else ''),
                'severity': n.severity,
                'state': dict(n._fields['state'].selection).get(n.state),
                'date': n.create_date.strftime('%Y-%m-%d'),
            })

        return {
            'kpis': {
                'open_ncrs': open_ncrs,
                'critical_ncrs': critical_ncrs,
                'overdue_capas': overdue_capas,
                'audits_in_progress': audits_in_progress,
                'ncr_closure_rate': ncr_closure_rate,
                'avg_compliance': avg_compliance,
            },
            'cdo_bar': {
                'total': len(cdos),
                'green': cdo_green,
                'yellow': cdo_yellow,
                'red': cdo_red,
                'green_pct': round((cdo_green / total_cdos) * 100, 1),
                'yellow_pct': round((cdo_yellow / total_cdos) * 100, 1),
                'red_pct': round((cdo_red / total_cdos) * 100, 1),
                'readiness_pct': cdo_readiness_pct,
            },
            'severity': severity_counts,
            'trend': {
                'labels': list(trend_map.keys()),
                'values': list(trend_map.values()),
            },
            'recent_ncrs': recent_ncrs,
        }
