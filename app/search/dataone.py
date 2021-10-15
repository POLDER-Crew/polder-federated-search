from d1_client import solr_client

class DataOneSearch:
    # https://dataone-python.readthedocs.io/en/latest/d1_client/api/d1_client.html#module-d1_client.solr_client
    client = solr_client.SolrClient()

    def text_search(self, **kwargs):
        return self.client.search(**kwargs)
