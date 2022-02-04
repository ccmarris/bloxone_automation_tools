=====================
B1DDI Demo Automation
=====================

| Version: 0.4.2
| Author: Chris Marrison
| Email: chris@infoblox.com

Description
-----------

This script is designed to provide a standard, simple way to demonstrate
the power of automation with the Bloxone platform for both BloxOne DDI and 
BloxOne Threat Defense. It can be used to create a set of demo data for 
demonstration of the GUI or initial set up for a proof of value.

This includes the the clean up (removal) of this data once the
demonstration is complete or no longer needed.

To simplify configuration and allow for user and customer specific
customisation, the scripts utilise a simple ini file that can be edited with
your favourite text editor.

The script has specifically been written in a *functional* manor to make it
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

    - bloxone 0.8.5+
    - PyYAML

These are specified in the *requirements.txt* file.

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
    import yaml


Basic Configuration
-------------------

There are two simple inifiles for configuration. Although these can be combined
into a single file with the appropriate sections, these have been kept separate
so that API keys, and the bloxone configuration, is maintained separately from
customer specific demo configurations. This helps you maintain a single copy
of your API key that is referenced by multiple customer/demo configurations.

This also allows you to keep copies of what was demonstrated for a particular
customer or purpose and where appropriate use different bloxone accounts easily.

In addition to the inifiles, two YAML files provide additional configuration
utilised in creating the security policy. By default there is no need to 
make any changes to these files, however, for advanced usage these can be
customised as necessary to create an appropriate policy.


bloxone.ini
~~~~~~~~~~~

The *bloxone.ini* file is used by the bloxone module to access the bloxone
API. A sample inifile for the bloxone module is shared as *bloxone.ini* and 
follows the following format provided below::

    [BloxOne]
    url = 'https://csp.infoblox.com'
    api_version = 'v1'
    api_key = '<you API Key here>'

Simply create and add your API Key, and this is ready for the bloxone
module used by the automation demo script. This inifile should be kept 
in a safe area of your filesystem and can be referenced with full path
in the demo.ini file.


demo.ini
~~~~~~~~

A template is also provided for the demo script inifile *demo.ini*. Unless an
alternative is specified on the command line, the script will automatically use
the demo.ini from the current working directory if available.


The format of the demo ini file is::

    [B1_POV]
    # Full path to bloxone module inifile
    b1inifile = bloxone.ini

    # User and customer details
    owner = <username>
    location = <location info>
    customer = <customer name>

    # Alternate pre/postfix configuration
    prefix = %(customer)s
    postfix = %(customer)s

    # B1DDI
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

    # B1TD POV 
    policy_level = medium
    policy = %(prefix)s-policy
    allow_list = %(prefix)s-allow
    deny_list = %(prefix)s-deny
    # Public IP 
    ext_net = x.x.x.x
    ext_cidr = 32
    ext_net_name = %(customer)s-network


The *demo.ini* file uses a single section, however, you can consider the keys 
and *customer*. Most of the remaining keys are automatically created from the
*custom* key, but can be overridden as needed. The exception being the *ext_net*
key used for BloxOne Threat Defense. This has to be globally unique across the
BloxOne Threat Defense Platform.

Only the common keys and app specific keys are required to execute the script
for a particular BloxOne App. 

.. note:: 

    As can be seen the demo inifile references the bloxone.ini file by default
    in the current working directory with the key b1inifile. It is suggested
    that you modify this with the full path to your bloxone ini file.

    For example, *b1inifile = /Users/<username>/configs/bloxone.ini*


The demo ini file is used to form the naming conventions and
Owner tagging to both ensure that it is easy to identify who the demo data
belongs to and ensure this is identified by automated clean-up scripts within
the Infoblox demo environments.

BloxOne DDI Specific keys
~~~~~~~~~~~~~~~~~~~~~~~~~

For BloxOne DDI you can customise the number of networks, subnet masks, and 
the first base network for the auto created demo data, as well as, the number 
of ips and hosts to be created.

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

BloxOne Threat Defense Specific keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For BloxOne Threat Defense you can customise the names used to generate the
network and custom (named) lists, as well as the policy name. In this case,
the external network or IP must be specified using the *ext_net* key and where
appropriate the *ext_cidr* key.

The *policy_level* key is used to specify the acceptable risk level of the 
customer and is set to *medium* by default. This controls the threat feeds
and associated policy actions that are implemented when creating the security
policy. The associated policy definition is defined in the 
*policy_definitions.yml* file.


YAML Configuration files
~~~~~~~~~~~~~~~~~~~~~~~~

There are two YAML configuration files used in the creation of the security
policy. The *policy_definitions.yml* file defines the threat feeds and 
associated policy actions as set by the *policy_level* key in the demo ini 
file. These definitions define the action, and order of the threat feeds with 
prefined sets for high, mediam and low 'levels'. These default 'levels' are
based on Infoblox experience and knowledge about the threat feeds.

The format of the *policy_definitions.yml* file is shown in the sample below::

    ---
    policy_name:
        action_block:
            - name: base
              type: named_feed
            - name: Threat Insight - Data Exfiltration
              type: custom_list
        
        action_log:
            - name: ext_ransomware
              type: named_feed


The prefix *policy_* is required, therefore to create a custom 'level' the 
first line of the definition section, must be of the format policy_*<name>* 
e.g. *policy_custom1*. This would then be referenced using the *policy_level* 
key in the demo ini file simply as *custom1*::

    policy_level = custom1


The second YAML configuration file is the *filters.yml* file. This file defines
Web Category Filters and Application Filters, including the name of the filter,
descrition, categories or applications and the policy action.

These are automatically positioned in the appropriate place in the security
policy based on the action type. You can define your own filters based on 
the following formats or additional by following the examples in the default
file.

Please see the sample of the *filters.yml* file below, including the 
examples that are commented by default::


    ---
    # Infoblox Web Categories 
    # Allowed Actions: action_block, action_redirect, action_log, action_allow 
    category_filters:
    - name: risk_fraud_crime
        description: Risk, fraud and crime web categories
        categories:
        - Browser Exploits
        - Consumer Protection
        - Illegal UK
        - Malicious Downloads
        - Malicious Sites
        - Phishing
        action: action_block

    # Application Filters
    # Allowed Actions: action_block, action_redirect, action_log, action_allow 
    # action_allow_with_resolution (app filters only)
    application_filters:
        - name: data_storage_apps
            desctiption: Data Storage Apps example for detection/logging
            apps:
                - Jumpshare
                - Google Drive
                - Zippyshare
                - Dropbox
            action: action_log

    # Addional Examples:
        # - name: Office365
            # description: Office365
            # apps:
                # - Microsoft 365
            # action: action_allow_with_local_resolution

        # - name Facebook
            # descrition: Social Media
            # apps:
                # - Facebook
            # action: action_block


Usage
-----

The bloxone_automation_tools.py provides the ability to automatically create
and remove configurations, based on the ini and yml files for both the 
BloxOne DDI and BloxOne Threat Defense apps on the Infoblox BloxOne SaaS 
platform.

This allows the script to be used for both demonstration purposes of the
automation capabilities provide by the BloxOne APIs, or the basis for initial
deployments. With the customisation capabilities that the YAML files provide
this is particularly useful in automatically creating 'best practise' security
policies for BloxOne Threat Defense.

The script supports -h or --help on the command line to access the options 
available::

    $ ./bloxone_automation_tools.py --help
    usage: bloxone_automation_tools.py [-h] -a APP [-c CONFIG] [-r] [-o] [-d]

    BloxOne Automation Tools

    optional arguments:
        -h, --help            show this help message and exit
        -a APP, --app APP     BloxOne Application [ b1ddi, b1td ]
        -c CONFIG, --config CONFIG
                              Overide Config file
        -r, --remove          Clean-up demo data
        -o, --output          Ouput log to file <customer>.log
        -d, --debug           Enable debug messages


With configuration and customisation performed within the ini files 
or for more advance usage the ini and YAML files, the script
becomes very simple to run with effectively two modes:

    1. Create mode
    2. Clean up mode

To run in create mode, simply point the script at the appropriate ini fle 
as required and specify which application using the --app option specifying
either *b1ddi* or *b1td*.

For example::

    % ./b1ddi_demo_automation.py --app b1ddi
    % ./b1ddi_demo_automation.py --app b1td
    % ./b1ddi_demo_automation.py -c <path to inifile> --app <app>
    % ./b1ddi_demo_automation.py -c ~/configs/customer.ini --app b1ddi
    % ./b1ddi_demo_automation.py -c ~/configs/customer.ini --app b1td
    
To run in clean-up mode simply add *--remove* or *-r* to the command line::

    % ./b1ddi_demo_automation.py --app b1ddi --remove
    % ./b1ddi_demo_automation.py --app b1td --remove
    % ./b1ddi_demo_automation.py -c <path to inifile> --app <app> --remove
    % ./b1ddi_demo_automation.py -c ~/configs/customer.ini --app b1ddi --remove
    % ./b1ddi_demo_automation.py -c ~/configs/customer.ini --app b1td --remove

.. note::

    It is safe to run the script multiple times in either mode. As the script
    checks for the existence of the Objects.

.. important::

    If you have issues running in 'create' mode or interupt the script please
    ensure that you run in 'clean-up' mode using --remove. 

    This will clean up any partially create objects where applicable.


BloxOne DDI
~~~~~~~~~~~

.. code::

    --app b1ddi

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


BloxOne Threat Defense
~~~~~~~~~~~~~~~~~~~~~~

.. code::

    --app b1td

In create mode the script will create an External Network; Custom List for
allow and deny, with an example in each; example Category and Application 
Filters; and a Security Policy combining these with the appropriate risk level 
of threat feeds applied in a best practise manner.

These are controlled by the following keys in the ini file::

    # B1TD
    policy_level = medium
    policy = %(prefix)s-policy
    allow_list = %(prefix)s-allow
    deny_list = %(prefix)s-deny
    # Public IP 
    ext_net = x.x.x.x
    ext_cidr = 32
    ext_net_name = %(customer)s-network

.. note::

    The external network *must* be meet the uniqueness requirements of the
    BloxOne Platform.


The policy actions, threat feeds, and filters are all configured in the 
*policy_definitions.yml* and *filters.yml* files.

The script automatically orders the Policy Rules based on the rule type and
associated action. The order of the threat feeds associated with each action
will then use the order presented in the *policy_definitions.yml* file.


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


Or for BloxOne Threat Defense::

    +++ Network List Zaphod-network created
    --- Security Policy Zaphod-policy not created


Example output can be found in the *example-b1ddi.txt* and *example-b1td.txt*
files.

In addition to the output to console the *-o* or *--out* option can be used 
to create a <customer>.log file.

License
-------

This project, and the bloxone module are licensed under the 2-Clause BSD License
- please see LICENSE file for details.

Aknowledgements
---------------

Thanks to the BloxOne DDI SME Team, and others, for beta testing the BloxOne
DDI functionality and Steve Makousky, Steve Salo, Ross Gibson and Gary Cox for
beta testing the BloxOne Threat Defense functionality. Thank you for providing 
all your feedback prior to this being released in to the wild.
