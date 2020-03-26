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
    is_company_customer_job = fields.Boolean(string="¿Es empresa donde trabaja el cliente?")
	# Boolean if Company is familiy reference's job
    is_company_family_ref_job = fields.Boolean(string="¿Es empresa donde trabaja la referencia familiar?")
	# Boolean if Company is personal reference's job
    is_company_personal_ref_job = fields.Boolean(string="¿Es empresa donde trabaja la referencia personal?")
	# Boolean if Company is commercial reference's job
    is_company_commercial_ref_job = fields.Boolean(string="¿Es empresa donde trabaja la referencia comercial?")
	# Boolean if Company customer's hotel hoster
    is_hotel_customer_host = fields.Boolean(string="¿Es hotel donde se hospeda el cliente?")




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
