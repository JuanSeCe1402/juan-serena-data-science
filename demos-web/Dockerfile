FROM caddy:2-alpine

ENV PORT=8080 \
    XDG_DATA_HOME=/tmp/caddy-data \
    XDG_CONFIG_HOME=/tmp/caddy-config

COPY Caddyfile /etc/caddy/Caddyfile
COPY dist/ /srv/

RUN caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

USER 1000:1000
EXPOSE 8080
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
