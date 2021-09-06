#!/usr/local/bin/python3
#vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
'''

 Description:

    BloxOne Proof of Value Demonstration Tools

 Requirements:
   Python3 with re, ipaddress, requests and sqlite3 modules

 Author: Chris Marrison

 Date Last Updated: 20210906

 Todo:

 Copyright (c) 2021 Chris Marrison / Infoblox

 Redistribution and use in source and binary forms,
 with or without modification, are permitted provided
 that the following conditions are met:

 1. Redistributions of source code must retain the above copyright
 notice, this list of conditions and the following disclaimer.

 2. Redistributions in binary form must reproduce the above copyright
 notice, this list of conditions and the following disclaimer in the
 documentation and/or other materials provided with the distribution.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 POSSIBILITY OF SUCH DAMAGE.

'''
__version__ = '0.3.0'
__author__ = 'Chris Marrison'
__author_email__ = 'chris@infoblox.com'

import logging
import os
import sys
import json
import bloxone
import argparse
import configparser
import datetime
import ipaddress
import random
import time


# Global Variables
log = logging.getLogger(__name__)
# console_handler = logging.StreamHandler(sys.stdout)
# log.addHandler(console_handler)

def parseargs():
    '''
    Parse Arguments Using argparse

    Parameters:
        None

    Returns:
        Returns parsed arguments
    '''
    parse = argparse.ArgumentParser(description='SE Automation Demo - Create Demo')
    parse.add_argument('-o', '--output', action='store_true', 
                        help="Ouput log to file <customer>.log") 
    parse.add_argument('-a', '--app', type=str, default='b1ddi',
                        help="BloxOne Application [b1ddi, b1td]")
    parse.add_argument('-c', '--config', type=str, default='demo.ini',
                        help="Overide Config file")
    parse.add_argument('-d', '--debug', action='store_true', 
                        help="Enable debug messages")
    parse.add_argument('-r', '--remove', action='store_true', 
                        help="Clean-up demo data")

    return parse.parse_args()


def setup_logging(debug=False, usefile=False):
    '''
     Set up logging

     Parameters:
        advanced (bool): True or False.

     Returns:
        None.

    '''

    # Set advanced level
    # if level == "advanced":
     #    logging.addLevelName(15, "advanced")
      #   logging.basicConfig(level=advanced,
       #                      format='%(asctime)s %(levelname)s: %(message)s')
    if debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s')
    else:
        if usefile:
            # Full log format
            logging.basicConfig(level=logging.INFO,
                                format='%(asctime)s %(levelname)s: %(message)s')
        else:
            # Simple log format
            logging.basicConfig(level=logging.INFO,
                                format='%(levelname)s: %(message)s')

    return


def open_file(filename):
    '''
    Attempt to open output file

    Parameters:
        filename (str): desired filename

    Returns file handler
        handler (file): File handler object
    '''
    if os.path.isfile(filename):
        backup = filename+".bak"
        try:
            shutil.move(filename, backup)
            log.info("Outfile exists moved to {}".format(backup))
            try:
                handler = open(filename, mode='w')
                log.info("Successfully opened output file {}.".format(filename))
            except IOError as err:
                log.error("{}".format(err))
                handler = False
        except:
            logging.warning("Could not back up existing file {}, exiting.".format(filename))
            handler = False
    else:
        try:
            handler = open(filename, mode='w')
            log.info("Opened file {} for invalid lines.".format(filename))
        except IOError as err:
            log.error("{}".format(err))
            handler = False

    return handler



def read_demo_ini(ini_filename):
    '''
    Open and parse ini file

    Parameters:
        ini_filename (str): name of inifile

    Returns:
        config (dict): Dictionary of BloxOne configuration elements

    '''
    # Local Variables
    cfg = configparser.ConfigParser()
    config = {}
    ini_keys = [ 'b1inifile', 'owner', 'location', 'customer', 'postfix', 
                'tld', 'dns_view', 'dns_domain', 'nsg', 'no_of_records', 
                'ip_space', 'base_net', 'no_of_networks', 'no_of_ips', 
                'container_cidr', 'cidr', 'net_comments']

    # Attempt to read api_key from ini file
    try:
        cfg.read(ini_filename)
    except configparser.Error as err:
        logging.error(err)

    # Look for demo section
    if 'B1DDI_Demo' in cfg:
        for key in ini_keys:
            # Check for key in BloxOne section
            if key in cfg['B1DDI_Demo']:
                config[key] = cfg['B1DDI_Demo'][key].strip("'\"")
                logging.debug('Key {} found in {}: {}'.format(key, ini_filename, config[key]))
            else:
                logging.warning('Key {} not found in B1DDI_demo section.'.format(key))
                config[key] = ''
    else:
        logging.warning('No B1DDI_demo Section in config file: {}'.format(ini_filename))

    return config


def create_tag_body(config, **params):
    '''
    Add Owner tag and any others defined in **params

    Parameters:
        owner (str): Typically username
        params (dict): Tag key/value pairs
    
    Returns:
        tags (str): JSON string to append to body
    '''
    now = datetime.datetime.now()  
    # datestamp = now.isoformat()
    datestamp = now.strftime('%Y-%m-%dT%H:%MZ')
    owner = config['owner']
    location = config['location']

    tags = {}
    tags.update({"Owner": owner})
    tags.update({"Location": location})
    tags.update({"Usage": "AUTOMATION DEMO"})
    tags.update({"Created": datestamp})


    if params:
        tags.update(**params)
        tag_body = '"tags":' + json.dumps(tags) 
    else:
        tag_body = '"tags":' + json.dumps(tags) 
    
    log.debug("Tag body: {}".format(tag_body))

    return tag_body


def ip_space(b1ddi, config):
    '''
    Create IP Space

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful
    '''
    status = False

    # Check for existence
    if not b1ddi.get_id('/ipam/ip_space', key="name", value=config['ip_space']):
        log.info("---- Create IP Space ----")
        tag_body = create_tag_body(config)
        body = '{ "name": "' + config['ip_space'] + '",' + tag_body +' }'
        log.debug("Body:{}".format(body))

        log.info("Creating IP_Space {}".format(config['ip_space']))
        response = b1ddi.create('/ipam/ip_space', body=body)
        if response.status_code in b1ddi.return_codes_ok:
            log.info("IP_Space {} Created".format(config['ip_space']))
            status = True
        else:
            log.warning("IP Space {} not created".format(config['ip_space']))
            log.debug("Return code: {}".format(response.status_code))
            log.debug("Return body: {}".format(response.text))
    else:
        log.warning("IP Space {} already exists".format(config['ip_space']))
    
    return status


def create_networks(b1ddi, config):
    '''
    Create Subnets

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful
    '''
    status = False
    net_comments = config['net_comments'].split(',')

    # Get id of ip_space
    log.info("---- Create Address Block and subnets ----")
    space = b1ddi.get_id('/ipam/ip_space', key="name", 
                        value=config['ip_space'], include_path=True)
    if space:
        log.info("IP Space id found: {}".format(space))

        tag_body = create_tag_body(config)
        base_net = config['base_net']

        # Create subnets
        cidr = config['container_cidr']
        body = ( '{ "address": "' + base_net + '", '
                + '"cidr": "' + cidr + '", '
                + '"space": "' + space + '", '
                + '"comment": "Internal Address Allocation", '
                + tag_body + ' }' )
        log.debug("Body:{}".format(body))
        log.info("~~~~ Creating Addresses block {}/{}~~~~ "
                .format(base_net, cidr))
        response = b1ddi.create('/ipam/address_block', body=body)

        if response.status_code in b1ddi.return_codes_ok:
            log.info("+++ Address block {}/{} created".format(base_net, cidr))

            # Create subnets
            network = ipaddress.ip_network(base_net + '/' + cidr)
            # Reset cidr for subnets
            cidr = config['cidr']
            subnet_list = list(network.subnets(new_prefix=int(cidr)))
            if len(subnet_list) < int(config['no_of_networks']):
                nets = len(subnet_list)
                log.warning("Address block only supports {} subnets".format(nets))
            else:
                nets = int(config['no_of_networks'])
            log.info("~~~~ Creating {} subnets ~~~~".format(nets))
            for n in range(nets):
                address = str(subnet_list[n].network_address)
                comment = net_comments[random.randrange(0,len(net_comments))]
                body = ( '{ "address": "' + address + '", '
                        + '"cidr": "' + cidr + '", '
                        + '"space": "' + space + '", '
                        + '"comment": "' + comment + '", '
                        + tag_body + ' }' )
                log.debug("Body:{}".format(body))
                log.info("Creating Subnet {}/{}".format(address, cidr))
                response = b1ddi.create('/ipam/subnet', body=body)

                if response.status_code in b1ddi.return_codes_ok:
                    log.info("+++ Subnet {}/{} successfully created".format(address, cidr))
                    if populate_network(b1ddi, config, space, subnet_list[n]):
                        log.info("+++ Network populated.")
                        status = True
                    else:
                        log.warning("--- Issues populating network")
                else:
                    log.warning("--- Subnet {}/{} not created".format(network, cidr))
                    log.debug("Return code: {}".format(response.status_code))
                    log.debug("Return body: {}".format(response.text))

        else:
            log.warning("--- Address Block {}/{} not created".format(base_net, cidr))
            log.debug("Return code: {}".format(response.status_code))
            log.debug("Return body: {}".format(response.text))
    else:
        log.warning("IP Space {} does not exist".format(config['ip_space']))

    return status


def populate_network(b1ddi, config, space, network):
    '''
    Create DHCP Range and IPs

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
        network (str): Network base address
    
    Returns:
        status (bool): True if successful
    '''
    status = False

    log.info("~~~~ Creating Range ~~~~")
    tag_body = create_tag_body(config)

    net_size = network.num_addresses
    range_size = int(net_size / 2)
    broadcast = network.broadcast_address
    start_ip = str(broadcast - (range_size + 1))
    end_ip = str(broadcast - 1)

    body = ( '{ "start": "' + start_ip + '", "end": "' + end_ip +
            '", "space": "' + space + '", '  + tag_body + ' }' )
    log.debug("Body:{}".format(body))

    log.info("Creating Range start: {}, end: {}".format(start_ip, end_ip))
    response = b1ddi.create('/ipam/range', body=body)
    if response.status_code in b1ddi.return_codes_ok:
        log.info("+++ Range created in network {}".format(str(network)))
        status = True
    else:
        log.warning("--- Range for network {} not created".format(str(network)))
        log.debug("Return code: {}".format(response.status_code))
        log.debug("Return body: {}".format(response.text))

    # Add reservations

    no_of_ips = int(range_size / 2)
    # If number requested is lt than caluculated use configured
    if int(config['no_of_ips']) < no_of_ips:
        no_of_ips = int(config['no_of_ips'])
    log.info("~~~~ Creating {} IPs ~~~~".format(no_of_ips))
    ips = list(network.hosts())
    for ip in range(1, no_of_ips):
        address = str(ips[ip])
        body = ( '{ "address": "' + address + '", "space": "' 
                + space + '", '  + tag_body + ' }' )
        log.debug("Body:{}".format(body))

        log.info("Creating IP Reservation: {}".format(address))
        response = b1ddi.create('/ipam/address', body=body)
        if response.status_code in b1ddi.return_codes_ok:
            log.info("+++ IP {} created".format(address))
            status = True
        else:
            log.warning("--- IP {} not created".format(address))
            log.debug("Return code: {}".format(response.status_code))
            log.debug("Return body: {}".format(response.text))
            status = False

    return status


def populate_dns(b1ddi, config):
    '''
    Populate DNS View with zones/records

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
        view (str): Network base address
    
    Returns:
        bool: True if successful
    '''
    status = False

    if create_zones(b1ddi, config):
        status = True
    else:
        status = False

    return status



def create_hosts(b1ddi, config):
    '''
    Create DNS View

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        bool: True if successful
    '''
    status = False

    return status


def create_zones(b1ddi, config):
    '''
    Create DNS Zones

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful
    '''
    status = False

    # Get id of DNS view
    log.info("---- Create Forward & Reverse Zones ----")
    view = b1ddi.get_id('/dns/view', key="name", 
                        value=config['dns_view'], include_path=True)
    if view:
        log.info("DNS View id found: {}".format(view))
        # Check for NSG
        nsg = b1ddi.get_id('/dns/auth_nsg', 
                            key="name", 
                            value=config['nsg'],
                            include_path=True)
        if nsg:
            # Prepare Body
            tag_body = create_tag_body(config)
            zone = config['dns_domain']
            body = ( '{ "fqdn": "' + zone + '", "view": "' + view + '", ' 
                    + '"nsgs": ["' + nsg + '"], '
                    + '"primary_type": "cloud", '
                    + tag_body + ' }' )
            # Create zone
            response = b1ddi.create('/dns/auth_zone', body)
            if response.status_code in b1ddi.return_codes_ok:
                log.info("+++ Zone {} created in view".format(zone))
            else:
                # Log error
                log.warning("--- Zone {} in view {} not created"
                            .format(zone, config['dns_view']))
                log.debug("Return code: {}".format(response.status_code))
                log.debug("Return body: {}".format(response.text))

            # Work out reverse /16 for network  
            r_network = bloxone.utils.reverse_labels(config['base_net'])
            # Remove "last" two octets
            r_network = bloxone.utils.get_domain(r_network, no_of_labels=2)
            zone = r_network + '.in-addr.arpa.'
            body = ( '{ "fqdn": "' + zone + '", "view": "' + view + '", ' 
                    + '"nsgs": ["' + nsg + '"], '
                    + '"primary_type": "cloud", '
                    + tag_body + ' }' )

            # Create reverse zone
            response = b1ddi.create('/dns/auth_zone', body)
            if response.status_code in b1ddi.return_codes_ok:
                log.info("+++ Zone {} created in view".format(zone))
            else:
                # Log error
                log.warning("--- Zone {} in view {} not created"
                            .format(zone, config['dns_view']))
                log.debug("Return code: {}".format(response.status_code))
                log.debug("Return body: {}".format(response.text))

            # Add Records to zones
            if add_records(b1ddi, config):
                log.info("+++ Records added to zones")
                status = True
            else:
                log.warning("--- Failed to add records")
                status = False
        else:
            log.warning("NSG {} not found. Cannot create zones."
                        .format(config['nsg']))
            status = False

    return status


def create_dnsview(b1ddi, config):
    '''
    Create DNS Hosts

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        bool: True if successful
    '''
    status = False

    # Check for existence
    if not b1ddi.get_id('/dns/view', key="name", value=config['dns_view']):
        log.info("---- Create DNS View ----")
        tag_body = create_tag_body(config)
        body = '{ "name": "' + config['dns_view'] + '",' + tag_body +' }'
        log.debug("Body:{}".format(body))

        log.info("Creating DNS View {}".format(config['dns_view']))
        response = b1ddi.create('/dns/view', body=body)
        if response.status_code in b1ddi.return_codes_ok:
            log.info("DNS View {} Created".format(config['dns_view']))
            status = True
        else:
            log.warning("DNS View {} not created".format(config['dns_view']))
            log.debug("Return code: {}".format(response.status_code))
            log.debug("Return body: {}".format(response.text))
    else:
        log.warning("DNS View {} already exists".format(config['dns_view']))
   
    return status


def add_records(b1ddi, config):
    '''
    Add records to zone

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        zone (str): Name of zone
        view
        no_of_records (int): number of records to create
        type (str): Record type
    
    Returns:
        bool: True if successful
    '''
    status = False
    zone_id = ''
    zone = config['dns_domain']

    view = b1ddi.get_id('/dns/view', key="name", 
                        value=config['dns_view'], include_path=True)
    if view:
        filter = ( '(fqdn=="' + zone + '")and(view=="' + view + '")' )
        # Get zone id
        response  = b1ddi.get('/dns/auth_zone', 
                                _filter=filter, 
                                _fields="fqdn,id") 
        if response.status_code in b1ddi.return_codes_ok:
            if 'results' in response.json().keys():
                zones = response.json()['results']
                if len(zones) == 1:
                    zone_id = zones[0]['id']
                    log.debug("Zone ID: {} Found".format(zone_id))
                else:
                    log.warning("Too many results returned for zone {}"
                                .format(zone))
            else:
                log.warning("No results returned for zone {}"
                            .format(zone))
                log.debug("Return code: {}".format(response.status_code))
                log.debug("Return body: {}".format(response.text))
        else:
            log.error("--- Request for zone {} failed".format(zone))
            log.debug("Return code: {}".format(response.status_code))
            log.debug("Return body: {}".format(response.text))

        # Create Records
        if zone_id:
            record_count = 0
            network = ipaddress.ip_network(config['base_net'] + '/' + config['cidr'])
            net_size = int(network.num_addresses) - 2
            # Check we can fit no_of_records in network
            if int(config['no_of_records']) > net_size:
                no_of_records = net_size
            else:
                no_of_records = int(config['no_of_records'])

            tag_body = create_tag_body(config)

            # Generate records and add to zone
            for n in range(1, (no_of_records + 1)):
                hostname = "host" + str(n)
                address = str(network.network_address + n)
                body = ( '{"name_in_zone":"' + hostname + '",' +
                         '"zone": "' + zone_id + '",' +
                         '"type": "A", ' +
                         '"rdata": {"address": "' + address + '"}, ' +
                         '"options": {"create_ptr": true},' + 
                         '"inheritance_sources": ' +
                         '{"ttl": {"action": "inherit"}}, ' +
                         tag_body + ' }' )
                log.debug("Body: {}".format(body))         
                response = b1ddi.create('/dns/record', body)
                if response.status_code in b1ddi.return_codes_ok:
                    log.info("Created record: {}.{} with IP {}"
                             .format(hostname, zone, address))
                    record_count += 1
                else:
                    log.warning("Failed to create record {}.{}"
                                .format(hostname, zone))
                    log.debug("Return code: {}".format(response.status_code))
                    log.debug("Return body: {}".format(response.text))
            if record_count == no_of_records:
                log.info("+++ Successfully created {} DNS Records"
                         .format(record_count))
                status = True
            else:
                log.info("--- Only {} DNS Records created".format(record_count))
                status = False
        else:
            log.warning("--- Unable to add records to zone {} in view {}"
                        .format(zone,view))
            status = False

    else:
        log.error("--- Request for id of view {} failed"
                  .format(config['dns_view']))
        log.debug("Return code: {}".format(response.status_code))
        log.debug("Return body: {}".format(response.text))

    return status


def create_demo(b1ddi, config):
    '''
    Create the demo data

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful

    '''
    exitcode = 0

    # Create IP Space
    if ip_space(b1ddi, config):
        # Create network structure
        if create_networks(b1ddi, config):
            log.info("+++ Successfully Populated IP Space")
        else:
            log.error("--- Failed to create networks in {}"
                    .format(config['ip_space']))
            exitcode = 1
    else:
        exitcode = 1

    # Create DNS View 
    if create_dnsview(b1ddi, config):
        if populate_dns(b1ddi, config):
            log.info("+++ Successfully Populated DNS View")
        else:
            log.error("--- Failed to create zones in {}"
                    .format(config['dns_view']))
            exitcode = 1
    else:
        exitcode = 1
    
    return exitcode


def clean_up(b1ddi, config):
    '''
    Clean Up Demo Data

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        bool: True if successful
    '''
    exitcode = 0

    # Check for existence
    id = b1ddi.get_id('/ipam/ip_space', key="name", value=config['ip_space'])
    if id:
        log.info("Deleting IP_Space {}".format(config['ip_space']))
        response = b1ddi.delete('/ipam/ip_space', id=id)
        if response.status_code in b1ddi.return_codes_ok:
            log.info("+++ IP_Space {} deleted".format(config['ip_space']))
        else:
            log.warning("--- IP Space {} not deleted due to error".format(config['ip_space']))
            log.debug("Return code: {}".format(response.status_code))
            log.debug("Return body: {}".format(response.text))
            exitcode = 1
    else:
        log.warning("IP Space {} not fonud.".format(config['ip_space'])) 
        exitcode = 1 

    # Check for existence
    id = b1ddi.get_id('/dns/view', key="name", value=config['dns_view'])
    if id:
        log.info("Cleaning up Zones for DNS View {}".format(config['dns_view']))
        if clean_up_zones(b1ddi, id):
            log.info("Deleting DNS View {}".format(config['dns_view']))
            response = b1ddi.delete('/dns/view', id=id)
            if response.status_code in b1ddi.return_codes_ok:
                log.info("+++ DNS View {} deleted".format(config['dns_view']))
            else:
                log.warning("--- DNS View {} not deleted due to error".format(config['dns_view']))
                log.debug("Return code: {}".format(response.status_code))
                log.debug("Return body: {}".format(response.text))
                exitcode = 1
        else:
            log.warning("Unable to clean-up zones in view {}".format(config['dns_view']))
            exitcode = 1
    else:
        log.warning("DNS View {} not fonud.".format(config['dns_view'])) 
        exitcode = 1 

    return exitcode


def clean_up_zones(b1ddi, view_id):
    '''
    Clean up zones for specified view id

    Parameters:

    Returns:
        bool: True if successful
    '''
    status = False
    filter = 'view=="' + view_id + '"'
    response = b1ddi.get('/dns/auth_zone', _filter=filter, _fields="fqdn,id")

    if response.status_code in b1ddi.return_codes_ok:
        if 'results' in response.json().keys():
            zones = response.json()['results']
            if len(zones):
                for zone in zones:
                    id = zone['id'].split('/')[2]
                    log.info("Deleting zone {}".format(zone['fqdn']))
                    r = b1ddi.delete('/dns/auth_zone', id=id)
                    if r.status_code in b1ddi.return_codes_ok:
                        log.info("+++ Zone {} deleted successfully"
                                 .format(zone['fqdn']))
                        status = True
                    else:
                        log.info("--- Zone {} not deleted".format(zone['fqdn']))
                        log.debug("Return code: {}"
                                  .format(response.status_code))
                        log.debug("Return body: {}".format(response.text))
                        status = False
            else:
                log.info("No zones present")
                status = True
        else:
            log.info("No results for view")
    else:
        log.info("--- Unable to retrieve zones for view id = {}"
                 .format(view_id))
        log.debug("Return code: {}".format(response.status_code))
        log.debug("Return body: {}".format(response.text))
        status = False
    
    return status


def check_config(config):
    '''
    Perform some basic network checks on config

    Parameters:
        config (dict): Config Dictionary
    
    Returns:
        config_ok (bool): True if all good
    '''
    config_ok = True
    container = int(config['container_cidr'])
    subnet = int(config['cidr'])

    if not bloxone.utils.validate_ip(config['base_net']):
        log.error("Base network not valid: {}".format(config['base_net']))
        config_ok = False
    elif container < 8 or container > 28:
        log.error("Container CIDR should be between 8 and 28: {}"
                  .format(container))
        config_ok = False
    elif container >= subnet:
        log.error("Container prefix does not contain subnet prefix: {} vs {}"
                  .format(container, subnet))
        config_ok = False
    elif subnet > 29:
        log.error("Subnet CIDR should be /29 or shorter: {}".format(subnet))
        config_ok = False
    elif  not config['no_of_ips']:
        log.error("Key: no_of_ips not declared")
        config_ok = False

    return config_ok

def main():
    '''
    Core Logic
    '''
    exitcode = 0
    usefile = False

    args = parseargs()
    inifile = args.config
    debug = args.debug

    # Read inifile
    config = read_demo_ini(inifile)
    if config['b1inifile']:
        b1inifile = config['b1inifile']
    else:
        # Try to use inifile
        b1inifile = inifile

    if len(config) > 0:
        # Check for file output
        if args.output:
            outputprefix = config['customer']
            usefile = True

        if usefile:
            logfn = outputprefix + ".log"
            hdlr = logging.FileHandler(logfn)
            log.addHandler(hdlr)

        if debug:
            log.setLevel(logging.DEBUG)
            setup_logging(debug=True, usefile=usefile)
        else:
            log.setLevel(logging.INFO)
            setup_logging(debug=False, usefile=usefile)

        log.info("====== B1DDI Automation Demo Version {} ======"
                .format(__version__))

        # Instatiate bloxone 
        b1ddi = bloxone.b1ddi(b1inifile)

        if not args.remove:
            log.info("Checking config...")
            if check_config(config):
                log.info("Config checked out proceeding...")
                log.info("------ Creating Demo Data ------")
                start_timer = time.perf_counter()
                exitcode = create_demo(b1ddi, config)
                end_timer = time.perf_counter() - start_timer
                log.info("---------------------------------------------------")
                log.info(f'Demo data created in {end_timer:0.2f}S')
                log.info("Please remember to clean up when you have finished:")
                command = '$ ' + ' '.join(sys.argv) + " --remove"
                log.info("{}".format(command)) 
            else:
                log.error("Config {} contains errors".format(inifile))
                exitcode = 3
        elif args.remove:
            log.info("------ Cleaning Up Demo Data ------")
            start_timer = time.perf_counter()
            exitcode = clean_up(b1ddi, config)
            end_timer = time.perf_counter() - start_timer
            log.info("---------------------------------------------------")
            log.info(f'Demo data removed in {end_timer:0.2f}S')
        else:
            log.error("Script Error - something seriously wrong")
            exitcode = 99

    else:
        logging.error("No config found in {}".format(inifile))
        exitcode = 2

    return exitcode

### Main ###
if __name__ == '__main__':
    exitcode = main()
    exit(exitcode)
## End Main ###