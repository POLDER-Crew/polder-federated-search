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

# this does better for npdc - let's see what we can do here
# PREFIX schema: <http://schema.org/>

# SELECT DISTINCT ?s ?score ?lit ?description ?name ?headline ?url ?boundingbox ?temporalCoverage ?type
# {
#   BIND(schema:Dataset AS ?type)
#   ?s a ?o
#   FILTER(?o=?type)

#   ?lit bds:search "ice" .
#   ?lit bds:matchAllTerms "false" .
#   ?lit bds:relevance ?score .
#   ?a rdf:type schema:Dataset .
#   ?s ?p ?lit .

#   graph ?g {
#     ?s ?p ?lit .
#    OPTIONAL { ?s schema:name ?name .   }
#     OPTIONAL { ?s schema:headline ?headline .   }
#     OPTIONAL { ?s schema:url ?url .   }
#     OPTIONAL { ?s schema:description ?description .    }
#     OPTIONAL { ?s schema:spatialCoverage/schema:geo/schema:box ?boundingbox . }
#     OPTIONAL { ?s schema:temporalCoverage ?temporalCoverage . }
#  }
#       }

# LIMIT 100
        self.sparql.setQuery(
            f"""
            PREFIX schema: <https://schema.org/>

            SELECT DISTINCT ?s ?score ?description ?name ?headline ?url ?boundingbox ?temporalCoverage ?type
            {{
               ?lit bds:search "{text}" .
               ?lit bds:matchAllTerms "false" .
               ?lit bds:relevance ?score .
               ?s ?p ?lit .

               graph ?g {{
                ?s ?p ?lit .
                VALUES ?type {{ schema:Organization }} .
                MINUS {{ ?s rdf:type ?type }}
                OPTIONAL {{ ?s schema:name ?name .   }}
                OPTIONAL {{ ?s schema:headline ?headline .   }}
                OPTIONAL {{ ?s schema:url ?url .   }}
                OPTIONAL {{ ?s schema:description ?description .    }}
                OPTIONAL {{ ?s schema:spatialCoverage/schema:geo/schema:box ?boundingbox . }}
                OPTIONAL {{ ?s schema:temporalCoverage ?temporalCoverage . }}

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
