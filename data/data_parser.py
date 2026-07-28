import logging
from connection.wrapper import request
from model.cluster import Cluster
from model.protected_object import ProtectedObject
import graphql.queries
from tqdm import tqdm as tqdm
from data import data_operation

logger = logging.getLogger(__name__)


def get_all_cluster_info(access_token: str) -> list[Cluster]:
    """Fetch all clusters information"""
    clusters = []

    try:
        query, variables = graphql.queries.all_cluster_info_query()
        response = request(access_token, query, variables)
        nodes = response.get("data", {}).get(
            "allClusterConnection", {}).get("nodes", [])
    except Exception as e:
        logger.exception("Failed to fetch cluster data")
        raise LookupError("Unable to collect clusters data!") from e

    if not nodes:
        return []

    for item in nodes:
        cluster = data_operation.create_cluster_from_data(item)
        if cluster:
            clusters.append(cluster)

    return clusters


def get_all_protected_objects(access_token: str,
                              selected_clusters: list[str],
                              csv_data: list,
                              is_relic: bool,
                              is_nas_share_stale: bool,
                              filter_object_type: str = None) -> list[ProtectedObject]:
    """Fetch all protected objects information"""
    protected_objects = []

    for obj in tqdm(csv_data, desc="Searching Objects"):
        try:
            query, variables = graphql.queries.search_object(
                name=obj, 
                cluster_ids=selected_clusters, 
                is_relic=is_relic, 
                is_nas_share_stale=is_nas_share_stale)
            response = request(access_token, query, variables)
            nodes = response.get("data", {}).get(
                "globalSearchResults", {}).get("nodes", [])
        except Exception as e:
            logger.warning("Failed to fetch object data")
            continue

        if not nodes:
            continue

        for item in nodes:
            protected_object = data_operation.create_object_from_data(item)
            if not protected_object:
                continue
            if not filter_object_type or \
                protected_object.object_type.lower() == filter_object_type.lower():
                protected_objects.append(protected_object)
    return protected_objects
