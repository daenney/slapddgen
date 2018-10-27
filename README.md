# slapddgen

* [slapddgen](#slapddgen)
    * [Usage](#usage)
    * [Modifying the templates](#modifying-the-templates)
    * [Docker](#docker)
        * [Building](#building)
        * [Running](#running)
            * [Production](#production)
    * [Configuration](#configuration)
        * [`cn=config.ldif`](#cnconfigldif)
        * [`cn=module{0}.ldif,cn=config`](#cnmodule0ldifcnconfig)
        * [`olcDatabase={-1}frontend.ldif,cn=config`](#olcdatabase-1frontendldifcnconfig)
        * [`olcDatabase={0}config.ldif,cn=config`](#olcdatabase0configldifcnconfig)
        * [`olcDatabase={1}monitor.ldif,cn=config`](#olcdatabase1monitorldifcnconfig)
        * [`olcDatabase={2}mdb.ldif,cn=config`](#olcdatabase2mdbldifcnconfig)
        * [`olcOverlay={0}memberof.ldif,olcDatabase={2}mdb,cn=config`](#olcoverlay0memberofldifolcdatabase2mdbcnconfig)
        * [`olcOverlay={1}refint.ldif,olcDatabase={2}mdb,cn=config`](#olcoverlay1refintldifolcdatabase2mdbcnconfig)
        * [`olcOverlay={2}ppolicy.ldif,olcDatabase={2}mdb,cn=config`](#olcoverlay2ppolicyldifolcdatabase2mdbcnconfig)
        * [`olcOverlay={3}unique.ldif,olcDatabase={2}mdb,cn=config`](#olcoverlay3uniqueldifolcdatabase2mdbcnconfig)
        * [`cn=schema.ldif,cn=config`](#cnschemaldifcnconfig)
        * [`cn=*.ldif,cn=schema,cn=config`](#cnldifcnschemacnconfig)

**NOTE**: This tool is very very alpha. Works for me, might work for you.

**NOTE**: Ensure your editor does not strip trailing whitespace if you
open any of the files in `cn=schema` as that will break the ldif format.

`slapddgen` generates a `slapd.d` that you can load into an OpenLDAP
server by pointing at it with `slapd -F`. This will start a server
with online configuration, aka `olc`, meaning the configuration
itself is stored in the directory server, not in `slapd.conf`.

## Usage

The input for this tool is contained in `config.json`, or whatever
`--config_file` is pointed at. There's too many things to do this
with environment variables or CLI switches. Removing things from
`config.json` is guaranteed to blow shit up, though for the modules,
ACLs, indices and unique empty arrays should be fine.

Once you've installed slapddgen you can run it with a `slapddgen generate
--config_file=/path/to/config.json --output_dir=/path/to/write/config/to`

## Modifying the templates

If you know what you're doing you can modify the templates in
`templates/slapd.d` to suit your needs. Doing so if you've `pip install`ed
slapddgen will be annoying, so in that case cloning the repository and
doing a `pip install -e .` instead will be more helpful.

## Docker

There is also an example `Dockerfile` that you can use to package
it all up in a Docker container. This can be useful for testing purposes
amongst other things.

### Building

```sh
VERSION=$(git rev-parse --abbrev-ref HEAD)
docker build --no-cache=true \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg COMMIT=$(git rev-parse HEAD) \
    --build-arg VERSION=${VERSION} \
    -t ldap:${VERSION} .
```

When building a release use `git describe --abbrev=0 --tags` instead
for the `VERSION`.

### Running

```sh
docker run -it -p 3389:389 -p 6636:636 ldap
```

This will expose port 389 in the container, the `ldap://` URL, to the host
on port 3389 (so you don't need to bind on a priviledged port) and do the
same for port 636, `ldaps://`.

You can change the entrypoint with `--entrypoint=/bin/sh`. Once you've done
that you can still manually launch OpenLDAP in the container by running
`slapd -u ldap -g ldap -d 256`.

#### Production

When running it for production purposes it's important to ensure
configuration and data can persist to disk. Otherwise you'd start up with a
fresh and empty directory service every time your restart the container.

To that end, you should probably volume mount the following:

* Configuration: `/etc/openldap`
* Database: `/var/lib/openldap/openldap-data`

A separate user, `ldapd` is create which defaults to a UID of `55555`. This
is to ensure you can correctly map a host user and the container user so you don't
get into permission issues with the volume mounts.

In order to change the UID of the `ldapd` user in the container you have to
rebuild it and pass in `--build-arg UID=<number>`.

## Configuration

slapddgen generates a bunch of configuration for you and assumes the following
DIT layout:

```text
- {{suffix}}
--- {{baseOU}},{{suffix}}
----- ou=accounts,{{baseOU}},{{suffix}}
----- ou=groups,{{baseOU}},{{suffix}}
----- ou=policy,{{baseOU}},{{suffix}}
```

You can of course change this yourself by modifying the templates.

The configuration generated uses online/dynamic configuration, aka olc, aka
`olcConfig`. As such there is no `slapd.conf` to speak of and you'll have to
apply ldif's with the help of `ldapmodify` to configure the OpenLDAP server
further.

The resulting `slapd.d` directory can be used to start an OpenLDAP server
from scratch. The following sections assume that you've run slapddgen and
explain some of the things in the generated configuration.

### `cn=config.ldif`

The following settings are defaults related to Alpine:

```ldif
olcConfigFile: /etc/openldap/slapd.conf
olcConfigDir: /etc/openldap/slapd.d/
olcArgsFile: /run/openldap/slapd.args
olcPidFile: /run/openldap/slapd.pid
```

Of note is:

```ldif
olcPasswordCryptSaltFormat: $6$rounds=50000$%.16s
```

This uses crypt's SHA512 with 50.000 rounds (key stretching). This relates to
the `olcPasswordHash` setting in `olcDatabase={-1}frontend.ldif` as well as
`olcPPolicyHashCleartext` in `olcOverlay={2}ppolicy.ldif,olcDatabase={2}mdb,cn=config`.

### `cn=module{0}.ldif,cn=config`

Configures which modules are loaded. Of note are `olcModulePath` and the
multitude of `olcModuleLoad` entries, relative to `olcModulePath`.

### `olcDatabase={-1}frontend.ldif,cn=config`

The frontend database is a special, pseudo, database which contains settings
that apply as defaults to all the other `olcDatabase`s.

The two interesting entries are:

```ldif
olcMonitoring: FALSE
olcPasswordHash: {CRYPT}
```

`olcMontioring` disables the monitoring overlay for all databases. It'll be
enabled explicitly for `olcDatabase={2}mdb.ldif`. The other ensures that we
always use `{CRYPT}` as our password hashing mechanism. Which settings are
applied to password hashing is defined by `olcPasswordCryptSaltFormat`.

### `olcDatabase={0}config.ldif,cn=config`

The only thing of interest here are the `olcAccess` entries, defining the
ACLs which allow entities to read/write `cn=config`.

### `olcDatabase={1}monitor.ldif,cn=config`

Like the previous section, `olcAccess` is the only interesting bit.

### `olcDatabase={2}mdb.ldif,cn=config`

This one is interesting, as this defines the data storage of our actual
entries in the DIT, as well as other things like ACLs.

Of interest:

```ldif
olcSuffix: dc=example,dc=com
olcRootDN: cn=Manager,dc=example,dc=com
olcRootPW: {CRYPT}super-long-hash
olcMonitoring: TRUE
olcDbMaxSize: 536870912
olcDbDirectory: /var/lib/openldap/openldap-data
olcDbIndex: objectClass eq
olcDbIndex: uid eq,sub
olcDbIndex: uidNumber eq
olcDbIndex: gidNumber eq
olcDbIndex: member eq
olcDbIndex: memberof eq
```

`olcSuffix` defines the default suffix for all entries. `olcRootDN` is the
DN of this database "root" user, and can modify anything regardless of ACLs.
The `olcRootPW` is the password of the `olcRootDN`, generated with
`slappasswd -h '{CRYPT}' -c '$6$rounds=50000$%.16s'`.

`olcMonitoring` enables monitoring for this database and `olcDbDirectory`
contains the path on disk where this database is stored.

The `olcDbIndex` entries define the indices OpenLDAP will maintain for us
and help speed up search operations.

`olcDbMaxSize` defines the size of the memory map that will be allocated
for the database. It cannot grow past this value at runtime though you
can set it to a higher value and then restart. The value is in bytes,
our default is half a gibibyte (GiB).

As usual there's also a number of `olcAccess` entries governing access to
the data.

### `olcOverlay={0}memberof.ldif,olcDatabase={2}mdb,cn=config`

Here we store the configuration for the memberof overlay. The memberof
overlay adds a virtual attribute `memberOf` to any entry in the DIT storing
what things this DN is a member of.

Imagine you have three `groupOfNames` that refer to a user in the `member`
attribute. The `memberOf` attribute for that user will then contain the
DNs of these three `groupOfNames`. Note that `memberOf` will only contain
the immediate/direct memberships, not any inherited ones (it will
not recursively expand the member attributes).

The settings of interest are:

```ldif
olcMemberOfDangling: error
olcMemberOfDanglingError: constraintViolation
olcMemberOfRefInt: TRUE
olcMemberOfGroupOC: groupOfNames
olcMemberOfMemberAD: member
olcMemberOfMemberOfAD: memberOf
```

`olcMemberOfDangling` specifies that we'll return an error in case a
modification would result in a dangling reference, returning an error of
type `olcMemberOfDanglingError`.

`olcMemberOfRefInt` specifies that we use the referential integrity
overlay (see the next section).

`olcMemberOfGroupOC` specifies which `objectClass` we monitor for
dangling references. This is usually only useful for gorups and we use
`groupOfNames` for groups. `olcMemberOfAD` specifies the attribute used
to store members of a group in, that's `member` and `olcMemberOfMemberOfAD`
specifes the attribute in which the relation is stored, `memberOf`.

### `olcOverlay={1}refint.ldif,olcDatabase={2}mdb,cn=config`

This configures the referential integrity overlay. Referential integrity
will take care of updating any references to a DN stored in the specified
attributes should that DN get renamed/moved.

Of note:

```ldif
olcRefintAttribute: owner
olcRefintAttribute: manager
olcRefintAttribute: memberOf
olcRefintAttribute: member
olcRefintAttribute: roleOccupant
olcRefintModifiersName: cn=Manager,dc=example,dc=com
```

The `olcRefintAttribute`s specify which attributes we want to enforce
referential integrity for. This can only every be attributes that store
a distinguished name.

`olcRefintModifiersName` specifes what we'll store in the `modifiersName`
operational attribute for any entry that gets updated by the referential
integrity overlay.

### `olcOverlay={2}ppolicy.ldif,olcDatabase={2}mdb,cn=config`

The password policy overlay allows to configure certain minimum
requirements for passwords (like those stored in the `userPassword`
attribute).

Of note:

```ldif
olcPPolicyHashCleartext: TRUE
olcPPolicyDefault: cn=password,ou=policy,dc=example,dc=com
olcPPolicyUseLockout: FALSE
```

`olcPPolicyHashCleartext` means that the server will automatically hash
any password sent in as clear text using `olcPasswordHash`.

`olcPPolicyDefault` defines an entry in the DIT where we store our
default password policy on which we can set other settings. The entry
should have `objectClass: pwdPolicy`. Its settings [are documented
here](http://www.zytrax.com/books/ldap/ch6/ppolicy.html#pwdpolicyattributes).

You can create additional/different password policies in the `ou=policy`
part of the tree and attach them to a user by adding the `pwdPolicySubentry`
attribute on them, pointing to a different policy.

`olcPPolicyUseLockout` instructs the server whether it should return an
`InvalidCredentials` (`FALSE`) when attempting to bind or an `AccountLocked`
(`TRUE`) instead. This configuration defaults to `FALSE` in order to not be
able to use this feature to enumerate accounts.

### `olcOverlay={3}unique.ldif,olcDatabase={2}mdb,cn=config`

The unique overlay allows enforcing uniqueness contraints of attributes on
a part of the tree (or the whole tree). Though the RDN is always enforced to
be unique (so you can't have two people with the same `uid` for example)
other attributes are not, most crucially things like `uidNumber`, `gidNumber`
or `homeDirectory`.

You can create constraints by adding an `olcUniqueURI` entry of the form:
`ldap:///[base dn]?[attributes...]?scope[?filter]`.

For example, if you wanted to enforce unique `gidNumber`s you could do:
`ldap:///?gidNumber?sub`. Unfortunately this will enforce `gidNumber`
constraints across both `posixAccount` and `posixGroup` so you won't be
able to create a `posixAccount` with `gidNumber` set to a `posixGroup`s
GID, which is undesirable. Instead do something like this:

```ldif
olcUniqueURI: ldap:///ou=groups,ou=example,dc=example,dc=com?gidNumber?sub
olcUniqueURI: ldap:///ou=accounts,ou=example,dc=example,dc=com?gidNumber?sub
olcUniqueURI: ldap:///ou=example,dc=example,dc=com?uidNumber?sub
```

Now the constraint will be enforced independently on these parts of the
tree, not as a whole.

### `cn=schema.ldif,cn=config`

Nothing of relevance to see or change here. It just needs to exist. Once
the server has been started this entry will be updated automatically
with the server's internal object classes and attributes (mostly all the
`olc`* object classes and attributes).

### `cn=*.ldif,cn=schema,cn=config`

Contains the schema files loaded by the server.

Updating this is rather tricky. The "easiest" way is to generate a `slapd.conf`
with the `include` statements for the schemas and then dump it out
using `slapdest -f /path/to/slapd.conf -F /path/to/slapd.d`.
