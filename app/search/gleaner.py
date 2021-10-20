from SPARQLWrapper import SPARQLWrapper, JSON
from .searcher_base import SearcherBase

class GleanerSearch(SearcherBase):
    # todo: this DEFINITELY needs to go in a config
    SPARQL_ENDPOINT="http://localhost:9999/blazegraph/namespace/polder/sparql"
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)

    def text_search(self, **kwargs):
        text = kwargs.pop('q', '')

        self.sparql.setQuery(
            f"""
            prefix prov: <http://www.w3.org/ns/prov#>
            PREFIX con: <http://www.ontotext.com/connectors/lucene#>
            PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
            PREFIX con-inst: <http://www.ontotext.com/connectors/lucene/instance#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <https://schema.org/>
            PREFIX schemaold: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT ?s
            WHERE {{
              SERVICE <{self.SPARQL_ENDPOINT}> {{
                   ?lit bds:search "{text}" .
                   ?lit bds:matchAllTerms "false" .
                   ?lit bds:relevance ?score .
                   ?s ?p ?lit .

                   graph ?g {{
                    ?s ?p ?lit .
                    ?s rdf:type ?type .
                    OPTIONAL {{ ?s schema:name ?name .   }}
                    OPTIONAL {{ ?s schema:headline ?headline .   }}
                    OPTIONAL {{ ?s schema:url ?url .   }}
                    OPTIONAL {{ ?s schema:description ?description .    }}
                  }}
                   ?sp prov:generated ?g  .
                   ?sp prov:used ?used .
                   ?used prov:hadMember ?hm .
                   ?hm prov:wasAttributedTo ?wat .
                   ?wat rdf:name ?orgname .
                   ?wat rdfs:seeAlso ?domain
              }}
            }}
            ORDER BY DESC(?score)
            OFFSET 0
            """
        )
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()
        return results
