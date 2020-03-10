# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AGPL (v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AGPL (AGPL v3) for more details.
#
##############################################################################

from datetime import datetime, date, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning


class CarRentalContract(models.Model):
    _name = 'car.rental.contract'
    _description = 'Renta de Vehículos'
    _inherit = 'mail.thread'

    @api.onchange('rent_start_date', 'rent_end_date')
    def check_availability(self):
        self.vehicle_id = ''
        fleet_obj = self.env['fleet.vehicle'].search([])
        for i in fleet_obj:
            for each in i.rental_reserved_time:
                if each.date_from <= self.rent_start_date <= each.date_to:
                    i.write({'rental_check_availability': False})
                elif self.rent_start_date < each.date_from:
                    if each.date_from <= self.rent_end_date <= each.date_to:
                        i.write({'rental_check_availability': False})
                    elif self.rent_end_date > each.date_to:
                        i.write({'rental_check_availability': False})
                    else:
                        i.write({'rental_check_availability': True})
                else:
                    i.write({'rental_check_availability': True})

    image = fields.Binary(related='vehicle_id.image', string="Imagen del vehículo")
    reserved_fleet_id = fields.Many2one('rental.fleet.reserved', invisible=True, copy=False)
    image_medium = fields.Binary(related='vehicle_id.image_medium', string="Logo (mediano)")
    image_small = fields.Binary(related='vehicle_id.image_small', string="Logo (pequeño)")
    name = fields.Char(string="Nombre", default="Contrato Borrador", readonly=True, copy=False)
    customer_id = fields.Many2one('res.partner', required=True, string='Cliente', help="Cliente")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehículo", required=True, help="Vehículo",
                                 readonly=True,
                                 states={'draft': [('readonly', False)]}
                                 )
    car_brand = fields.Many2one('fleet.vehicle.model.brand', string="Marca", size=50,
                                related='vehicle_id.model_id.brand_id', store=True, readonly=True)
    car_color = fields.Char(string="Color", size=50, related='vehicle_id.color', store=True, copy=False,
                            default='#FFFFFF', readonly=True)
    cost = fields.Float(string="Costo de renta", help="Este campo determina el costo de la renta", required=True)
    rent_start_date = fields.Date(string="Fecha inicio renta", required=True, default=str(date.today()),
                                  help="Fecha inicio contrato", track_visibility='onchange')
    rent_end_date = fields.Date(string="Fecha fin renta", required=True, help="Fecha fin contrato",
                                track_visibility='onchange')
    state = fields.Selection([('draft', 'Borrador'), ('reserved', 'Reservado'), ('running', 'Ejecución'), ('cancel', 'Cancelado'),
                              ('checking', 'Verificando'), ('invoice', 'Factura'), ('done', 'Terminado')], string="Estado",
                             default="draft", copy=False, track_visibility='onchange')
    notes = fields.Text(string="Detalles y notas")
    cost_generated = fields.Float(string='Costo recurrente',
                                  help="Costo pagado periodicamente, dependiendo de la frecuencia elegida")
    cost_frequency = fields.Selection([('no', 'No'), ('daily', 'Diario'), ('weekly', 'Semanal'), ('monthly', 'Mensual'),
                                       ('yearly', 'Anual')], string="Frecuencia de costo recurrente",
                                      help='Frecuencia de costo recurrente', required=True)
    journal_type = fields.Many2one('account.journal', 'Diario',
                                   default=lambda self: self.env['account.journal'].search([('id', '=', 1)]))
    account_type = fields.Many2one('account.account', 'Cuenta',
                                   default=lambda self: self.env['account.account'].search([('id', '=', 17)]))
    recurring_line = fields.One2many('fleet.rental.line', 'rental_number', readonly=True, help="Facturas recurrentes",
                                     copy=False)
    first_payment = fields.Float(string='Primer pago',
                                 help="Transaction/Office/Contract charge amount, must paid by customer side other "
                                      "than recurrent payments",
                                 track_visibility='onchange',
                                 required=True)
    first_payment_inv = fields.Many2one('account.invoice', copy=False)
    first_invoice_created = fields.Boolean(string="First Invoice Created", invisible=True, copy=False)
    attachment_ids = fields.Many2many('ir.attachment', 'car_rent_checklist_ir_attachments_rel',
                                      'rental_id', 'attachment_id', string="Attachments",
                                      help="Images of the vehicle before contract/any attachments")
    checklist_line = fields.One2many('car.rental.checklist', 'checklist_number', string="Checklist",
                                     help="Facilities/Accessories, That should verify when closing the contract.",
                                     states={'invoice': [('readonly', True)],
                                             'done': [('readonly', True)],
                                             'cancel': [('readonly', True)]})
    total = fields.Float(string="Total (Accessories/Tools)", readonly=True, copy=False)
    tools_missing_cost = fields.Float(string="Missing Cost", readonly=True, copy=False,
                                      help='This is the total amount of missing tools/accessories')
    damage_cost = fields.Float(string="Damage Cost", copy=False)
    damage_cost_sub = fields.Float(string="Damage Cost", readonly=True, copy=False)
    total_cost = fields.Float(string="Total", readonly=True, copy=False)
    invoice_count = fields.Integer(compute='_invoice_count', string='# Invoice', copy=False)
    check_verify = fields.Boolean(compute='check_action_verify', copy=False)
    sales_person = fields.Many2one('res.users', string='Sales Person', default=lambda self: self.env.uid,
                                   track_visibility='always')

    @api.multi
    def action_run(self):
        self.state = 'running'

    @api.multi
    @api.depends('checklist_line.checklist_active')
    def check_action_verify(self):
        flag = 0
        for each in self:
            for i in each.checklist_line:
                if i.checklist_active:
                    continue
                else:
                    flag = 1
            if flag == 1:
                each.check_verify = False
            else:
                each.check_verify = True

    @api.constrains('rent_start_date', 'rent_end_date')
    def validate_dates(self):
        if self.rent_end_date < self.rent_start_date:
            raise Warning("Please select the valid end date.")

    @api.multi
    def set_to_done(self):
        invoice_ids = self.env['account.invoice'].search([('origin', '=', self.name)])
        f = 0
        for each in invoice_ids:
            if each.state != 'paid':
                f = 1
                break
        if f == 0:
            self.state = 'done'
        else:
            raise UserError("Some Invoices are pending")

    @api.multi
    def _invoice_count(self):
        invoice_ids = self.env['account.invoice'].search([('origin', '=', self.name)])
        self.invoice_count = len(invoice_ids)

    @api.constrains('state')
    def state_changer(self):
        if self.state == "running":
            state_id = self.env.ref('fleet_rental.vehicle_state_rent').id
            self.vehicle_id.write({'state_id': state_id})
        elif self.state == "cancel":
            state_id = self.env.ref('fleet_rental.vehicle_state_active').id
            self.vehicle_id.write({'state_id': state_id})
        elif self.state == "invoice":
            self.rent_end_date = fields.Date.today()
            state_id = self.env.ref('fleet_rental.vehicle_state_active').id
            self.vehicle_id.write({'state_id': state_id})

    @api.constrains('checklist_line', 'damage_cost')
    def total_updater(self):
        total = 0.0
        tools_missing_cost = 0.0
        for records in self.checklist_line:
            total += records.price
            if not records.checklist_active:
                tools_missing_cost += records.price
        self.total = total
        self.tools_missing_cost = tools_missing_cost
        self.damage_cost_sub = self.damage_cost
        self.total_cost = tools_missing_cost + self.damage_cost

    @api.multi
    def fleet_scheduler1(self, rent_date):
        inv_obj = self.env['account.invoice']
        inv_line_obj = self.env['account.invoice.line']
        recurring_obj = self.env['fleet.rental.line']
        #start_date = datetime.strptime(self.rent_start_date, '%Y-%m-%d').date()
        start_date = datetime.strptime(str(self.rent_start_date), '%Y-%m-%d').date()
        #end_date = datetime.strptime(self.rent_end_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(str(self.rent_end_date), '%Y-%m-%d').date()
        supplier = self.customer_id
        inv_data = {
            'name': supplier.name,
            'reference': supplier.name,
            'account_id': supplier.property_account_payable_id.id,
            'partner_id': supplier.id,
            'currency_id': self.account_type.company_id.currency_id.id,
            'journal_id': self.journal_type.id,
            'origin': self.name,
            'company_id': self.account_type.company_id.id,
            'date_due': self.rent_end_date,
        }
        inv_id = inv_obj.create(inv_data)
        product_id = self.env['product.product'].search([("name", "=", "Fleet Rental Service")])
        if product_id.property_account_income_id.id:
            income_account = product_id.property_account_income_id
        elif product_id.categ_id.property_account_income_categ_id.id:
            income_account = product_id.categ_id.property_account_income_categ_id
        else:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d).') % (product_id.name,
                                                                                     product_id.id))
        recurring_data = {
            'name': self.vehicle_id.name,
            'date_today': rent_date,
            'account_info': income_account.name,
            'rental_number': self.id,
            'recurring_amount': self.cost_generated,
            'invoice_number': inv_id.id,
            'invoice_ref': inv_id.id,
        }
        recurring_obj.create(recurring_data)
        inv_line_data = {
            'name': self.vehicle_id.name,
            'account_id': income_account.id,
            'price_unit': self.cost_generated,
            'quantity': 1,
            'product_id': product_id.id,
            'invoice_id': inv_id.id,
        }
        inv_line_obj.create(inv_line_data)
        mail_content = _(
            '<h3>Recordatorio de pago recurrente!</h3><br/>Hola %s, <br/> Este es un recordatorio para informarte que '
            'el pago recurrente para el '
            'contrato de renta ha sido cargado.'
            'Favor realizar el pago.'
            '<br/><br/>'
            'Por favor revisar los detalles abajo:<br/><br/>'
            '<table><tr><td>Referencia Contrato<td/><td> %s<td/><tr/>'
            '<tr/><tr><td>Valor <td/><td> %s<td/><tr/>'
            '<tr/><tr><td>Fecha de vencimiento <td/><td> %s<td/><tr/>'
            '<tr/><tr><td>Persona responsable <td/><td> %s, %s<td/><tr/><table/>') % \
                       (self.customer_id.name, self.name, inv_id.amount_total, inv_id.date_due,
                        inv_id.user_id.name,
                        inv_id.user_id.mobile)
        main_content = {
            'subject': "Recordatorio pago recurrente!",
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.customer_id.email,
        }
        self.env['mail.mail'].create(main_content).send()

    @api.model
    def fleet_scheduler(self):
        inv_obj = self.env['account.invoice']
        inv_line_obj = self.env['account.invoice.line']
        recurring_obj = self.env['fleet.rental.line']
        today = date.today()
        for records in self.search([]):
            start_date = datetime.strptime(records.rent_start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(records.rent_end_date, '%Y-%m-%d').date()
            if end_date >= date.today():
                temp = 0
                if records.cost_frequency == 'daily':
                    temp = 1
                elif records.cost_frequency == 'weekly':
                    week_days = (date.today() - start_date).days
                    if week_days % 7 == 0 and week_days != 0:
                        temp = 1
                elif records.cost_frequency == 'monthly':
                    if start_date.day == date.today().day and start_date != date.today():
                        temp = 1
                elif records.cost_frequency == 'yearly':
                    if start_date.day == date.today().day and start_date.month == date.today().month and \
                                    start_date != date.today():
                        temp = 1
                if temp == 1 and records.cost_frequency != "no" and records.state == "running":
                    supplier = records.customer_id
                    inv_data = {
                        'name': supplier.name,
                        'reference': supplier.name,
                        'account_id': supplier.property_account_payable_id.id,
                        'partner_id': supplier.id,
                        'currency_id': records.account_type.company_id.currency_id.id,
                        'journal_id': records.journal_type.id,
                        'origin': records.name,
                        'company_id': records.account_type.company_id.id,
                        'date_due': self.rent_end_date,
                    }
                    inv_id = inv_obj.create(inv_data)
                    product_id = self.env['product.product'].search([("name", "=", "Fleet Rental Service")])
                    if product_id.property_account_income_id.id:
                        income_account = product_id.property_account_income_id
                    elif product_id.categ_id.property_account_income_categ_id.id:
                        income_account = product_id.categ_id.property_account_income_categ_id
                    else:
                        raise UserError(
                            _('Por favor defina una cuenta de Ingresos para este producto: "%s" (id:%d).') % (product_id.name,
                                                                                                 product_id.id))
                    recurring_data = {
                        'name': records.vehicle_id.name,
                        'date_today': today,
                        'account_info': income_account.name,
                        'rental_number': records.id,
                        'recurring_amount': records.cost_generated,
                        'invoice_number': inv_id.id,
                        'invoice_ref': inv_id.id,
                    }
                    recurring_obj.create(recurring_data)
                    inv_line_data = {
                        'name': records.vehicle_id.name,
                        'account_id': income_account.id,
                        'price_unit': records.cost_generated,
                        'quantity': 1,
                        'product_id': product_id.id,
                        'invoice_id': inv_id.id,

                    }
                    inv_line_obj.create(inv_line_data)
                    mail_content = _(
                        '<h3>Recordatorio de pago recurrente!</h3><br/>Hola %s, <br/> Este es un recordatorio para informarte que  '
                        'el pago recurrente para el '
                        'contrato de renta ha sido cargado.'
                        'Favor realizar el pago.'
                        '<br/><br/>'
                        'Por favor revisar los detalles abajo:<br/><br/>'
                        '<table><tr><td>Referencia Contrato<td/><td> %s<td/><tr/>'
                        '<tr/><tr><td>Valor <td/><td> %s<td/><tr/>'
                        '<tr/><tr><td>Fecha vencimiento <td/><td> %s<td/><tr/>'
                        '<tr/><tr><td>Persona responsable <td/><td> %s, %s<td/><tr/><table/>') % \
                        (self.customer_id.name, self.name, inv_id.amount_total, inv_id.date_due,
                         inv_id.user_id.name,
                         inv_id.user_id.mobile)
                    main_content = {
                        'subject': "Recordatorio Pago Recurrente!",
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': self.customer_id.email,
                    }
                    self.env['mail.mail'].create(main_content).send()
            else:
                if self.state == 'running':
                    records.state = "checking"

    @api.multi
    def action_verify(self):
        self.state = "invoice"
        self.reserved_fleet_id.unlink()
        self.rent_end_date = fields.Date.today()
        # print(rent_end_date,'ooooooooooooiiiiiiiiiiiii')
        if self.total_cost != 0:
            inv_obj = self.env['account.invoice']
            inv_line_obj = self.env['account.invoice.line']
            supplier = self.customer_id
            inv_data = {
                'name': supplier.name,
                'reference': supplier.name,
                'account_id': supplier.property_account_payable_id.id,
                'partner_id': supplier.id,
                'currency_id': self.account_type.company_id.currency_id.id,
                'journal_id': self.journal_type.id,
                'origin': self.name,
                'company_id': self.account_type.company_id.id,
                'date_due': self.rent_end_date,
            }
            inv_id = inv_obj.create(inv_data)
            product_id = self.env['product.product'].search([("name", "=", "Fleet Rental Service")])
            if product_id.property_account_income_id.id:
                income_account = product_id.property_account_income_id
            elif product_id.categ_id.property_account_income_categ_id.id:
                income_account = product_id.categ_id.property_account_income_categ_id
            else:
                raise UserError(
                    _('Por favor defina una cuenta de Ingresos para este producto: "%s" (id:%d).') % (product_id.name,
                                                                                         product_id.id))
            inv_line_data = {
                'name': "Costos de daños o accesorios perdidos",
                'account_id': income_account.id,
                'price_unit': self.total_cost,
                'quantity': 1,
                'product_id': product_id.id,
                'invoice_id': inv_id.id,
            }
            inv_line_obj.create(inv_line_data)
            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object('account.action_invoice_tree1')
            list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
            form_view_id = imd.xmlid_to_res_id('account.invoice_form')
            result = {
                'name': action.name,
                'help': action.help,
                'type': 'ir.actions.act_window',
                'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                          [False, 'calendar'], [False, 'pivot']],
                'target': action.target,
                'context': action.context,
                'res_model': 'account.invoice',
            }
            if len(inv_id) > 1:
                result['domain'] = "[('id','in',%s)]" % inv_id.ids
            elif len(inv_id) == 1:
                result['views'] = [(form_view_id, 'form')]
                result['res_id'] = inv_id.ids[0]
            else:
                result = {'type': 'ir.actions.act_window_close'}
            return result

    @api.multi
    def action_confirm(self):
        check_availability = 0
        for each in self.vehicle_id.rental_reserved_time:
            if each.date_from <= self.rent_start_date <= each.date_to:
                check_availability = 1
            elif self.rent_start_date < each.date_from:
                if each.date_from <= self.rent_end_date <= each.date_to:
                    check_availability = 1
                elif self.rent_end_date > each.date_to:
                    check_availability = 1
                else:
                    check_availability = 0
            else:
                check_availability = 0
        if check_availability == 0:
            reserved_id = self.vehicle_id.rental_reserved_time.create({'customer_id': self.customer_id.id,
                                                                       'date_from': self.rent_start_date,
                                                                       'date_to': self.rent_end_date,
                                                                       'reserved_obj': self.vehicle_id.id
                                                                       })
            self.write({'reserved_fleet_id': reserved_id.id})
        else:
            raise Warning('Lo sentimos, este vehículo ya está reservado')
        self.state = "reserved"
        sequence_code = 'car.rental.sequence'
        order_date = self.create_date
        order_date = str(order_date)[0:10]
        self.name = self.env['ir.sequence'] \
            .with_context(ir_sequence_date=order_date).next_by_code(sequence_code)
        mail_content = _('<h3>Orden confirmada!</h3><br/>Hola %s, <br/> Ésta notificación es para informarte que tu contrato de renta '
                         'está comfirmado. <br/><br/>'
                         'Por favor lea los detalles abajo:<br/><br/>'
                         '<table><tr><td>Número Referencia<td/><td> %s<td/><tr/>'
                         '<tr><td>Desde <td/><td> %s hasta %s <td/><tr/><tr><td>Vehículo <td/><td> %s<td/><tr/>'
                         '<tr><td>Punto de contácto<td/><td> %s , %s<td/><tr/><table/>') % \
                         (self.customer_id.name, self.name, self.rent_start_date, self.rent_end_date,
                        self.vehicle_id.name, self.sales_person.name, self.sales_person.mobile)
        main_content = {
            'subject': _('Confirmed: %s - %s') %
                        (self.name, self.vehicle_id.name),
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.customer_id.email,
        }
        self.env['mail.mail'].create(main_content).send()

    @api.multi
    def action_cancel(self):
        self.state = "cancel"
        if self.reserved_fleet_id:
            self.reserved_fleet_id.unlink()

    @api.multi
    def force_checking(self):
        self.state = "checking"

    @api.multi
    def action_view_invoice(self):
        inv_obj = self.env['account.invoice'].search([('origin', '=', self.name)])
        inv_ids = []
        for each in inv_obj:
            inv_ids.append(each.id)
        view_id = self.env.ref('account.invoice_form').id
        if inv_ids:
            if len(inv_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.invoice',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    'res_id': inv_ids and inv_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', inv_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.invoice',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    'res_id': inv_ids
                }

            return value

    @api.multi
    def action_invoice_create(self):
        for each in self:
            rent_date = self.rent_start_date
            if each.cost_frequency != 'no' and rent_date < date.today():
                rental_days = (date.today() - rent_date).days
                if each.cost_frequency == 'weekly':
                    rental_days = int(rental_days / 7)
                if each.cost_frequency == 'monthly':
                    rental_days = int(rental_days / 30)
                for each1 in range(0, rental_days + 1):
                    #if rent_date > datetime.strptime(each.rent_end_date, "%Y-%m-%d").date():
                    if rent_date > datetime.strptime(str(each.rent_end_date), "%Y-%m-%d").date():
                        break
                    each.fleet_scheduler1(rent_date)
                    if each.cost_frequency == 'daily':
                        rent_date = rent_date + timedelta(days=1)
                    if each.cost_frequency == 'weekly':
                        rent_date = rent_date + timedelta(days=7)
                    if each.cost_frequency == 'monthly':
                        rent_date = rent_date + timedelta(days=30)

        if self.first_payment != 0:
            self.first_invoice_created = True
            inv_obj = self.env['account.invoice']
            inv_line_obj = self.env['account.invoice.line']
            supplier = self.customer_id
            inv_data = {
                'name': supplier.name,
                'reference': supplier.name,
                'account_id': supplier.property_account_payable_id.id,
                'partner_id': supplier.id,
                'currency_id': self.account_type.company_id.currency_id.id,
                'journal_id': self.journal_type.id,
                'origin': self.name,
                'company_id': self.account_type.company_id.id,
                'date_due': self.rent_end_date,
            }
            inv_id = inv_obj.create(inv_data)
            self.first_payment_inv = inv_id.id
            product_id = self.env['product.product'].search([("name", "=", "Fleet Rental Service")])
            if product_id.property_account_income_id.id:
                income_account = product_id.property_account_income_id.id
            elif product_id.categ_id.property_account_income_categ_id.id:
                income_account = product_id.categ_id.property_account_income_categ_id.id
            else:
                raise UserError(
                    _('Por favor defina una cuenta de Ingresos para este producto: "%s" (id:%d).') % (product_id.name,
                                                                                         product_id.id))
            inv_line_data = {
                'name': self.vehicle_id.name,
                'account_id': income_account,
                'price_unit': self.first_payment,
                'quantity': 1,
                'product_id': product_id.id,
                'invoice_id': inv_id.id,
            }
            inv_line_obj.create(inv_line_data)
            inv_id.action_invoice_open()
            mail_content = _(
                '<h3>Primer pago recibido!</h3><br/>Hi %s, <br/> Te informamos que tu primer pago '
                'ha sido recibido. <br/><br/>'
                'Por favor revise los detalles abajo:<br/><br/>'
                '<table><tr><td>Número de factura<td/><td> %s<td/><tr/>'
                '<tr><td>Date<td/><td> %s <td/><tr/><tr><td>Valor <td/><td> %s<td/><tr/><table/>') % \
                           (self.customer_id.name, inv_id.number, inv_id.date_invoice, inv_id.amount_total)
            main_content = {
                'subject': _('Pago recibido: %s') % inv_id.number,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': self.customer_id.email,
            }
            self.env['mail.mail'].create(main_content).send()
            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object('account.action_invoice_tree1')
            list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
            form_view_id = imd.xmlid_to_res_id('account.invoice_form')
            result = {
                'name': action.name,
                'help': action.help,
                'type': 'ir.actions.act_window',
                'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                          [False, 'calendar'], [False, 'pivot']],
                'target': action.target,
                'context': action.context,
                'res_model': 'account.invoice',
            }
            if len(inv_id) > 1:
                result['domain'] = "[('id','in',%s)]" % inv_id.ids
            elif len(inv_id) == 1:
                result['views'] = [(form_view_id, 'form')]
                result['res_id'] = inv_id.ids[0]
            else:
                result = {'type': 'ir.actions.act_window_close'}
            return result
        else:
            raise Warning("Please enter advance amount to make first payment")


class FleetRentalLine(models.Model):
    _name = 'fleet.rental.line'

    name = fields.Char('Description')
    date_today = fields.Date('Date')
    account_info = fields.Char('Account')
    recurring_amount = fields.Float('Amount')
    rental_number = fields.Many2one('car.rental.contract', string='Número de renta')
    payment_info = fields.Char(compute='paid_info', string='Estado de pago', default='draft')
    invoice_number = fields.Integer(string='Invoice ID')
    invoice_ref = fields.Many2one('account.invoice', string='Factura de referencia')
    date_due = fields.Date(string='Fecha de vencimiento', related='invoice_ref.date_due')

    @api.multi
    def paid_info(self):
        for each in self:
            if self.env['account.invoice'].browse(each.invoice_number):
                each.payment_info = self.env['account.invoice'].browse(each.invoice_number).state
            else:
                each.payment_info = 'Registro borrado'


class CarRentalChecklist(models.Model):
    _name = 'car.rental.checklist'

    name = fields.Many2one('car.tools', string="Nombre")
    checklist_active = fields.Boolean(string="Disponible", default=True)
    checklist_number = fields.Many2one('car.rental.contract', string="Número de lista de chequeo")
    price = fields.Float(string="Precio")

    @api.onchange('name')
    def onchange_name(self):
        self.price = self.name.price


class CarTools(models.Model):
    _name = 'car.tools'

    name = fields.Char(string="Nombre")
    price = fields.Float(string="Precio")
