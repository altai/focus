import itertools
import netaddr
import uuid

import flask
from flask import blueprints
from flaskext import principal

from C4GD_web.models import orm
from C4GD_web.views import pagination
from C4GD_web.views import forms


bp = blueprints.Blueprint('networks', __name__, url_prefix='/global/networks/')


@bp.before_request
def authorize():
    principal.Permission(('role', 'admin')).test()


HEADERS = [x.strip() for x in 'created_at          | updated_at          | deleted_at | deleted | id | injected | cidr          | netmask       | bridge | gateway    | broadcast    | dns1 | vlan | vpn_public_address | vpn_public_port | vpn_private_address | dhcp_start | project_id | host | cidr_v6 | gateway_v6 | label   | netmask_v6 | bridge_interface | multi_host | dns2 | uuid                                 | priority | rxtx_base '.split('|')]

@bp.route('')
def index():
    store = orm.get_store('NOVA_RO')
    total_count = store.execute('SELECT count(*) FROM networks').get_one()[0]
    p = pagination.Pagination(total_count)
    data = store.execute(
        'SELECT * FROM networks ORDER BY label  LIMIT ?, ? ',
        p.limit_offset()).get_all()
    data = map(lambda row: dict(zip(HEADERS, row)), data) 
    return {
        'objects': data,
        'pagination': p,
        'delete_form': forms.DeleteForm()}


@bp.route('<object_id>/')
def show(object_id):
    store = orm.get_store('NOVA_RO')
    row = store.execute(
        'SELECT * FROM networks WHERE id = ? LIMIT 1', (object_id,)).get_one()
    obj = dict(zip(HEADERS, row))
    headers = dict([(x, x.replace('_', ' ').capitalize()) for x in HEADERS])
    fixed_ips = store.execute(
        'SELECT address, reserved FROM fixed_ips WHERE network_id = ?',
        (obj['id'], )).get_all()
    return {'object': obj, 'headers': headers, 'fixed_ips': fixed_ips}


@bp.route('new/', methods=['GET', 'POST'])
def new():
    """Create network.

    Insert record in db for network and create records for fixed IPs based on
    network CIDR.
    """
    form = forms.CreateNetwork()
    if form.validate_on_submit():
        # creating fixed IPs as nova/network/manager.py:_create_fixed_ips() does
        try:
            project_net = netaddr.IPNetwork(form.cidr.data)
        except netaddr.core.AddrFormatError:
            flask.flash(
                'Unable to build IP list for CIDR %s' % form.cidr.data, 'error')
        else:
            store = orm.get_store('NOVA_RW')
            store.execute(
                'INSERT INTO networks (label, cidr, netmask, bridge, gateway, '
                'broadcast, vlan, vpn_public_address, vpn_public_port, '
                'vpn_private_address, dhcp_start, host, bridge_interface, '
                'rxtx_base, multi_host, uuid, created_at, deleted, injected) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, '
                '?, now(), 0, 0)',
                (form.label.data, form.cidr.data, form.netmask.data, 
                 form.bridge.data, form.gateway.data, form.broadcast.data, 
                 form.vlan.data, form.vpn_public_address.data, 
                 form.vpn_public_port.data, form.vpn_private_address.data, 
                 form.dhcp_start.data, form.host.data, form.bridge_interface.data, 
                 str(uuid.uuid4())))
            store.commit()
            network_id = store.execute('SELECT last_insert_id()').get_one()[0]
            num_ips = len(project_net)
            bottom_reserved = 2 # network, gateway
            top_reserved = 1 # broadcast
            ips = []
            for index in range(num_ips):
                address = str(project_net[index])
                if index < bottom_reserved or num_ips - index <= top_reserved:
                    reserved = True
                else:
                    reserved = False

                ips.append({'network_id': network_id,
                            'address': address,
                            'reserved': reserved})
            values = itertools.chain(*[(
                        x['address'], 
                        x['network_id'], 
                        x['reserved']) for x in ips])
            sql_tmpl = (
                'INSERT INTO fixed_ips (address, network_id, reserved, '
                'created_at, deleted, allocated, leased) VALUES %s'
                % ','.join(['(?, ?, ?, now(), 0, 0, 0)'] * len(ips)))
            store.execute(sql_tmpl, values)
            store.commit()
            flask.flash(
                'Network %s created, %s fixed IPs populated.' % \
                    (network_id, len(ips)), 'success')
            return flask.redirect(flask.url_for('.index'))
    return {'form': form}


@bp.route('delete/<object_id>/', methods=['POST'])
def delete(object_id):
    """Delete network and associated fixed IPs."""
    form = forms.DeleteForm()
    if form.validate_on_submit():
        store = orm.get_store('NOVA_RW')
        exists = store.execute(
            'SELECT count(*) FROM networks where id = ?', 
            (object_id,)).get_one()[0] > 0
        if not exists:
            flask.abort(404)
        store.execute(
            'DELETE FROM networks WHERE id = ? LIMIT 1',
            (object_id,))
        store.commit()
        store.execute(
            'DELETE FROM fixed_ips WHERE network_id = ? LIMIT 1',
            (object_id,))
        store.commit()
        flask.flash('Network deleted.', 'success')
    return flask.redirect(flask.url_for('.index'))
    
    
