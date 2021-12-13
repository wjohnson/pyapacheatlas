import argparse
from collections import namedtuple
import json
import os

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient

SearchOutput = namedtuple(
    typename="SearchOutput",
    field_names="SearchScore,AssetId,AssetType,TermId,TermDisplay,Reason"
)

if __name__ == "__main__":
    """
     This sample provides an example of discovering and updating entities that
     are related to terms in your glossary.

     The samples looks at all glossary terms and then searches for each term
     with a wildcard.
    """
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
    client = PurviewClient(
        account_name=os.environ.get("PURVIEW_NAME", ""),
        authentication=oauth
    )

    glossary = client.glossary.get_glossary()
    try:
        terms = glossary["terms"]
    except KeyError:
        print("Your default glossary appears to be empty.")
        print("Please add a term to your glossary and try this demo again.")
        exit(3)
    # Consists of DisplayText and term
    term_variants = {
        t["displayText"]: {'guid': t["termGuid"], "variants": []} for t in terms
    }

    # TODO: You apply business logic to massage the terms in different ways
    # based on how you might say "Master Data" in the glossary but have it
    # on a table as "m-data" (as an example).

    # For every term, search across all dataset entities (so no process entities).
    for term in terms:
        primary_display_text = term["displayText"]
        term_guid = term["termGuid"]

        search_query = client.discovery.search_entities(
            query=f"{primary_display_text}*",
            search_filter={"typeName": "DataSet", "includeSubTypes": True}
        )
        lowest_seen_score = 99
        threshold = args.threshold

        search_intermediate_results = []

        # Iterate over the search results for each term
        # Discover all of the entities that are relevant by cutting the search
        # off at a specific relevance threshold (default is 3.0).
        for entity in search_query:
            if entity["entityType"] == "AtlasGlossaryTerm":
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
                entity['entityType'], term_guid, primary_display_text,
                search_reason
            )

            search_intermediate_results.append(searchoutput)

            if lowest_seen_score < threshold:
                break

    # Print out the search results so you can decide whether you want to move
    # forward or not with adding the terms.
    for so in search_intermediate_results:
        print(so)
    input(">>>>Review the printout above to see what will be associated. Press enter to continue or Ctrl+C to back out now...")
    # For every entity and term that met the threshold, add an
    # AtlasGlossarySemanticAssignment relationship (one at a time).
    for so in search_intermediate_results:
        print(
            f"Attempting to add '{so.TermDisplay}' to {so.AssetId} ({so.SearchScore}) because {so.Reason} ")
        relationship = {
            "typeName": "AtlasGlossarySemanticAssignment",
            "attributes": {},
            "guid": "-100",
            "end1": {
                "guid": so.TermId,
                "typeName": "AtlasGlossaryTerm"
            },
            "end2": {
                "guid": so.AssetId
            }
        }
        try:
            # Attempt the upload, but the relationship may already exist
            # So simply skip log it and skip past it.
            results = client.upload_relationship(relationship)
            print("\tSuccess")
        except Exception as e:
            print(
                f"\tException for {so.TermId}:{so.AssetId} and was not uploaded: {e}")
