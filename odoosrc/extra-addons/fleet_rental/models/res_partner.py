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

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _name = 'res.partner'
    _description = "Partner Rent a Car"

	# Boolean if Company is customer's job
    x_is_company_customer_job = fields.Boolean(string="¿Es empresa donde trabaja el cliente?")

	# Boolean if Company is familiy reference's job
    x_is_company_family_ref_job = fields.Boolean(string="¿Es empresa donde trabaja la referencia familiar?")

	# Boolean if Company is personal reference's job
    x_is_company_personal_ref_job = fields.Boolean(string="¿Es empresa donde trabaja la referencia personal?")

	# Boolean if Company is commercial reference's job
    x_is_company_commercial_ref_job = fields.Boolean(string="¿Es empresa donde trabaja la referencia comercial?")

	# Boolean if Company customer's hotel hoster
    x_is_hotel_customer_host = fields.Boolean(string="¿Es hotel donde se hospeda el cliente?")

    # City origin of ID document
    x_city_id_document = fields.Char('Ciudad Expedición Documento')

    # Driver License Number
    x_driver_license_number = fields.Char("Número de Licencia")

    # Driver license generate's day
    x_license_generates_day = fields.Date("Fecha Expedición Licencia")


	# Company customer's job
    x_company_customer_job = fields.Many2one('res.partner',string='Empresa donde Trabaja',  domain=[('is_company', '=', True)])

    # Familiy reference's
    x_person_family_ref = fields.Many2one('res.partner',
        string='Persona Referencia Familiar',
        domain=[('is_company', '=', False)])
	
    # Familiy reference's job
    x_company_family_ref_job = fields.Many2one('res.partner',
        string='Empresa donde Trabaja la referencia Familiar',
        domain=[('is_company', '=', True)])


    # Personal reference's
    x_person_personal_ref = fields.Many2one('res.partner',
        string='Persona Referencia Personal',
        domain=[('is_company', '=', False)])
	
    # Familiy reference's job
    x_company_personal_ref_job = fields.Many2one('res.partner',
        string='Empresa donde Trabaja la Referencia Personal',
        domain=[('is_company', '=', True)])


    # Commercial reference's
    x_person_commercial_ref = fields.Many2one('res.partner',
        string='Persona Referencia Comercial',
        domain=[('is_company', '=', False)])
	
    # Commercial reference's job
    x_company_commercial_ref_job = fields.Many2one('res.partner',
        string='Empresa donde Trabaja la Referencia Comercial',
        domain=[('is_company', '=', True)])


    # Customer's hotel hoster
    x_company_hotel_customer_host = fields.Many2one('res.partner',
        string='Hotel donde se Hospeda',
        domain=['|',('is_company', '=', True),('x_is_hotel_customer_host', '=', True)])

    # room
    x_hotel_room = fields.Char("Habitación")

    # Check in day
    x_checkin_day = fields.Date("Fecha de Hospedaje")



class EmployeeFleet(models.Model):
    _inherit = 'fleet.vehicle'

    rental_check_availability = fields.Boolean(default=True, copy=False)
    color = fields.Char(string='Color', default='#FFFFFF')
    rental_reserved_time = fields.One2many('rental.fleet.reserved', 'reserved_obj', String='Reserved Time', readonly=1,
                                           ondelete='cascade')
    fuel_type = fields.Selection([('gasoline', 'Gasoline'),
                                  ('diesel', 'Diesel'),
                                  ('electric', 'Electric'),
                                  ('hybrid', 'Hybrid'),
                                  ('petrol', 'Petrol')],
                                 'Fuel Type', help='Fuel Used by the vehicle')

    _sql_constraints = [('vin_sn_unique', 'unique (vin_sn)', "Chassis Number already exists !"),
                        ('license_plate_unique', 'unique (license_plate)', "License plate already exists !")]
