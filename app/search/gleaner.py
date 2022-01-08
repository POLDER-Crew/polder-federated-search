from SPARQLWrapper import SPARQLWrapper, JSON
from .search import SearcherBase, SearchResultSet, SearchResult


class GleanerSearch(SearcherBase):

    def __init__(self, **kwargs):
        ENDPOINT_URL = kwargs.pop('endpoint_url')
        self.sparql = SPARQLWrapper(ENDPOINT_URL)

    def text_search(self, text=None):
        self.sparql.setQuery(
            f"""
            PREFIX sschema: <https://schema.org/>
            PREFIX schema: <http://schema.org/>

            SELECT DISTINCT ?score ?lit ?id ?url ?sameAs ?title ?abstract ?keywords ?temporal_coverage

            {{
              VALUES ?type {{ schema:Dataset sschema:Dataset }}
              VALUES ?ids {{ schema:identifier sschema:identifier }}
              VALUES ?urls {{ sschema:url schema:url }}
              VALUES ?titles {{ sschema:name schema:name }}
              VALUES ?abstracts {{ sschema:description schema:description }}
              VALUES ?keys {{ sschema:keywords schema:keywords }}
              VALUES ?sameAsVals {{ sschema:sameAs schema:sameAs }}
              VALUES ?temporal {{ sschema:temporalCoverage schema:temporalCoverage }}

              ?s a ?type .

              ?lit bds:search "Greenland" .
              ?lit bds:matchAllTerms "false" .
              ?lit bds:relevance ?score .
              ?s ?p ?lit .

              graph ?g {{
                ?s ?ids ?id .
                ?s ?p ?lit .
                ?s ?urls ?url .
                ?s ?titles ?title .
                Optional {{
                    ?s ?abstracts ?abstract .
                    ?s ?keys ?keywords .
                    ?s ?sameAsVals ?sameAs .
                    ?s ?temporal ?temporal_coverage .
                }}
              }}

            }}

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
