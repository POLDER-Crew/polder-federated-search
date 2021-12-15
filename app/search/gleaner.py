from SPARQLWrapper import SPARQLWrapper, JSON
from .search import SearcherBase, SearchResultSet


def convert_result(sparql_result_dict):
    result = {}
    for k, v in sparql_result_dict.items():
        result[k] = v['value']
    return result


class GleanerSearch(SearcherBase):

    def __init__(self, **kwargs):
        ENDPOINT_URL = kwargs.pop('endpoint_url')
        self.sparql = SPARQLWrapper(ENDPOINT_URL)

    def text_search(self, **kwargs):
        # todo: filter these so we just get whole URLS: OPTIONAL {{ ?s schema:identifier / schema:value ?identifier_url . }}
        text = kwargs.pop('q', '')

        self.sparql.setQuery(
            f"""
            PREFIX sschema: <https://schema.org/>
            PREFIX schema: <http://schema.org/>

            SELECT DISTINCT ?score ?abstract ?title ?url ?sameAs ?boundingbox ?temporalCoverage ?identifier
            {{
               {{
                   BIND(schema:Dataset AS ?type)
                   ?s a ?o
                   FILTER(?o=?type)
                }} UNION {{
                   BIND(sschema:Dataset AS ?type)
                   ?s a ?o
                   FILTER(?o=?type)
                }}
               ?lit bds:search "{text}" .
               ?lit bds:matchAllTerms "false" .
               ?lit bds:relevance ?score .
               ?s ?p ?lit .

               graph ?g {{
                ?s ?p ?lit .
                OPTIONAL {{ ?s schema:name ?title .   }}
                OPTIONAL {{ ?s schema:url ?url .   }}
                OPTIONAL {{ ?s schema:description ?abstract .    }}
                OPTIONAL {{ ?s schema:spatialCoverage/schema:geo/schema:box ?boundingbox . }}
                OPTIONAL {{ ?s schema:temporalCoverage ?temporalCoverage . }}
                OPTIONAL {{ ?s schema:identifier ?identifier . }}
                OPTIONAL {{ ?s schema:sameAs ?sameAs . }}
              }}
            }}
            ORDER BY DESC(?score)
            OFFSET 0
            LIMIT {self.PAGE_SIZE}
        """
        )
        self.sparql.setReturnFormat(JSON)
        data = self.sparql.query().convert()
        result_set = SearchResultSet(
            total_results=len(data['results']['bindings']),
            page_start=0,  # for now
            results=list(map(convert_result, data['results']['bindings']))
        )
        return result_set
