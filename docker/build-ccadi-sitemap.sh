#!/bin/bash

set -e

# 'download' does not work for some reason, but 'public' permissions do
mc stat minio/sitemaps || mc mb minio/sitemaps
mc policy set public minio/sitemaps

rm -f ccadi-sitemap.xml

# build the skeleton of the XML sitemap
printf '<?xml version="1.0" encoding="UTF-8"?>\n' >> ccadi-sitemap.xml
printf '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemalocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">' >> bas-sitemap.xml
for i in http://hedeby.uwaterloo.ca/api/metadata?page={0..150}
    do printf "<url><loc>${i}</loc></url>" >> ccadi-sitemap.xml
done

printf "</urlset>" >> ccadi-sitemap.xml

mc cp ccadi-sitemap.xml minio/sitemaps/ccadi-sitemap.xml
