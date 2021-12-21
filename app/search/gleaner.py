from SPARQLWrapper import SPARQLWrapper, JSON
from .search import SearcherBase, SearchResultSet, SearchResult


class GleanerSearch(SearcherBase):

    def __init__(self, **kwargs):
        ENDPOINT_URL = kwargs.pop('endpoint_url')
        self.sparql = SPARQLWrapper(ENDPOINT_URL)

    def text_search(self, text=None):
        # todo: filter these so we just get whole URLS: OPTIONAL {{ ?s schema:identifier / schema:value ?identifier_url . }}
        self.sparql.setQuery(
            f"""
            PREFIX sschema: <https://schema.org/>
            PREFIX schema: <http://schema.org/>

            SELECT ?id
            (SAMPLE(?score) AS ?score)
            (SAMPLE(?abstract) AS ?abstract)
            (SAMPLE(?title) AS ?title)
            (SAMPLE(?url) AS ?url)
            (SAMPLE(?sameAs) AS ?sameAs)
            (SAMPLE(?spatial_coverage) AS ?spatial_coverage)
            (SAMPLE(?temporal_coverage) AS ?temporal_coverage)
            {{
               {{
                   BIND(schema:Dataset AS ?type)
                   ?s a ?o
                   FILTER(?o=?type)
                }} UNION {{
                   BIND(sschema:Dataset AS ?stype)
                   ?s a ?o
                   FILTER(?o=?stype)
                }}
               ?lit bds:search "{text}" .
               ?lit bds:matchAllTerms "false" .
               ?lit bds:relevance ?score .
               ?s ?p ?lit .

               graph ?g {{
                ?s schema:identifier ?id .
                OPTIONAL {{ ?s schema:name ?title .   }}
                OPTIONAL {{ ?s schema:url ?url .   }}
                OPTIONAL {{ ?s schema:description ?abstract .    }}
                OPTIONAL {{ ?s schema:spatialCoverage/schema:geo/schema:box ?spatial_coverage . }}
                OPTIONAL {{ ?s schema:temporalCoverage ?temporal_coverage . }}
                OPTIONAL {{ ?s schema:sameAs ?sameAs . }}
              }}
            }}
            GROUP BY ?id
            ORDER BY DESC(?score)
            OFFSET 0
            LIMIT {self.PAGE_SIZE}
        """
        )
        # a note: BlazeGraph relevance scores go from 0.0 to 1.0; all results are normalized.

        self.sparql.setReturnFormat(JSON)
        data = self.sparql.query().convert()
        result_set = SearchResultSet(
            total_results=len(data['results']['bindings']),
            page_start=0,  # for now
            results=self.convert_results(data['results']['bindings'])
        )
        return result_set

    def convert_result(self, sparql_result_dict):
        result = {}
        for k, v in sparql_result_dict.items():
            result[k] = v['value']
        result['urls'] = [result.pop('url', None), result.pop('sameAs', None)]
        result['source'] = "Gleaner"
        return SearchResult(**result)
