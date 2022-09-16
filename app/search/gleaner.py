import logging
import math
import validators

from SPARQLWrapper import SPARQLWrapper, JSON, POST
from .search import SearcherBase, SearchResultSet, SearchResult

logger = logging.getLogger('app')

class GleanerSearch(SearcherBase):
    @staticmethod
    def build_query(text_query="", filter_query="", page_number=1):
        # NOTE: Page numbers start counting from 1, because this number gets exposed
        # to the user, and people who are not programmers are weirded out by 0-indexed things.
        # The max is there in case a negative url parameter gets in here and causes havoc.
        page_start = max(0, page_number - 1) * GleanerSearch.PAGE_SIZE

        # GraphDB doesn't allow named subqueries. So we write our query out twice - once to get the total
        # result count, in order to do paging, and once to get the actual results and page through them.
        base_query = f"""
            SELECT
            (MAX(?relevance) AS ?score)
            ?s
            ?id
            ?url
            ?title
            ?g
            (GROUP_CONCAT(DISTINCT ?license ; separator=", ") as ?license)
            (GROUP_CONCAT(DISTINCT ?author ; separator=", ") as ?author)
            (GROUP_CONCAT(DISTINCT ?abstract ; separator=", ") as ?abstract)
            (GROUP_CONCAT(DISTINCT ?sameAs ; separator=", ") as ?sameAs)
            (GROUP_CONCAT(DISTINCT ?keywords ; separator=", ") as ?keywords)
            (GROUP_CONCAT(DISTINCT ?temporal_coverage ; separator=", ") as ?temporal_coverage)
            (GROUP_CONCAT(DISTINCT ?spatial_coverage ; separator=", ") as ?spatial_coverage)
            {{

                {text_query}
                ?s a schema:Dataset  .
                ?s schema:name ?title .
                ?s schema:temporalCoverage ?temporal_coverage .

                {{ ?s schema:keywords ?keywords . }} UNION {{
                    ?catalog ?relationship ?s .
                    ?catalog schema:keywords ?keywords .
                }}

                {{
                    ?s schema:description ?abstract .
                }} UNION {{
                    ?s schema:description/schema:value  ?abstract .
                }}

                {{
                    ?s schema:spatialCoverage ?spatial_coverage .
                    FILTER(ISLITERAL(?spatial_coverage)) .
                }} UNION {{
                    ?s schema:spatialCoverage/schema:geo ?geo .
                    ?geo a schema:GeoShape .
                    {{
                        ?geo schema:polygon ?polygon .
                        BIND(concat("polygon:", ?polygon) as ?spatial_coverage) .
                    }} UNION {{
                        ?geo schema:line ?line .
                        BIND(concat("line:", ?line) as ?spatial_coverage) .
                    }} UNION {{
                        ?geo schema:box ?box .
                        BIND(concat("box:", ?box) as ?spatial_coverage) .
                    }} UNION {{
                        ?geo schema:circle ?circle .
                        BIND(concat("circle:", ?circle) as ?spatial_coverage) .
                    }}
                }} UNION {{
                    ?s schema:spatialCoverage/schema:geo ?geo .
                    ?geo a schema:GeoCoordinates .
                    ?geo schema:longitude ?lon.
                    ?geo schema:latitude ?lat .
                    BIND(concat("longitude:", str(?lon), ", latitude:", str(?lat) ) as ?spatial_coverage )  .
                }}

                OPTIONAL {{
                    ?s schema:sameAs ?sameAs .
                }}
               OPTIONAL {{

                    {{ ?s schema:license ?license . }} UNION {{
                    ?catalog ?relationship ?s .
                    ?catalog schema:license ?license .
                }}
                }}
                OPTIONAL {{
                    ?s schema:url ?url .
                }}
                OPTIONAL {{
                    ?s schema:identifier | schema:identifier/schema:value ?identifier .
                    FILTER(ISLITERAL(?identifier)) .
                }}
                OPTIONAL {{
                    ?sp prov:generated ?g  .
                }}
                OPTIONAL {{
                    
                    {{ ?s schema:creator/schema:name ?author . }} UNION {{
                    ?catalog ?relationship ?s .
                    ?catalog schema:creator/schema:name ?author .
                }}
                    FILTER(ISLITERAL(?author)) .
                }}
                {filter_query}
                BIND(COALESCE(?identifier, ?s) AS ?id)
            }}
            GROUP BY ?s ?id ?url ?title  ?g
        """

        return f"""
            PREFIX luc: <http://www.ontotext.com/connectors/lucene#>
            PREFIX luc-index: <http://www.ontotext.com/connectors/lucene/instance#>
            PREFIX onto: <http://www.ontotext.com/>
            PREFIX schema: <https://schema.org/>
            prefix prov: <http://www.w3.org/ns/prov#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT ?total_results ?score ?id ?abstract ?url ?title ?sameAs ?keywords ?license ?temporal_coverage ?spatial_coverage ?author
            {{
                {{
                    SELECT (COUNT(*) as ?total_results) {{
                        {base_query}
                    }}
                }}
                UNION
                {{
                    {base_query}
                    OFFSET {page_start}
                    LIMIT {GleanerSearch.PAGE_SIZE}
                }}
            }}
            ORDER BY DESC(?total_results) DESC(?score)
        """

    @staticmethod
    def _build_text_search_query(text=None):
        if text:
            return f"""
                ?search a luc-index:full_text_search ;
                luc:query '''{text}''' ;
                luc:entities ?s .
                ?s luc:score ?relevance .
            """
        else:
            # A blank search in this doesn't filter results, it just takes longer.
            return ""

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

    def execute_query(self, page_number):
        logger.debug(self.query)
        self.sparql.setQuery(self.query)
        self.sparql.setMethod(POST)
        self.sparql.setReturnFormat(JSON)
        data = self.sparql.query().convert()

        # The first result in each result set is now a row telling us the total number of
        # available results.
        total_results = int(data['results']['bindings'].pop(0)[
            'total_results']['value'])

        result_set = SearchResultSet(
            total_results=total_results,
            available_pages=math.ceil(total_results / GleanerSearch.PAGE_SIZE),
            page_number=page_number,
            # The remaining results are normal results.
            results=self.convert_results(data['results']['bindings'])
        )
        return result_set

    def text_search(self, **kwargs):
        text = kwargs.pop('text', None)
        page_number = kwargs.pop('page_number', 0)

        user_query = GleanerSearch._build_text_search_query(text)

        # Assigning this to a class member makes it easier to test
        self.query = GleanerSearch.build_query(user_query, None, page_number)
        return self.execute_query(page_number)

    def date_filter_search(self, **kwargs):
        start_min = kwargs.pop('start_min', None)
        start_max = kwargs.pop('start_max', None)
        end_min = kwargs.pop('end_min', None)
        end_max = kwargs.pop('end_max', None)
        page_number = kwargs.pop('page_number', 0)

        user_query = GleanerSearch._build_date_filter_query(
            start_min, start_max, end_min, end_max)
        # Assigning this to a class member makes it easier to test
        self.query = GleanerSearch.build_query(None, user_query, page_number)
        return self.execute_query(page_number)

    def combined_search(self, **kwargs):
        text = kwargs.pop('text', None)
        start_min = kwargs.pop('start_min', None)
        start_max = kwargs.pop('start_max', None)
        end_min = kwargs.pop('end_min', None)
        end_max = kwargs.pop('end_max', None)
        page_number = kwargs.pop('page_number', 0)

        date_query = GleanerSearch._build_date_filter_query(
            start_min, start_max, end_min, end_max)
        text_query = GleanerSearch._build_text_search_query(text)

        # Assigning this to a class member makes it easier to test
        self.query = GleanerSearch.build_query(text_query, date_query, page_number)
        return self.execute_query(page_number)

    def convert_result(self, sparql_result_dict):
        result = {}
        for k, v in sparql_result_dict.items():
            result[k] = v['value']
        # if we didn't do a text search, we didn't get a score.
        # This is a workaround for now.
        result['score'] = result.pop('score', 1)
        result['urls'] = []

        url = result.pop('url', None)
        sameAs = result.pop('sameAs', None)
        if url is not None:
            result['urls'].append(url)
        if sameAs is not None:
            result['urls'].append(sameAs)
        if validators.url(result['id']):
            result['urls'].append(result['id'])

        keywords = result.pop('keywords', '')
        result['keywords'] = keywords.split(',')
        authors = result.pop('author', '')
        result['author'] = authors.split(',')
        result['source'] = "Gleaner"
        return SearchResult(**result)
