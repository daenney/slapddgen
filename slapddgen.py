# -*- coding: utf-8 -*-
import crypt
import datetime
import json
import os
import shutil
import tempfile
import uuid
import zlib

import click
import jinja2

SHORT_TIME = '%Y%m%d%H%M%SZ'
LONG_TIME = '%Y%m%d%H%M%S.%fZ'


def CommandWithConfigFile(config_file_param_name):
    class CustomCommandClass(click.Command):
        def invoke(self, ctx):
            config_file = ctx.params[config_file_param_name]
            if config_file is not None:
                with open(config_file) as f:
                    config_data = json.load(f)
                    for key, value in config_data.items():
                        ctx.params[key] = value
            return super(CustomCommandClass, self).invoke(ctx)
    return CustomCommandClass


@click.group()
def cli():
    pass


@cli.command(cls=CommandWithConfigFile('config_file'))
@click.option('--config_file', type=click.Path())
@click.option('--output_dir', type=click.Path())
def generate(**kwargs):
    click.echo("Setting up environment")
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('slapddgen', 'templates')
    )

    cur_time = datetime.datetime.now(datetime.timezone.utc)
    tmpdir = tempfile.TemporaryDirectory()
    os.makedirs(os.path.join(tmpdir.name, 'slapd.d', 'cn=config', 'cn=schema'))
    os.makedirs(os.path.join(tmpdir.name, 'slapd.d', 'cn=config',
                             'olcDatabase={2}mdb'))
    click.echo("Created temporary workspace")

    base_dir = os.path.join(tmpdir.name, 'slapd.d')
    config_dir = os.path.join(base_dir, 'cn=config')

    # Render the templates
    template = env.get_template('slapd.d/cn=config.ldif')
    template.stream(
        entry_uuid=uuid.uuid4(),
        time_short=cur_time.strftime(SHORT_TIME),
        time_long=cur_time.strftime(LONG_TIME),
        salt_format=kwargs['ldap']['saltFormat'],
        config_file=kwargs['ldap']['configFile'],
        config_dir=kwargs['ldap']['configDir'],
        args_file=kwargs['ldap']['argsFile'],
        pid_file=kwargs['ldap']['pidFile'],
    ).dump(os.path.join(base_dir, 'cn=config.ldif'))

    config_dir = os.path.join(base_dir, 'cn=config')

    template = env.get_template('slapd.d/cn=config/cn=module{0}.ldif')
    template.stream(
        entry_uuid=uuid.uuid4(),
        time_short=cur_time.strftime(SHORT_TIME),
        time_long=cur_time.strftime(LONG_TIME),
        module_path=kwargs['ldap']['modulePath'],
        modules=kwargs['ldap']['modules'],
    ).dump(os.path.join(config_dir, 'cn=module{0}.ldif'))

    template = env.get_template('slapd.d/cn=config/cn=schema.ldif')
    template.stream(
        entry_uuid=uuid.uuid4(),
        time_short=cur_time.strftime(SHORT_TIME),
        time_long=cur_time.strftime(LONG_TIME),
    ).dump(os.path.join(config_dir, 'cn=schema.ldif'))

    template = env.get_template(
        'slapd.d/cn=config/olcDatabase={-1}frontend.ldif')
    template.stream(
        entry_uuid=uuid.uuid4(),
        time_short=cur_time.strftime(SHORT_TIME),
        time_long=cur_time.strftime(LONG_TIME),
    ).dump(os.path.join(config_dir, 'olcDatabase={-1}frontend.ldif'))

    template = env.get_template('slapd.d/cn=config/olcDatabase={0}config.ldif')
    template.stream(
        entry_uuid=uuid.uuid4(),
        time_short=cur_time.strftime(SHORT_TIME),
        time_long=cur_time.strftime(LONG_TIME),
        root_dn=kwargs['rootDN'],
        suffix=kwargs['suffix'],
    ).dump(os.path.join(config_dir, 'olcDatabase={0}config.ldif'))

    template = env.get_template(
        'slapd.d/cn=config/olcDatabase={1}monitor.ldif')
    template.stream(
        entry_uuid=uuid.uuid4(),
        time_short=cur_time.strftime(SHORT_TIME),
        time_long=cur_time.strftime(LONG_TIME),
        root_dn=kwargs['rootDN'],
        suffix=kwargs['suffix'],
    ).dump(os.path.join(config_dir, 'olcDatabase={1}monitor.ldif'))

    template = env.get_template('slapd.d/cn=config/olcDatabase={2}mdb.ldif')
    acls = kwargs['mdb']['acls']
    acls = [acl.format(suffix=kwargs['suffix'], base_ou=kwargs['baseOU'])
            for acl in acls]
    passwd = kwargs['rootPW']
    if '{CRYPT}' not in passwd:
        passwd = crypt.crypt(kwargs['rootPW'],
                             salt=crypt.mksalt(method=crypt.METHOD_SHA512,
                                               rounds=50000))
        passwd = '{{CRYPT}}{0}'.format(passwd)

    template.stream(
        entry_uuid=uuid.uuid4(),
        time_short=cur_time.strftime(SHORT_TIME),
        time_long=cur_time.strftime(LONG_TIME),
        suffix=kwargs['suffix'],
        size=kwargs['mdb']['size'],
        indices=kwargs['mdb']['indices'],
        acls=acls,
        password=passwd,
        root_dn=kwargs['rootDN'],
    ).dump(os.path.join(config_dir, 'olcDatabase={2}mdb.ldif'))

    db_dir = os.path.join(config_dir, 'olcDatabase={2}mdb')

    template = env.get_template(
        'slapd.d/cn=config/olcDatabase={2}mdb/olcOverlay={0}memberof.ldif')
    template.stream(
        entry_uuid=uuid.uuid4(),
        time_short=cur_time.strftime(SHORT_TIME),
        time_long=cur_time.strftime(LONG_TIME),
    ).dump(os.path.join(db_dir, 'olcOverlay={0}memberof.ldif'))

    template = env.get_template(
        'slapd.d/cn=config/olcDatabase={2}mdb/olcOverlay={1}refint.ldif')
    template.stream(
        entry_uuid=uuid.uuid4(),
        time_short=cur_time.strftime(SHORT_TIME),
        time_long=cur_time.strftime(LONG_TIME),
        root_dn=kwargs['rootDN'],
        suffix=kwargs['suffix'],
    ).dump(os.path.join(db_dir, 'olcOverlay={1}refint.ldif'))

    template = env.get_template(
        'slapd.d/cn=config/olcDatabase={2}mdb/olcOverlay={2}ppolicy.ldif')
    template.stream(
        entry_uuid=uuid.uuid4(),
        time_short=cur_time.strftime(SHORT_TIME),
        time_long=cur_time.strftime(LONG_TIME),
        suffix=kwargs['suffix'],
    ).dump(os.path.join(db_dir, 'olcOverlay={2}ppolicy.ldif'))

    template = env.get_template(
        'slapd.d/cn=config/olcDatabase={2}mdb/olcOverlay={3}unique.ldif')
    rules = kwargs['unique']
    rules = [rule.format(suffix=kwargs['suffix'], base_ou=kwargs['baseOU'])
             for rule in rules]
    template.stream(
        entry_uuid=uuid.uuid4(),
        time_short=cur_time.strftime(SHORT_TIME),
        time_long=cur_time.strftime(LONG_TIME),
        rules=rules,
    ).dump(os.path.join(db_dir, 'olcOverlay={3}unique.ldif'))

    schema_dir = os.path.join(config_dir, 'cn=schema')
    for index, templ in enumerate(['core', 'cosine', 'inetorgperson',
                                   'ppolicy', 'rfc2307bis']):
        name = 'cn={{{index}}}{templ}.ldif'.format(index=index, templ=templ)
        template = env.get_template(
            'slapd.d/cn=config/cn=schema/{name}'.format(name=name))
        template.stream(
            entry_uuid=uuid.uuid4(),
            time_short=cur_time.strftime(SHORT_TIME),
            time_long=cur_time.strftime(LONG_TIME),
        ).dump(os.path.join(schema_dir, name))

    click.echo("Rendered templates")

    # Ewww, but needed
    for (root, _, filenames) in os.walk(tmpdir.name):
        for file in filenames:
            fname = os.path.join(root, file)
            crc = None
            data = None
            with open(fname, 'r') as f:
                data = f.read()
                crc = hex(zlib.crc32(str.encode(data)) & 0xffffffff)
            with open(fname, 'w') as f:
                f.write(
                    '# AUTO-GENERATED FILE - DO NOT EDIT!! Use ldapmodify.\n')
                f.write('# CRC32 {}\n'.format(crc.split('0x')[1]))
                f.write(data)

    click.echo("Written CRC to all files")
    shutil.rmtree(os.path.join(kwargs['output_dir'], 'slapd.d'),
                  ignore_errors=True)
    os.makedirs(kwargs['output_dir'], exist_ok=True)
    shutil.move(base_dir, kwargs['output_dir'])
    click.echo(
        "All done, result can be found in {}".format(kwargs['output_dir']))
