import rdflib
from .searcher_base import SearcherBase

class GleanerSearch(SearcherBase):
    SPARQL_ENDPOINT="http://triplestore:9999"
    graph = rdflib.Graph()

    def text_search(self, **kwargs):
        return g.query(
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
              SERVICE <{SPARQL_ENDPOINT}> {{
                   ?lit bds:search "{kwargs['q']}" .
                   ?lit bds:matchAllTerms "false" .
                   ?lit bds:relevance ?score .
                   ?s ?p ?lit .

                   graph ?g {
                    ?s ?p ?lit .
                    ?s rdf:type ?type .
                    OPTIONAL { ?s schema:name ?name .   }
                    OPTIONAL { ?s schema:headline ?headline .   }
                    OPTIONAL { ?s schema:url ?url .   }
                    OPTIONAL { ?s schema:description ?description .    }
                  }
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
