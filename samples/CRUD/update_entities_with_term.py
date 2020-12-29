import argparse
from collections import namedtuple
import json
import os

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import AtlasClient  # Communicate with your Atlas server
from pyapacheatlas.readers import ExcelConfiguration, ExcelReader

SearchOutput = namedtuple(
    "SearchOutput", "SearchScore,AssetId,AssetType,TermId,TermDisplay,Reason")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--threshold", "--t",
        help="The level of the search score to filter to, Defaults to 3.0",
        default=3.0, type=float)
    args = parser.parse_args()

    # Authenticate against your Atlas server
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    client = AtlasClient(
        endpoint_url=os.environ.get("ENDPOINT_URL", ""),
        authentication=oauth
    )

    glossary = client.get_glossary()
    terms = glossary["terms"]
    # Consists of DisplayText and term
    term_variants = {
        t["displayText"]: {'guid': t["termGuid"], "variants": []} for t in terms
    }
    # TODO: Apply business logic to massage the terms

    for term in terms:
        primary_display_text = term["displayText"]
        term_guid = term["termGuid"]

        search_query = client.search_entities(
            query=f"{primary_display_text}*",
            # This is not working :-(
            # search_filter={"add": [{"typeName": "demo_column_lineage","includeSubTypes": False}]}
        )
        lowest_seen_score = 99
        threshold = 1.0

        search_intermediate_results = []

        for batch in search_query:
            for entity in batch:
                if entity["typeName"] == "AtlasGlossaryTerm":
                    continue
                search_score = entity['@search.score']
                lowest_seen_score = search_score if search_score < lowest_seen_score else lowest_seen_score
                if search_score < threshold:
                    break
                search_reason = "No reason given"
                if '@search.highlights' in entity:
                    search_reason = entity['@search.highlights']
                searchoutput = SearchOutput(
                    search_score, entity['id'],
                    entity['typeName'], term_guid, primary_display_text,
                    search_reason
                )

                search_intermediate_results.append(searchoutput)

            if lowest_seen_score < threshold:
                break

    for so in search_intermediate_results:
        print(so)
    input(">>>>Review the printout above to see what will be associated. Press enter to continue or Ctrl+C to back out now...")
    for so in search_intermediate_results:
        print(
            f"Attempting to add '{so.TermDisplay}' to {so.AssetId} ({so.SearchScore}) because {so.Reason} ")
        relationship = {
            "typeName": "AtlasGlossarySemanticAssignment",
            "attributes": {},
            "guid": -100,
            "end1": {
                "guid": so.TermId,
                "typeName": "AtlasGlossaryTerm"
            },
            "end2": {
                "guid": so.AssetId
            }
        }
        try:
            results = client.upload_relationship(relationship)
            print("\tSuccess")
        except Exception as e:
            print(
                f"\tException for {so.TermId}:{so.AssetId} and was not uploaded: {e}")
        print("\n")
