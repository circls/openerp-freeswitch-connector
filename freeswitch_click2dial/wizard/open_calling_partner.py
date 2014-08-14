# -*- encoding: utf-8 -*-
##############################################################################
#
#    FreeSWITCH Click2dial module for OpenERP
#    Copyright (C) 2010-2013 Alexis de Lattre <alexis@via.ecp.fr>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp.osv import orm, fields
from openerp.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class wizard_open_calling_partner(orm.TransientModel):
    _name = "wizard.open.calling.partner"
    _description = "Open calling partner"

    _columns = {
        # I can't set any field to readonly, because otherwize it would call
        # default_get (and thus connect to FreeSWITCH) a second time when the user
        # clicks on one of the buttons
        'calling_number': fields.char('Calling number', size=30, help="Phone number of calling party that has been obtained from FreeSWITCH."),
        'partner_id': fields.many2one('res.partner', 'Partner name', help="Partner related to the calling number."),
        'parent_partner_id': fields.many2one('res.partner', 'Parent partner', help="Parent Partner related to the calling number."),
        'to_update_partner_id': fields.many2one('res.partner', 'Partner to update', help="Partner on which the phone or mobile number will be written"),
        'current_phone': fields.related('to_update_partner_id', 'phone', type='char', relation='res.partner', string='Current phone'),
        'current_mobile': fields.related('to_update_partner_id', 'mobile', type='char', relation='res.partner', string='Current mobile'),
            }


    def default_get(self, cr, uid, fields, context=None):
        '''Thanks to the default_get method, we are able to query FreeSWITCH and
        get the corresponding partner when we launch the wizard'''
        res = {}
        if context is None:
            context = {}
        if 'incall_number_popup' in context:
            # That's when we come from incall_notify_by_user_ids()
            # of the module freeswitch_popup()
            res['partner_id'] = False
            res['parent_partner_id'] = False
            res['to_update_partner_id'] = False
            res['calling_number'] = context.get('incall_number_popup')
        else:
            calling_number = self.pool['freeswitch.server']._get_calling_number(
                cr, uid, context=context)
            #To test the code without FreeSWITCH server
            #calling_number = "0141981246"
            if calling_number:
                res['calling_number'] = calling_number
                record = self.pool['phone.common'].get_record_from_phone_number(
                    cr, uid, calling_number, context=context)
                if record and record[0] == 'res.partner':
                    res['partner_id'] = record[1]
                    partner = self.pool['res.partner'].browse(
                        cr, uid, record[1], context=context)
                    res['parent_partner_id'] = \
                        partner.parent_id and partner.parent_id.id or False
                else:
                    res['partner_id'] = False
                    res['parent_partner_id'] = False
                res['to_update_partner_id'] = False
            else:
                _logger.debug("Could not get the calling number from FreeSWITCH.")
                raise orm.except_orm(
                    _('Error :'),
                    _("Could not get the calling number from FreeSWITCH. Is your phone ringing or are you currently on the phone ? If yes, check your setup and look at the OpenERP debug logs."))

        return res


    def open_filtered_object(
            self, cr, uid, ids, oerp_object, try_parent=True, context=None):
        '''Returns the action that opens the list view of the 'oerp_object'
        given as argument filtered on the partner'''
        # This module only depends on "base"
        # and I don't want to add a dependancy on "sale" or "account"
        # So I just check here that the model exists, to avoid a crash
        if not self.pool['ir.model'].search(cr, uid, [('model', '=', oerp_object._name)], context=context):
            raise orm.except_orm(_('Error :'), _("The object '%s' is not found in your OpenERP database, probably because the related module is not installed." % oerp_object._description))

        partner = self.read(cr, uid, ids[0], ['partner_id', 'parent_partner_id'], context=context)
        if try_parent:
            partner_id_to_filter = (
                partner['parent_partner_id']
                and partner['parent_partner_id'][0]
                or (partner['partner_id'] and partner['partner_id'][0] or False))
        else:
            partner_id_to_filter = partner['partner_id'] and partner['partner_id'][0] or False
        if partner_id_to_filter:
            action = {
                'name': oerp_object._description,
                'view_mode': 'tree,form,kanban',
                'res_model': oerp_object._name,
                'type': 'ir.actions.act_window',
                'nodestroy': False, # close the pop-up wizard after action
                'target': 'current',
                'context': {'search_default_partner_id': partner_id_to_filter},
                }
            return action
        else:
            return False


    def open_sale_orders(self, cr, uid, ids, context=None):
        '''Function called by the related button of the wizard'''
        return self.open_filtered_object(cr, uid, ids, self.pool.get('sale.order'), context=context)


    def open_invoices(self, cr, uid, ids, context=None):
        '''Function called by the related button of the wizard'''
        return self.open_filtered_object(cr, uid, ids, self.pool.get('account.invoice'), context=context)


    def simple_open(self, cr, uid, ids, field='partner_id', context=None):
        record_to_open = self.read(cr, uid, ids[0], [field], context=context)[field]
        if record_to_open:
            return {
                'name': self.pool['res.partner']._description,
                'view_mode': 'form,tree,kanban',
                'res_model': 'res.partner',
                'type': 'ir.actions.act_window',
                'nodestroy': False, # close the pop-up wizard after action
                'target': 'current',
                'res_id': record_to_open[0],
                }
        else:
            return False


    def open_partner(self, cr, uid, ids, context=None):
        '''Function called by the related button of the wizard'''
        return self.simple_open(cr, uid, ids, field='partner_id', context=context)


    # TODO
    def open_parent_partner(self, cr, uid, ids, context=None):
        '''Function called by the related button of the wizard'''
        return self.simple_open(cr, uid, ids, field='parent_partner_id', context=context)


    def create_partner(self, cr, uid, ids, phone_type='phone', context=None):
        '''Function called by the related button of the wizard'''
        calling_number = self.read(cr, uid, ids[0], ['calling_number'], context=context)['calling_number']
        fs_server = self.pool['freeswitch.server']._get_freeswitch_server_from_user(cr, uid, context=context)
        # Convert the number to the international format
        number_to_write = self.pool['freeswitch.server']._convert_number_to_international_format(cr, uid, calling_number, fs_server, context=context)

        context['default_' + phone_type] = number_to_write

        action = {
            'name': 'Create new partner',
            'view_mode': 'form,tree,kanban',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'nodestroy': False,
            'target': 'current',
            'context': context,
        }
        return action


    def create_partner_phone(self, cr, uid, ids, context=None):
        return self.create_partner(cr, uid, ids, phone_type='phone', context=context)


    def create_partner_mobile(self, cr, uid, ids, context=None):
        return self.create_partner(cr, uid, ids, phone_type='mobile', context=context)


    def update_partner(self, cr, uid, ids, phone_type='mobile', context=None):
        cur_wizard = self.browse(cr, uid, ids[0], context=context)
        if not cur_wizard.to_update_partner_id:
            raise orm.except_orm(_('Error :'), _("Select the partner to update."))
        fs_server = self.pool['freeswitch.server']._get_freeswitch_server_from_user(cr, uid, context=context)
        number_to_write = self.pool['freeswitch.server']._convert_number_to_international_format(cr, uid, cur_wizard.calling_number, fs_server, context=context)
        self.pool['res.partner'].write(cr, uid, cur_wizard.to_update_partner_id.id, {phone_type: number_to_write}, context=context)
        action = {
            'name': 'Partner: ' + cur_wizard.to_update_partner_id.name,
            'view_mode': 'form,tree,kanban',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'nodestroy': False,
            'target': 'current',
            'res_id': cur_wizard.to_update_partner_id.id
            }
        return action


    def update_partner_phone(self, cr, uid, ids, context=None):
        return self.update_partner(cr, uid, ids, phone_type='phone', context=context)


    def update_partner_mobile(self, cr, uid, ids, context=None):
        return self.update_partner(cr, uid, ids, phone_type='mobile', context=context)


    def onchange_to_update_partner(self, cr, uid, ids, to_update_partner_id, context=None):
        res = {}
        res['value'] = {}
        if to_update_partner_id:
            to_update_partner = self.pool['res.partner'].browse(cr, uid, to_update_partner_id, context=context)
            res['value'].update({'current_phone': to_update_partner.phone,
                'current_mobile': to_update_partner.mobile})
        else:
            res['value'].update({'current_phone': False, 'current_mobile': False})
        return res

