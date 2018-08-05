# slapddgen

* [slapddgen](#slapddgen)
    * [Layout](#layout)
    * [Notes](#notes)

**NOTE**: This tool is very very alpha. Works for me, might work for you.

**NOTE**: Ensure your editor does not strip trailing whitespace if you
open any of the files in `cn=schema` as that will break the ldif format.

`slapddgen` generates a `slapd.d` that you can load into an OpenLDAP
server by pointing at it with `slapd -F`. This will start a server
with online configuration, aka `olc`, meaning the configuration
itself is stored in the directory server, not in `slapd.conf`.

The input for this tool is contained in `config.json`, or whatever
`--config_file` is pointed at. There's too many things to do this
with environment variables or CLI switches. Removing things from
`config.json` is guaranteed to blow shit up, though for the modules,
ACLs, indices and unique empty arrays should be fine.

## Layout

The configuration that gets generated assumes the data in the
directory server will be layed yout like this:

```text
- {{suffix}}
--- {{baseOU}},{{suffix}}
----- ou=accounts,{{baseOU}},{{suffix}}
----- ou=groups,{{baseOU}},{{suffix}}
----- ou=policy,{{baseOU}},{{suffix}}
```

It also assumes there will be a `cn=admin,{{suffix}}` entity of
the `organizationalRole` type who's member attribute will include
the DN of anyone with full administrative access to the server.

The `suffix` should be self-explanatory but the `baseOU` typically
raises some eyebrows. It's there to facilitate merging multiple
LDAP environments later on (say merging two environments after
an acquisition) and also allows for easy experimentation under a
different base OU without being affected by the ACLs currently
in place or risking affecting those ACLs.

## Notes

The defaults target an OpenLDAP server running on Alpine, so you might
have to adjust the paths in the `ldap` section of `config.json`.

It uses the RFC2307bis schema, this is not configurable.
As such `posixGroup` is no longer structural and if you need something
to just be a `posixGroup` you'll have to combine it with another
object class. `organizationalRole` is a decent candidate as it only
requires the `cn` attribute. In most cases you'll probably want to
combine a `posixGroup` with a `groupOfNames` and use the `member`
attribute with DNs instead of `memberUid` so that the referential
integrity overlay can do its thing for you.

It does not load any data for you, but sets up a few useful defaults
and configuration of some initial ACLs, the mdb database backend and
a few of the overlays. The result should be an OpenLDAP server with
a sensible base configuration that you can then go and tweak.

Note that once the configuration is generated you should not edit
the files by hand (or if you do, update the `# CRC32` preamble).
Instead, once loaded into the server you can use `ldapmodify` to
update the configuration.

The tool will always generate a configuration that uses CRYPT
with SHA-512 and 50.000 rounds for the passwords. Though
the format is configurable using `ldap.saltFormat` the use of
CRYPT is not. This means that the configuration generated will
not work on Windows machines where CRYPT is not available.

You can generate a hash with `slappasswd -h '{CRYPT}' -c '$6$rounds=50000$%.16s'`
for the `rootPW`. If `rootPW` starts with `{CRYPT}` it'll be put
into the generated configuration as such, if not it's assumed it's
plain text and slapddgen will create a proper hash for it. The
configuration additionally sets up the server in such a way that
any time a plain text password is submitted to it, it will be hashed
before it is actually stored.

The configuration does not include options for TLS, because
these vary (unhelpfully) based on what TLS library the server was
built with (GnuTLS vs Mozila NSS vs OpenSSL and derivatives). For
those refer to `man slapd-config` and use `ldapmodify` to update
the server after it's been started.
