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


def search_object(name: str, cluster_ids: list[str], is_relic: bool = False, is_nas_share_stale: bool = False) -> tuple[str, dict]:
    variables = {
        "filter": [
            {
                "field": "LOCATION",
                "texts": [
                    name
                ]
            },
            {
                "field": "IS_GHOST",
                "texts": [
                    "false"
                ]
            },
            {
                "field": "IS_ACTIVE",
                "texts": [
                    "true"
                ]
            }
        ],
        "sortBy": "NAME",
        "sortOrder": "ASC",
        "first": 300
    }

    if cluster_ids:
        variables["filter"].append({
            "field": "CLUSTER_ID",
            "texts": cluster_ids
        })

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

    query = """query GlobalSearchLocationQuery(
      $first: Int!,
      $filter: [Filter!]!, 
      $sortBy: HierarchySortByField, 
      $sortOrder: SortOrder,) {
      globalSearchResults(
        first: $first
        filter: $filter
        sortBy: $sortBy
        sortOrder: $sortOrder
      ) {
        nodes {
          id
          name
          objectType
          ...on NasShare {
            hostAddress
          }
          effectiveSlaDomain {
            id
            name
          }
        }
      }
    }
    """

    return query, variables
