from configuration.configuration import get_excluded_clusters_uuids


def all_cluster_info_query() -> tuple[str, dict]:
    variables = {
        "filter": {
            "productFilters": [
                {
                    "productType": "CDM"
                }
            ],
            "excludeId": get_excluded_clusters_uuids()
        }
    }

    query = f"""query ListAllClustersInfo($filter: ClusterFilterInput,$sortBy: ClusterSortByEnum = ClusterName){{
      allClusterConnection(filter: $filter, sortBy: $sortBy){{
        nodes{{
          id
          name
          state{{
            connectedState
          }}
        }}
      }}
    }}"""

    return query, variables


def search_object(name: str, cluster_ids: list[str], is_relic: bool = False, is_nas_share_stale: bool = None) -> tuple[str, dict]:
    variables = {
        "filter": [
            {
                "field": "LOCATION",
                "texts": [
                    name
                ]
            },
            {
                "field": "CLUSTER_ID",
                "texts": cluster_ids
            },
            {
                "field": "IS_GHOST",
                "texts": [
                    "false"
                ]
            }
        ],
        "sortBy": "NAME",
        "sortOrder": "ASC",
        "first": 300
    }
    
    if is_relic:
        variables["filter"].append({
            "field": "IS_RELIC",
            "texts": [
                "true"
            ]
        })
    
    if is_nas_share_stale == True:
        variables["filter"].append({
            "field": "IS_STALE",
            "texts": [
                "true"
            ]
        })
      

    query = f"""query GlobalSearchObjectQuery($first: Int!, 
    $filter: [Filter!]!, 
    $sortBy: HierarchySortByField, 
    $sortOrder: SortOrder, 
    $after: String) {{
      globalSearchResults(
        first: $first
        filter: $filter
        sortBy: $sortBy
        sortOrder: $sortOrder
        after: $after
      ) {{
        nodes {{
        	id
        	name
          ...on NasShare {{
            hostAddress
          }}
        	objectType
          effectiveSlaDomain {{
            id
            name
          }}
        }}
      }}
    }}"""

    return query, variables
