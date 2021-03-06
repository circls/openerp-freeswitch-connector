# -*- encoding: utf-8 -*-
##############################################################################
#
#    HR Recruitment phone module for Odoo/OpenERP
#    Copyright (c) 2012-2014 Akretion (http://www.akretion.com)
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm


class hr_applicant(orm.Model):
    _name = 'hr.applicant'
    _inherit = ['hr.applicant', 'phone.common']

    def create(self, cr, uid, vals, context=None):
        vals_reformated = self._generic_reformat_phonenumbers(
            cr, uid, vals, context=context)
        return super(hr_applicant, self).create(
            cr, uid, vals_reformated, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        vals_reformated = self._generic_reformat_phonenumbers(
            cr, uid, vals, context=context)
        return super(hr_applicant, self).write(
            cr, uid, ids, vals_reformated, context=context)

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if context.get('callerid'):
            res = []
            if isinstance(ids, (int, long)):
                ids = [ids]
            for applicant in self.browse(cr, uid, ids, context=context):
                name = applicant.partner_name
                res.append((applicant.id, name))
            return res
        else:
            return super(hr_applicant, self).name_get(
                cr, uid, ids, context=context)

    def case_close_with_emp(self, cr, uid, ids, context=None):
        """ We need to erase applicant record phone numbers
            to avoid problems with callerid lookup.
        """
        if context is None:
            context = {}

        res = super(hr_applicant, self).case_close_with_emp(
            cr, uid, ids, context=context)
        for applicant in self.browse(cr, uid, ids, context=context):
#            phone = self.read(cr, uid, ids, ['partner_phone'])[0]["partner_phone"]
#            mobile = self.read(cr, uid, ids, ['partner_mobile'])[0]["partner_mobile"]
            self.write(cr, uid, [applicant.id], {'partner_phone': ""}, context=context)
            self.write(cr, uid, [applicant.id], {'partner_mobile': ""}, context=context)
        return res

class phone_common(orm.AbstractModel):
    _inherit = 'phone.common'

    def _get_phone_fields(self, cr, uid, context=None):
        res = super(phone_common, self)._get_phone_fields(
            cr, uid, context=context)
        res['hr.applicant'] = {
            'phonefields': ['partner_phone', 'partner_mobile'],
            'get_name_sequence': 50,
            }
        return res
