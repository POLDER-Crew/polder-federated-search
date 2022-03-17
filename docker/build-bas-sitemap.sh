set -e

mc policy set public minio/sitemaps/bas-sitemap.xml

next="true"
cursor="null"

rm -f bas-sitemap.xml

printf '<?xml version="1.0" encoding="UTF-8"?>\n' >> bas-sitemap.xml
printf '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' >> bas-sitemap.xml

while [ "$next" = "true" ]
do
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
    line=$(echo $results | jq -rc '.. | .id? | select( . != null ) | "<loc><url>\(.)</url></loc>"')
    printf "%s" "${line}" >> bas-sitemap.xml
    cursor=$(echo $results | jq '.. | .endCursor? | select( . != null )' | sed s/\"/\\\\\"/g)
    next=$(echo $results | jq '.. | .hasNextPage? | select( . != null )')
done

printf "</urlset>" >> bas-sitemap.xml

mc cp bas-sitemap.xml minio/sitemaps/bas-sitemap.xml
