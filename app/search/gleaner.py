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

                ?s a ?type .

                ?s ?ids ?id .
                ?s ?urls ?url .
                ?s ?titles ?title .
                ?s ?temporal ?temporal_coverage .

                OPTIONAL {{
                    ?s ?abstracts ?abstract .
                    ?s ?keys ?keyword .
                    ?s ?sameAsVals ?sameAs .
                }}

                {user_query}

            }}
            GROUP BY ?id ?url ?title
            ORDER BY DESC(?score)
            OFFSET 0
            LIMIT {GleanerSearch.PAGE_SIZE}
        """

    @staticmethod
    def _build_text_search_query(text=None):
        if text is None:
            return ""

        # A blank search in this will give NO results, which seems like
        # the opposite of what we want.
        return f"""
            ?lit bds:search "{text}" .
            ?lit bds:matchAllTerms "false" .
            ?lit bds:relevance ?relevance .
            ?s ?p ?lit .
        """

    @staticmethod
    def _build_date_filter_query(start_min=None, start_max=None, end_min=None, end_max=None):
        # First of all, make sure we are even filtering anything. Do not bother binding variables,
        # which may be expensive, if we do not need them.
        if start_min is None and start_max is None and end_min is None and end_max is None:
            return ""

        # First, bind our necessary variables to filter start and end dates for temporal coverage
        user_query = """
            BIND(
                IF(
                    CONTAINS(?temporal_coverage, "/"),
                    STRDT(STRBEFORE(?temporal_coverage, "/"), xsd:date),
                    IF(
                        CONTAINS(?temporal_coverage, " - "),
                        STRDT(STRBEFORE(?temporal_coverage, " - "), xsd:date),
                        ?temporal_coverage
                    )
                )
              AS ?start_date
            )

            BIND(
                IF(
                    CONTAINS(?temporal_coverage, "/"),
                    STRDT(STRAFTER(?temporal_coverage, "/"), xsd:date),
                    IF(
                        CONTAINS(?temporal_coverage, " - "),
                        STRDT(STRAFTER(?temporal_coverage, " - "), xsd:date),
                        ?temporal_coverage
                    )
                )
              AS ?end_date
            )
        """

        # Then do the actual filtering, depending on what the user asked for
        if start_min is not None:
            user_query += f"FILTER(?start_date >= '{start_min.isoformat()}'^^xsd:date)"
        if start_max is not None:
            user_query += f"FILTER(?start_date <= '{start_max.isoformat()}'^^xsd:date)"
        if end_min is not None:
            user_query += f"FILTER(?end_date >= '{end_min.isoformat()}'^^xsd:date)"
        if end_max is not None:
            user_query += f"FILTER(?end_date <= '{end_max.isoformat()}'^^xsd:date)"

        return user_query

    def __init__(self, **kwargs):
        ENDPOINT_URL = kwargs.pop('endpoint_url')
        self.sparql = SPARQLWrapper(ENDPOINT_URL)

    def execute_query(self):
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

    def text_search(self, text=None):
        user_query = GleanerSearch._build_text_search_query(text)

        # Assigning this to a class member makes it easier to test
        self.query = GleanerSearch.build_query(user_query)
        return self.execute_query()

    def date_filter_search(self, start_min=None, start_max=None, end_min=None, end_max=None):
        user_query = GleanerSearch._build_date_filter_query(
            start_min, start_max, end_min, end_max)
        # Assigning this to a class member makes it easier to test
        self.query = GleanerSearch.build_query(user_query)
        return self.execute_query()

    def combined_search(self, text=None, start_min=None, start_max=None, end_min=None, end_max=None):
        user_query = GleanerSearch._build_date_filter_query(start_min, start_max, end_min, end_max)
        user_query += GleanerSearch._build_text_search_query(text)

        # Assigning this to a class member makes it easier to test
        self.query = GleanerSearch.build_query(user_query)
        return self.execute_query()

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
