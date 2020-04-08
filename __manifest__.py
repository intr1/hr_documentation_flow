# -*- coding: utf-8 -*-

{
    'name': 'Documentation Flow',
    'version': '0.1',
    'category': 'Human Resources',
    'sequence': 5,
    'summary': 'manage Document flow',
    'description': """
    Module is done as a Test/Show case for the bloopark systems GmbH & Co. KG.
    before installing this module make sure that Employees(hr) module is installed.
    this module will add menu under employee>>configuration menu, named Documentation Flow,
    also menu named Flow in next to employee directory.
    by the configuration you can create flexible flows using next parameters : Manager - employee parent(manager),
    Dep. manager - any department manager,
    and  employee - any employeee which you want.
    after the configuration is done, users can create records in Flow menu item.
    on creation of record, system will generate list of the employees who will take action in this record Flow,
    based on the initiator and choosen flow configuration.
    in generated list is written employee name, comment and status(in, out, waiting).
    this statuses means:
                        in - it means that the employee can do action, approve or cancel.
                        out - employee already done action.
                        waiting - employee is waiting to other flow participants to do action.
    by this list system defines who is able to do action(validate/cancel), this action can be done only by employee have 'in' status in flow list.
    i have not creted security groups, it automaticly adds model access records to internal users(base.group_user).
    module is built by Soso Ninidze, for any question please contact through mail sosoninidze@gmail.com
    """,
    'website': 'kamechi.club',
    'images': [
    ],
    'depends': [
        'base_setup',
        'mail',
        'resource',
        'web',
        'mail_bot',
        'hr'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_documentation_view.xml',
    ],
    'demo': [
        
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
