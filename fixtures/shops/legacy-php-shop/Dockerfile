# Copies the vendored legacy shop (unmodified) into the official PHP + Apache image.
FROM php:8.3-apache
COPY src/ /var/www/html/
RUN mkdir -p /var/www/html/data && chown -R www-data:www-data /var/www/html/data
