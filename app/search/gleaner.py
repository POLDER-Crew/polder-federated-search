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

                SELECT
                    (MAX(?relevance) AS ?score)
                    ?id
                    ?url
                    ?sameAs
                    ?title
                    ?abstract
                    (GROUP_CONCAT(DISTINCT ?keyword ; separator=", ") as ?keywords)
                    (GROUP_CONCAT(DISTINCT ?temporal_cov ; separator=", ") as ?temporal_coverage)

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

                  ?lit bds:search "{text}" .
                  ?lit bds:matchAllTerms "false" .
                  ?lit bds:relevance ?relevance .
                  ?s ?p ?lit .

                  graph ?g {{
                    ?s ?ids ?id .
                    ?s ?urls ?url .
                    ?s ?titles ?title .
                    Optional {{
                        ?s ?abstracts ?abstract .
                        ?s ?keys ?keyword .
                        ?s ?sameAsVals ?sameAs .
                        ?s ?temporal ?temporal_cov .
                    }}
                  }}

                }}
                GROUP BY ?id ?url ?sameAs ?title ?abstract
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

    def temporal_search(self, start=None, end=None):
        self.sparql.setQuery(
            f"""
                PREFIX sschema: <https://schema.org/>
                PREFIX schema: <http://schema.org/>

                SELECT
                    ?id
                    ?url
                    ?sameAs
                    ?title
                    ?abstract
                    (GROUP_CONCAT(DISTINCT ?keyword ; separator=", ") as ?keywords)
                    (GROUP_CONCAT(DISTINCT ?temporal_cov ; separator=", ") as ?temporal_coverage)
                    ?start_date
                    ?end_date

                    {{

                        VALUES ?type {{ schema:Dataset sschema:Dataset }}
                        VALUES ?ids {{ schema:identifier sschema:identifier }}
                        VALUES ?urls {{ sschema:url schema:url }}
                        VALUES ?titles {{ sschema:name schema:name }}
                        VALUES ?abstracts {{ sschema:description schema:description }}
                        VALUES ?keys {{ sschema:keywords schema:keywords }}
                        VALUES ?sameAsVals {{ sschema:sameAs schema:sameAs }}
                        VALUES ?temporal {{ sschema:temporalCoverage schema:temporalCoverage }}

                        bind(
                            if(
                                contains(?temporal_cov, "/"),
                                xsd:date(strbefore(?temporal_cov, "/")),
                                if(
                                    contains(?temporal_cov, " - "),
                                    xsd:date(strbefore(?temporal_cov, " - ")),
                                    ?temporal_cov
                                )
                            )
                          as ?start_date
                        )

                        bind(
                            if(
                                contains(?temporal_cov, "/"),
                                strafter(?temporal_cov, "/"),
                                if(
                                    contains(?temporal_cov, " - "),
                                    strafter(?temporal_cov, " - "),
                                    ?temporal_cov
                                )
                            )
                          as ?end_date
                        )


                          ?s a ?type .

                          ?s ?ids ?id .
                          ?s ?urls ?url .
                          ?s ?temporal ?temporal_cov .
                          ?s ?titles ?title .
                          Optional {{
                            ?s ?abstracts ?abstract .
                            ?s ?keys ?keyword .
                            ?s ?sameAsVals ?sameAs .
                          }}
                    }}

                }}
            GROUP BY ?id ?url ?sameAs ?title ?abstract ?start_date ?end_date
            OFFSET 0
            LIMIT {self.PAGE_SIZE}
        """
    )

    def convert_result(self, sparql_result_dict):
        result = {}
        for k, v in sparql_result_dict.items():
            result[k] = v['value']
        result['urls'] = []
        url = result.pop('url', None)
        sameAs = result.pop('sameAs', None)
        if url is not None:
            result['urls'].append(url)
        if sameAs is not None:
            result['urls'].append(sameAs)
        keywords = result.pop('keywords', '')
        result['keywords'] = keywords.split(',')
        result['source'] = "Gleaner"
        return SearchResult(**result)
