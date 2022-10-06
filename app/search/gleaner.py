import json
import logging
import math
import validators

from pygeojson import Point, Polygon, LineString, GeometryCollection
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
            (GROUP_CONCAT(DISTINCT ?license ; separator=",") as ?license)
            (GROUP_CONCAT(DISTINCT ?author ; separator=",") as ?author)
            (GROUP_CONCAT(DISTINCT ?abstract ; separator=",") as ?abstract)
            (GROUP_CONCAT(DISTINCT ?sameAs ; separator=",") as ?sameAs)
            (GROUP_CONCAT(DISTINCT ?keywords ; separator=",") as ?keywords)
            (GROUP_CONCAT(DISTINCT ?spatial_coverage_text ; separator=",") as ?spatial_coverage_text)
            (GROUP_CONCAT(DISTINCT ?spatial_coverage_polygon ; separator=",") as ?spatial_coverage_polygon)
            (GROUP_CONCAT(DISTINCT ?spatial_coverage_line ; separator=",") as ?spatial_coverage_line)
            (GROUP_CONCAT(DISTINCT ?spatial_coverage_box ; separator=",") as ?spatial_coverage_box)
            (GROUP_CONCAT(DISTINCT ?spatial_coverage_circle ; separator=",") as ?spatial_coverage_circle)
            (GROUP_CONCAT(DISTINCT ?spatial_coverage_point ; separator=",") as ?spatial_coverage_point)
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
                    ?s schema:spatialCoverage ?spatial_coverage_text .
                    FILTER(ISLITERAL(?spatial_coverage_text)) .
                }} UNION {{
                    ?s schema:spatialCoverage/schema:geo ?geo .
                    ?geo a schema:GeoShape .
                    {{
                        ?geo schema:polygon ?spatial_coverage_polygon .
                    }} UNION {{
                        ?geo schema:line ?spatial_coverage_line .
                    }} UNION {{
                        ?geo schema:box ?spatial_coverage_box .
                    }} UNION {{
                        ?geo schema:circle ?spatial_coverage_circle .
                    }}
                }} UNION {{
                    ?s schema:spatialCoverage/schema:geo ?geo .
                    ?geo a schema:GeoCoordinates .
                    ?geo schema:longitude ?lon.
                    ?geo schema:latitude ?lat .
                    BIND(concat('str(?lat), " ", str(?lon)') as ?spatial_coverage_point )  .
                }}

                OPTIONAL {{
                    ?s schema:sameAs ?sameAs .
                }}
               OPTIONAL {{

                    {{ ?s schema:license | schema:license/schema:license ?license . }} UNION {{
                    ?catalog ?relationship ?s .
                    ?catalog schema:license ?license .
                }}
                    FILTER(ISLITERAL(?license)) .
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
            SELECT 
                ?total_results 
                ?score 
                ?id 
                ?abstract 
                ?url 
                ?title 
                ?sameAs 
                ?keywords 
                ?license 
                ?spatial_coverage_text
                ?spatial_coverage_polygon
                ?spatial_coverage_line
                ?spatial_coverage_box
                ?spatial_coverage_circle
                ?spatial_coverage_point
                ?author
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
    def _build_author_search_query(author=None):
        if author:
            return f"""
                FILTER CONTAINS(?author, '''{author}''') . 
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
        if text!=None:
            if  text.startswith("'") and text.endswith("'"):
                text = self.escape_char(text)
            elif text.startswith('"') and text.endswith('"'):
                text = self.escape_char(text)
        author = kwargs.pop('author',None)
        page_number = kwargs.pop('page_number', 0)

        user_query = GleanerSearch._build_text_search_query(text)

        # Assigning this to a class member makes it easier to test
        self.query = GleanerSearch.build_query(user_query, None, page_number)
        return self.execute_query(page_number)

    # A helper method to escape char for different matches
    def escape_char(self,text):
        count = text.count('"') #for " " (double quotes)
        count2 = text.count("'") #for ' ' (for single quotes)
        
        #if it has a quote and the count of quotes is odd add an extra quote e.g "Biobasis " Zackenberg" (double quotes)
        if text.startswith('"') and text.endswith('"') and count%2==1 :
            text = text.replace('"','\\"')
            text = text + '\\"'
            

        #if it has a quote and the count of quotes is odd add an extra quote e.g 'Biobasis ' Zackenberg'  (single quotes)
        elif text.startswith("'") and text.endswith("'") and count2%2==1:
            text = text.replace("'",'\\"')
            text = text + '\\"'

        #If the texts has quotes escape them e.g 'Biobasis  Zackenberg' (single quotes)
        elif text.startswith("'") and text.endswith("'"):
            text = text.replace("'",'\\"')

        #If the texts has quotes escape them e.g "Biobasis  Zackenberg" (double quotes)
        elif text.startswith('"') and text.endswith('"'):
            text = text.replace('"','\\"')

        return text


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
        if text!=None:
            if  text.startswith("'") and text.endswith("'"):
                text = self.escape_char(text)
            elif text.startswith('"') and text.endswith('"'):
                text = self.escape_char(text)
       
        author = kwargs.pop('author', None)
        start_min = kwargs.pop('start_min', None)
        start_max = kwargs.pop('start_max', None)
        end_min = kwargs.pop('end_min', None)
        end_max = kwargs.pop('end_max', None)
        page_number = kwargs.pop('page_number', 0)

        date_query = GleanerSearch._build_date_filter_query(
            start_min, start_max, end_min, end_max)
        text_query = GleanerSearch._build_text_search_query(text)
        author_query = GleanerSearch._build_author_search_query(author)

        # Assigning this to a class member makes it easier to test

        self.query = GleanerSearch.build_query(text_query, date_query+author_query, page_number)


        return self.execute_query(page_number)

    # schema:GeoShape lines and polygons are represented as lists of
    # points represented by lat/lon pairs. This converts such a list
    # into a list of tuples in the format that PyGeoJSON expects:
    # (lon, lat)
    def _build_coords_from_list(self, plist):
        points = plist.split(' ')
        return [(points[i+1], points[i])
                for i in range(0, len(points), 2)]

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

        # these are lists of each available geometry type
        geometry = {
            'text': result.pop('spatial_coverage_text', ''),
            'polygon': result.pop('spatial_coverage_polygon', ''),
            'line': result.pop('spatial_coverage_line', ''),
            'box': result.pop('spatial_coverage_box', ''),
            'circle': result.pop('spatial_coverage_circle', ''),
            'point': result.pop('spatial_coverage_point', ''),
        }

        if url is not None:
            result['urls'].append(url)
        if sameAs is not None:
            result['urls'].append(sameAs)
        if validators.url(result['id']):
            result['urls'].append(result['id'])

        # Each of the things in the geometry dict can be a list, so take
        # them from being a list of strings to being a list of PyGeoJSON objects
        # Also, schema:GeoCoordinates are lat lon, while GeoJSON is lon lat,
        # because why would life be simple?
        if len(geometry['text']):
            geometry['text'] = geometry['text'].split(',')
        else:
            geometry['text'] = []

        if len(geometry['point']):
            geometry['point'] = list(map(
                lambda coords: Point(coordinates=tuple(reversed(coords.split(' ')))),
                geometry['point'].split(',')
            ))
        else:
            geometry['point'] = []

        if len(geometry['line']):
            def _build_line_from_points(plist):
                pairs = self._build_coords_from_list(plist)
                return LineString(coordinates=pairs)

            geometry['line'] = list(
                map(_build_line_from_points, geometry['line'].split(',')))
        else:
            geometry['line'] = []

        if len(geometry['polygon']):
            def _build_polygon_from_points(plist):
                pairs = self._build_coords_from_list(plist)
                return Polygon(coordinates=[pairs])

            geometry['polygon'] = list(
                map(_build_polygon_from_points, geometry['polygon'].split(',')))
        else:
            geometry['polygon'] = []

        if len(geometry['box']):
            def _build_bbox_polygon_from_points(plist):
                coords = plist.split(' ')
                return SearchResult.polygon_from_box({
                    'south': coords[0],
                    'west': coords[1],
                    'north': coords[2],
                    'east': coords[3]
                })
            geometry['box'] = list(
                map(_build_bbox_polygon_from_points, geometry['box'].split(',')))
        else:
            geometry['box'] = []

        if len(geometry['circle']):
            logger.info(
                "We got a circle as a spatial coverage object!", result)
        else:
            geometry['circle'] = []

        keywords = result.pop('keywords', '')
        result['keywords'] = keywords.split(',')
        authors = result.pop('author', '')
        result['author'] = authors.split(',')
        result['geometry'] = {
            'text': geometry['text'],
            # put our lists into one big bag of geometries to put on a map
            'geometry_collection': GeometryCollection(
                geometry['point'] +
                geometry['line'] +
                geometry['polygon'] +
                geometry['box'] +
                geometry['circle']
            )
        }
        result['source'] = "Gleaner"
        return SearchResult(**result)
 