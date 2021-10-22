from SPARQLWrapper import SPARQLWrapper, JSON
from .searcher_base import SearcherBase

def convert_result(sparql_result_dict):
    result = {}
    for k, v in sparql_result_dict.items():
        result[k] = v['value']
    return result

class GleanerSearch(SearcherBase):
    # todo: this DEFINITELY needs to go in a config
    SPARQL_ENDPOINT="http://localhost:9999/blazegraph/namespace/polder/sparql"
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)


    def text_search(self, **kwargs):
        # todo: what other types aside from schema:Dataset do we want?
        text = kwargs.pop('q', '')

        self.sparql.setQuery(
            f"""
            PREFIX schema: <https://schema.org/>

            SELECT DISTINCT ?s ?score ?description ?name ?headline ?url
            {{
               ?lit bds:search "{text}" .
               ?lit bds:matchAllTerms "false" .
               ?lit bds:relevance ?score .
               ?s ?p ?lit .

               graph ?g {{
                ?s ?p ?lit .
                VALUES ?type {{ schema:Dataset }}
                ?x rdf:type ?type
                OPTIONAL {{ ?s schema:name ?name .   }}
                OPTIONAL {{ ?s schema:headline ?headline .   }}
                OPTIONAL {{ ?s schema:url ?url .   }}
                OPTIONAL {{ ?s schema:description ?description .    }}
              }}
            }}
            ORDER BY DESC(?score)
            OFFSET 0
            LIMIT 100
        """
        )
        self.sparql.setReturnFormat(JSON)
        data = self.sparql.query().convert()

        return list(map(convert_result, data['results']['bindings']))
        # todo: show the number of documents and offset in my results query
