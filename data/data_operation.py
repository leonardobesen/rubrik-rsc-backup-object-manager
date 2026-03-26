import logging
from model.cluster import Cluster
from model.protected_object import ProtectedObject

logger = logging.getLogger(__name__)


def create_cluster_from_data(data: dict) -> Cluster | None:
    """Create a Cluster object from a dictionary of data."""
    try:
        return Cluster(
            id=data["id"],
            name=data["name"],
            connected_state=data.get("state", {}).get("connectedState"),
        )
    except KeyError as e:
        logger.error(
            f"Missing expected cluster data field: {e}", exc_info=True)
    except Exception as e:
        logger.exception(
            "Unexpected error while creating Cluster object", exc_info=True)
    return None


def create_object_from_data(data: dict) -> ProtectedObject | None:
    """Create a ProtectedObject object from a dictionary of data."""
    try:
        protect_obj = ProtectedObject(
            id=data["id"],
            name=data["name"],
            object_type=data["objectType"],
            sla_id=data.get("effectiveSlaDomain", {}).get("id", ""),
            sla_name=data.get("effectiveSlaDomain", {}).get("name", "")
        )
        
        protect_obj.location = data.get("hostAddress","")
        
        return protect_obj
    except KeyError as e:
        logger.error(
            f"Missing expected object data field: {e}", exc_info=True)
    except Exception as e:
        logger.exception(
            "Unexpected error while creating ProtectedObject", exc_info=True)
    return None
