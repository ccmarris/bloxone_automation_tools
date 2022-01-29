=====================
B1DDI Demo Automation
=====================

Version: 0.2.9
Author: Chris Marrison
Email: chris@infoblox.com

Description
-----------

This script is designed to provide a standard, simple way to demonstrate
the power of automation with the Bloxone DDI platform and create a set of 
demo data for demonstration of the GUI.

This includes the the clean up (removal) of this demo data once the
demonstration is complete.

To simplify configuration and allow for user and customer specific
customisation, the scripts utilise a simple ini file that can be edited with
your favourite text editor.

The script has specifically been written in a *functional* manor to make them
simple to understand.


Prerequisites
-------------

Python 3.6 or above


Installing Python
~~~~~~~~~~~~~~~~~

You can install the latest version of Python 3.x by downloading the appropriate
installer for your system from `python.org <https://python.org>`_.

.. note::

  If you are running MacOS Catalina (or later) Python 3 comes pre-installed.
  Previous versions only come with Python 2.x by default and you will therefore
  need to install Python 3 as above or via Homebrew, Ports, etc.

  By default the python command points to Python 2.x, you can check this using 
  the command::

    $ python -V

  To specifically run Python 3, use the command::

    $ python3


.. important::

  Mac users will need the xcode command line utilities installed to use pip3,
  etc. If you need to install these use the command::

    $ xcode-select --install

.. note::

  If you are installing Python on Windows, be sure to check the box to have 
  Python added to your PATH if the installer offers such an option 
  (it's normally off by default).


Modules
~~~~~~~

Non-standard modules:

    - bloxone 0.5.6+

The latest version of the bloxone module is available on PyPI and can simply be
installed using::

    pip3 install bloxone --user

To upgrade to the latest version::

    pip3 install bloxone --user --upgrade

Complete list of modules::

    import bloxone
    import os
    import sys
    import json
    import argparse
    import logging
    import datetime
    import ipaddress
    import time


Basic Configuration
-------------------

There are two simple inifiles for configuration. Although these can be combined
into a single file with the appropriate sections, these have been kept separate
so that API keys, and the bloxone configuration, is maintained separately from
customer specific demo configurations. This helps you maintain a single copy
of your API key that is referenced by multiple demo configurations.

This also allows you to keep copies of what was demonstrated for a particular
customer or purpose and where appropriate use different bloxone accounts easily.

A sample inifile for the bloxone module is shared as *bloxone.ini* and follows
the following format provided below::

    [BloxOne]
    url = 'https://csp.infoblox.com'
    api_version = 'v1'
    api_key = '<you API Key here>'

You can therefore simply add your API Key, and this is ready for the bloxone
module used by the automation demo script.

A template is also provided for the demo script inifile *demo.ini*. Unless an
alternative is specified on the command line, the script will automatically use
the demo.ini from the current working directory if available.


The format of the demo ini file is::

    
    [B1DDI_Demo]
    # Full path to bloxone module inifile
    b1inifile = <path to ini file for bloxone module>

    # User and customer details
    owner = <username>
    location = <location info>
    customer = <customer name>

    # Alternate postfix configuration
    postfix = %(customer)s

    # DNS Configuration
    tld = com
    dns_view = %(owner)s-%(postfix)s-view
    dns_domain = %(customer)s.%(tld)s
    nsg = b1ddi-auto-demo
    no_of_records = 10

    # IP Space Configuration
    ip_space = %(owner)s-%(postfix)s-demo
    no_of_networks = 10
    no_of_ips = 5
    base_net = 192.168.0.0
    container_cidr = 16
    cidr = 24
    net_comments = Office Network, VoIP Network, POS Network, Guest WiFI, IoT Network


Once your API key is configured in the bloxone.ini, and your username and
customer name are set it is possible to run the scripts with the remaining
defaults or tweak as you need!


.. note:: 

    As can be seen the demo inifile references the bloxone.ini file by default
    in the current working directory with the key b1inifile. It is suggested
    that you modify this with the full path to your bloxone ini file.

    For example, *b1inifile = /Users/<username>/configs/bloxone.ini*


The demo ini file is used to form the naming conventions and
Owner tagging to both ensure that it is easy to identify who the demo data
belongs to and ensure this is identified by automated clean-up scripts within
the Infoblox demo environments.

You can customise the number of networks, subnet masks, and the first base 
network for the auto created demo data, as well as, the number of ips and 
hosts to be created.

.. note::

    Basic checks of of the base network and CIDR prefix lengths is performed by
    the script.

One important key in the inifile is *nsg* this is used to facilitate the
creation of authoritative DNS zones. A generic Name Server Group has been
defined, however, you are able to define your own and utilise this as needed.
This also means that it is possible for you to demostrate the automation and
population of an On Prem Host for DNS.

.. important::

    The default bloxone.ini and script assumes that the b1ddi-auto-demo
    DNS Server Group (NSG) already exists. If you are running outside of Infoblox 
    you will need to create this NSG, or specify an alternative. This requires
    an On Prem Host to be assigned to the NSG.

    Within Infoblox, the default NSG has an associated On Prem Host that is not
    in use. Please do not try to use or modify either the On Prem Host or the
    NSG as this may affect other peoples ability to perform demonstrations.
    Please create your own and customise your inifile appropriately.



Usage
-----

For simplicity the b1ddi-automation-demo.py script is use to both create and remove the demo
data sets.

The script supports -h or --help on the command line to access the options available::

    $ ./b1ddi_demo_automation.py --help
    usage: b1ddi_demo_automation.py [-h] [-c CONFIG] [-d] [-r]

    SE Automation Demo - Create Demo

    optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG, --config CONFIG
                          Overide Config file
    -d, --debug           Enable debug messages
    -r, --remove          Clean-up demo data
    
With all the configuration and customisation performed within the ini files the script
becomes very simple to run with effectively two modes:

    1. Create mode
    2. Clean up mode

To run in create mode, simply point the script at the appropriate ini fle as required.
For example::

    % ./b1ddi_demo_automation.py OR python3 b1ddi-demo-automation.py
    % ./b1ddi_demo_automation.py -c <path to inifile>
    % ./b1ddi_demo_automation.py -c ~/configs/customer.ini
    
To run in clean-up mode simply add *--remove* or *-r* to the command line::

    % ./b1ddi_demo_automation.py --remove
    % ./b1ddi_demo_automation.py -c <path to inifile> --remove
    % ./b1ddi_demo_automation.py -c ~/configs/customer.ini --remove

.. note::

    It is safe to run the script multiple times in either mode. As the script
    checks for the existence of the IP Space and DNS View.

.. important::

    If you have issues running in 'create' mode or interupt the script please
    ensure that you run in 'clean-up' mode using --remove. 

    This will clean up any partially create IP Space or DNS View


The details
~~~~~~~~~~~

In create mode the script creates an IP Space with an address block, subnets are then 
created wth ranges and IP reservations. These are based on the following elements in 
the ini file::

    ip_space = %(owner)s-%(postfix)s-demo
    base_net = 192.168.0.0
    no_of_networks = 10
    no_of_ips = 5
    container_cidr = 16
    cidr = 24
    net_comments = Office Network, VoIP Network, POS Network, Guest WiFI, IoT Network

The ranges will effectively take up the top 50% of the subnet, whilst the number
of IP reservations is ether be the *no_of_ips* or 25% of the subnet, which ever
is the smaller number.

Configuration checking is performed to confirm that *base_net* is a valid IPv4
address and both *container_cidr* and *cidr* are suitable and larger than a 
/28 and /29 respectively.

Subnet are created with a "Comment/Description" that is randomly assigned from 
the list of descriptions in *net_comments*. A default set is included in the 
example *demo.ini* file, however, this can be customised as needed. The number
of descriptions is not fixed to the five examples so you can include more or 
less descriptions as needed - this is just a sample set.

A DNS View is then also created with an authoritative forward lookup zone and
/16 reverse lookup zone for the *base_net* (adjusted for byte boundaries). These
zones are populated with a set of A records wth corresponding PTRs. 

These are controlled by the following keys in the ini file::

    # DNS Configuration
    tld = com
    dns_view = %(owner)s-%(postfix)s-view
    dns_domain = %(customer)s.%(tld)s
    nsg = b1ddi-auto-demo
    no_of_records = 10

.. note::
    
    The script will create an appropriate number of A and PTR records
    based on the *no_of_records* or the 'size' of the base network, which
    ever is the smaller number.

Output
~~~~~~

Section headers are represented using::

     ============ Section Heading ============

Subsections are represented using::

    ------------ Subsection ------------

Although the majority of messages are general information, certain
message use the convention of "+++ message" for positive messages about
the configuration, whilst negative messages use "--- message". For example::

    INFO: +++ Range created in network 192.168.0.0/24
    INFO: --- Subnet 192.168.1.0/24 not created

Example output can be found in the file *example1.txt*.

In addition to the output to console the :option:`-o` or :option:`--out`
can be used to create a <customer>.log file.

License
-------

This project, and the bloxone module are licensed under the 2-Clause BSD License
- please see LICENSE file for details.

Aknowledgements
---------------

Thanks to the BloxOne DDI SME Team, and others, for beta testing and providing
feedback prior to releasing this to the wild.
