next="true"
cursor="null"

while [ "$next" = "true" ]
do
    results=$(curl -s 'https://api.datacite.org/graphql' \
        -H 'Accept-Encoding: gzip, deflate, br' \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json' \
        -H 'Connection: keep-alive' \
        -H 'DNT: 1' \
        -H 'Origin: https://api.datacite.org' \
        --data-binary '{"query":"{\n  query: \n    organization(id: \"ror.org/01rhff309\")' \
         "{\n      datasets(after: ${cursor}) {\n        totalCount\n        nodes {\n          id\n        }\n" \
        'pageInfo {\n        endCursor\n\n        hasNextPage\n      }\n      }\n    }\n  }\n"}' \
        --compressed
        )
    urls=$(echo jq -r '.. | .id? | select( . != null )' $results )
    cursor=$(echo $results | jq '.. | .endCursor? | select( . != null )')
    next=$(echo $results | jq '.. | .hasNextPage? | select( . != null )')

    echo $urls
done
