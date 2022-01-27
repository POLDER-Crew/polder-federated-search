from SPARQLWrapper import SPARQLWrapper, JSON
from .search import SearcherBase, SearchResultSet, SearchResult


class GleanerSearch(SearcherBase):
    @staticmethod
    def build_query(user_query=""):
        return f"""
            PREFIX sschema: <https://schema.org/>
            PREFIX schema: <http://schema.org/>

            SELECT
                (MAX(?relevance) AS ?score)
                ?id
                ?url
                ?title
                (GROUP_CONCAT(DISTINCT ?abstract ; separator=", ") as ?abstract)
                (GROUP_CONCAT(DISTINCT ?sameAs ; separator=", ") as ?sameAs)
                (GROUP_CONCAT(DISTINCT ?keywords ; separator=", ") as ?keywords)
                (GROUP_CONCAT(DISTINCT ?temporal_coverage ; separator=", ") as ?temporal_coverage)

            {{
                VALUES ?type {{ schema:Dataset sschema:Dataset }}
                VALUES ?ids {{ schema:identifier sschema:identifier }}
                VALUES ?urls {{ sschema:url schema:url }}
                VALUES ?titles {{ sschema:name schema:name }}
                VALUES ?abstracts {{ sschema:description schema:description }}
                VALUES ?keys {{ sschema:keywords schema:keywords }}
                VALUES ?sameAsVals {{ sschema:sameAs schema:sameAs }}
                VALUES ?temporal {{ sschema:temporalCoverage schema:temporalCoverage }}

                BIND(
                    IF(
                        CONTAINS(?temporal_cov, "/"),
                        STRDT(STRBEFORE(?temporal_cov, "/"), xsd:date),
                        IF(
                            CONTAINS(?temporal_cov, " - "),
                            STRDT(STRBEFORE(?temporal_cov, " - "), xsd:date),
                            ?temporal_cov
                        )
                    )
                  AS ?start_date
                )

                BIND(
                    IF(
                        CONTAINS(?temporal_cov, "/"),
                        STRDT(STRAFTER(?temporal_cov, "/"), xsd:date),
                        IF(
                            CONTAINS(?temporal_cov, " - "),
                            STRDT(STRAFTER(?temporal_cov, " - "), xsd:date),
                            ?temporal_cov
                        )
                    )
                  AS ?end_date
                )

                ?s a ?type .

                {user_query}

                ?s ?ids ?id .
                ?s ?urls ?url .
                ?s ?titles ?title .
                OPTIONAL {{
                    ?s ?abstracts ?abstract .
                    ?s ?keys ?keyword .
                    ?s ?sameAsVals ?sameAs .
                    ?s ?temporal ?temporal_cov .
                }}

            }}
            GROUP BY ?id ?url ?title
            ORDER BY DESC(?score)
            OFFSET 0
            LIMIT {GleanerSearch.PAGE_SIZE}
        """

    def __init__(self, **kwargs):
        ENDPOINT_URL = kwargs.pop('endpoint_url')
        self.sparql = SPARQLWrapper(ENDPOINT_URL)

    def text_search(self, text=None):
        user_query = f"""
            ?lit bds:search "{text}" .
            ?lit bds:matchAllTerms "false" .
            ?lit bds:relevance ?relevance .
            ?s ?p ?lit .
        """

        # Assigning this to a class member makes it easier to test
        self.query = GleanerSearch.build_query(user_query)
        self.sparql.setQuery(self.query)

        # a note: BlazeGraph relevance scores go from 0.0 to 1.0; all results are normalized.
        self.sparql.setReturnFormat(JSON)
        data = self.sparql.query().convert()
        result_set = SearchResultSet(
            total_results=len(data['results']['bindings']),
            page_start=0,  # for now
            results=self.convert_results(data['results']['bindings'])
        )
        return result_set

    def date_filter_search(self, start_min=None, start_max=None, end_min=None, end_max=None):
        date_filter = ""
        if start_min is not None:
            date_filter += f"FILTER(?start_date >= '{start_min.isoformat()}'^^xsd:date)"
        if start_max is not None:
            date_filter += f"FILTER(?start_date <= '{start_max.isoformat()}'^^xsd:date)"
        if end_min is not None:
            date_filter += f"FILTER(?end_date >= '{end_min.isoformat()}'^^xsd:date)"
        if end_max is not None:
            date_filter += f"FILTER(?end_date <= '{end_max.isoformat()}'^^xsd:date)"


        # Assigning this to a class member makes it easier to test
        self.query = GleanerSearch.build_query(date_filter)

        self.sparql.setQuery(self.query)
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
