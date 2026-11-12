# Official PHP linux/amd64 manifest resolved on 7 November 2026.
FROM php:8.3-apache@sha256:8732e645530351f2f16aa7dd7619a44dad614bcfde6b4eb994f9a228d24f9b98
WORKDIR /opt/shop
COPY vendor/src/ ./src/
COPY vendor/LICENSE.cutover vendor/source.json ./provenance/
COPY lab/ ./lab/
RUN php -r 'if (!extension_loaded("curl")) { fwrite(STDERR, "PHP curl extension missing\n"); exit(1); }' \
    && (find src lab -name '*.php' -print0 | xargs -0 -n 1 php -l) \
    && mkdir -p src/data \
    && chown www-data:www-data src/data
USER www-data
EXPOSE 8080
CMD ["php", "-S", "0.0.0.0:8080", "-t", "/opt/shop/src", "/opt/shop/lab/router.php"]
