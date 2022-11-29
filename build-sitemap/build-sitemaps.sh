#!/bin/bash

set -e

mc config host add minio "http://${MINIO_SERVER_HOST}:${MINIO_SERVER_PORT_NUMBER}" "${MINIO_CLIENT_ACCESS_KEY}" "${MINIO_CLIENT_SECRET_KEY}"

# 'download' does not work for some reason, but 'public' permissions do
mc stat minio/sitemaps || mc mb minio/sitemaps
mc policy set public minio/sitemaps

# Build the BAS sitemap first
next="true"
cursor="null"

rm -f bas-sitemap.xml

# build the skeleton of the XML sitemap
printf '<?xml version="1.0" encoding="UTF-8"?>\n' >> bas-sitemap.xml
printf '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemalocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">' >> bas-sitemap.xml
while [ "$next" = "true" ]
do # A paged GraphQL query, against the datacite API. ror.org/01rhff309 is the Organization ID for BAS in DataCite's platform; we could use this to create other sitemaps this way too.
    results=$(curl -s 'https://api.datacite.org/graphql' \
        -H 'Accept-Encoding: gzip, deflate, br' \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json' \
        -H 'Connection: keep-alive' \
        -H 'DNT: 1' \
        -H 'Origin: https://api.datacite.org' \
        --compressed \
        --data-binary   "{\"query\":\"{\n  query: \n    organization(id: \\\"ror.org/01rhff309\\\") {\n      datasets(after: ${cursor}) {\n        totalCount\n        nodes {\n          id\n        }\n      pageInfo {\n        endCursor\n        hasNextPage\n      }\n      }\n    }\n  }\n\"}"

    )
    # Use jq to grab each DOI and output one line of a very basic sitemap
    line=$(echo $results | jq -rc '.. | .id? | select( . != null ) | "\t<url>\n\t\t<loc>\(.)</loc>\n\t</url>\n"')
    printf "%s" "${line}" >> bas-sitemap.xml
    # Get the cursor for the next page in the query, rinse, repeat
    cursor=$(echo $results | jq '.. | .endCursor? | select( . != null )' | sed s/\"/\\\\\"/g)
    next=$(echo $results | jq '.. | .hasNextPage? | select( . != null )')
done

printf "</urlset>" >> bas-sitemap.xml

mc cp bas-sitemap.xml minio/sitemaps/bas-sitemap.xml

# Build the GCMD sitemap next

python3 /usr/local/bin/index-gcmd.py

mc cp gcmd-sitemap.xml minio/sitemaps/gcmd-sitemap.xml

# Build the CCADI sitemap

rm -f ccadi-sitemap.xml

# build the skeleton of the XML sitemap
printf '<?xml version="1.0" encoding="UTF-8"?>\n' >> ccadi-sitemap.xml
printf '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemalocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">' >> ccadi-sitemap.xml
for i in http://hedeby.uwaterloo.ca/api/metadata?page={0..150}
    do printf "<url><loc>${i}</loc></url>" >> ccadi-sitemap.xml
done

printf "</urlset>" >> ccadi-sitemap.xml

mc cp ccadi-sitemap.xml minio/sitemaps/ccadi-sitemap.xml
