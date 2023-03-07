{
  "users" : {
    "admin" : {
      "username" : "admin",
      "password" : "{bcrypt}$2a$10$qr/tAGcMXlvb1zLaskOQuuCiZnnVMPcmMMaI/dv0POVO.lR4qYOmO",
      "grantedAuthorities" : [ "ROLE_ADMIN" ],
      "appSettings" : {
        "DEFAULT_INFERENCE" : true,
        "DEFAULT_VIS_GRAPH_SCHEMA" : true,
        "DEFAULT_SAMEAS" : true,
        "IGNORE_SHARED_QUERIES" : false,
        "EXECUTE_COUNT" : true
      },
      "dateCreated" : 1676506756379
    },
    "indexer-user" : {
      "username" : "indexer-user",
      "password" : "{bcrypt}$2a$10$9ARLdLrp3ggqKg2v7Baktukf0q9Fu8nHzC2WGXd2IJ.uqqPwxU2x.",
      "grantedAuthorities" : [ "WRITE_REPO_*", "READ_REPO_*", "ROLE_USER" ],
      "appSettings" : {
        "DEFAULT_SAMEAS" : true,
        "DEFAULT_INFERENCE" : true,
        "EXECUTE_COUNT" : true,
        "IGNORE_SHARED_QUERIES" : false
      },
      "dateCreated" : 1676594808685
    }
  },
  "user_queries" : {
    "admin" : {
      "SPARQL Select template" : {
        "name" : "SPARQL Select template",
        "body" : "SELECT ?s ?p ?o\nWHERE {\n\t?s ?p ?o .\n} LIMIT 100",
        "shared" : false
      },
      "Clear graph" : {
        "name" : "Clear graph",
        "body" : "CLEAR GRAPH <http://example>",
        "shared" : false
      },
      "Add statements" : {
        "name" : "Add statements",
        "body" : "PREFIX dc: <http://purl.org/dc/elements/1.1/>\nINSERT DATA\n      {\n      GRAPH <http://example> {\n          <http://example/book1> dc:title \"A new book\" ;\n                                 dc:creator \"A.N.Other\" .\n          }\n      }",
        "shared" : false
      },
      "Remove statements" : {
        "name" : "Remove statements",
        "body" : "PREFIX dc: <http://purl.org/dc/elements/1.1/>\nDELETE DATA\n{\nGRAPH <http://example> {\n    <http://example/book1> dc:title \"A new book\" ;\n                           dc:creator \"A.N.Other\" .\n    }\n}",
        "shared" : false
      }
    }
  }
}