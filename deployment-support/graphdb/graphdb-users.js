{
  "users" : {
    "admin" : {
      "username" : "admin",
      "password" : "{bcrypt}$2a$10$1EGIVefe72hCg1dypNCjCeyrs1XKrOt5.VUC.vADTjy7vEjBpAT3.",
      "grantedAuthorities" : [ "ROLE_ADMIN" ],
      "appSettings" : {
        "DEFAULT_INFERENCE" : true,
        "DEFAULT_VIS_GRAPH_SCHEMA" : true,
        "DEFAULT_SAMEAS" : true,
        "IGNORE_SHARED_QUERIES" : false,
        "EXECUTE_COUNT" : true
      },
      "dateCreated" : 1676502250553
    },
    "indexer-user" : {
      "username" : "indexer-user",
      "password" : "{bcrypt}$2a$10$makSbYLkozIT18DNMAVdwOrnie.017hXt0Uy7UM7X2tWBTJ.9SzYS",
      "grantedAuthorities" : [ "WRITE_REPO_*", "READ_REPO_*", "ROLE_USER" ],
      "appSettings" : {
        "DEFAULT_SAMEAS" : true,
        "DEFAULT_INFERENCE" : true,
        "EXECUTE_COUNT" : true,
        "IGNORE_SHARED_QUERIES" : false
      },
      "dateCreated" : 1676502254981
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
