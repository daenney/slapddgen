FROM alpine:3.8
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.name="ldap-server"
LABEL org.label-schema.description="OpenLDAP server configured for example.com"
LABEL org.label-schema.vcs-url="https://git.example.com/ldap"
LABEL org.label-schema.vendor="example.com"
LABEL maintainer="test@example.com"

ARG BUILD_DATE
ARG VERSION
ARG COMMIT
ARG UID=55555

LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.version=$VERSION
LABEL org.label-schema.vcs-ref=$COMMIT

RUN addgroup -g $UID -S ldapd && \
    adduser -u $UID -S ldapd -G ldapd

RUN apk add --no-cache openldap \
                       openldap-back-mdb \
                       openldap-back-monitor \
                       openldap-overlay-accesslog \
                       openldap-overlay-auditlog \
                       openldap-overlay-constraint \
                       openldap-overlay-dds \
                       openldap-overlay-deref \
                       openldap-overlay-dynlist \
                       openldap-overlay-memberof \
                       openldap-overlay-ppolicy \
                       openldap-overlay-refint \
                       openldap-overlay-unique \
                       ca-certificates && \
    rm /etc/openldap/ldap.conf /etc/openldap/slapd.conf /etc/openldap/slapd.ldif && \
    rm -rf /etc/openldap/schema && \
    rm /etc/openldap/DB_CONFIG.example && \
    rm /var/lib/openldap/openldap-data/DB_CONFIG.example && \
    mkdir /var/run/openldap && \
    chown ldapd:ldapd /run/openldap && \
    chown -R ldapd:ldapd /var/lib/openldap && \
    mkdir /etc/openldap/slapd.d

COPY config /etc/openldap
RUN chown -R ldapd:ldapd /etc/openldap/slapd.d

ENTRYPOINT ["/usr/sbin/slapd", "-u", "ldapd", "-g", "ldapd", "-d", "256", "-h", "ldap:// ldaps:/// ldapi://%2fvar%2frun%2fopenldap%2fslapd.sock"]
