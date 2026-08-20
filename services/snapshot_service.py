import logging
from typing import Dict, List
from collections import defaultdict
from model.protected_object import ProtectedObject
from connection.wrapper import request
import graphql.queries
from tqdm import tqdm

logger = logging.getLogger(__name__)


class SnapshotResult:
    """Class to store snapshot results for an object"""
    def __init__(self, object_id: str, object_name: str, sla_id: str, sla_name: str):
        self.object_id = object_id
        self.object_name = object_name
        self.sla_id = sla_id
        self.sla_name = sla_name
        self.taskchain_uuid = None
        self.error = None
        self.status = "pending"


def group_objects_by_sla(protected_objects: List[ProtectedObject]) -> Dict[str, List[ProtectedObject]]:
    """
    Group protected objects by their SLA ID.
    Objects without an SLA ID or with UNPROTECTED/DO_NOT_PROTECT status are excluded.
    
    Args:
        protected_objects: List of ProtectedObject instances
        
    Returns:
        Dictionary with SLA ID as key and list of objects as value
    """
    grouped = defaultdict(list)
    excluded_count = 0
    
    for obj in protected_objects:
        # Skip objects without SLA ID or with excluded SLA statuses
        if not obj.sla_id or obj.sla_id.upper() in ["UNPROTECTED", "DO_NOT_PROTECT"]:
            excluded_count += 1
            continue
        
        grouped[obj.sla_id].append(obj)
    
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} objects without valid SLA assignment (UNPROTECTED or DO_NOT_PROTECT)")
    
    # Convert defaultdict to regular dict for clarity
    return dict(grouped)


def execute_on_demand_snapshots(
    access_token: str,
    protected_objects: List[ProtectedObject]
) -> Dict[str, List[SnapshotResult]]:
    """
    Execute on-demand snapshots grouped by SLA ID.
    
    Args:
        access_token: RSC API access token
        protected_objects: List of ProtectedObject instances
        
    Returns:
        Dictionary with SLA ID as key and list of SnapshotResult as value
    """
    
    # Group objects by SLA ID
    grouped_by_sla = group_objects_by_sla(protected_objects)
    
    if not grouped_by_sla:
        logger.warning("No objects with SLA ID found. Cannot execute snapshots.")
        return {}
    
    results = {}
    
    # Execute mutation for each SLA group
    for sla_id, objects in tqdm(grouped_by_sla.items(), desc="Executing On-Demand Snapshots"):
        workload_ids = [obj.id for obj in objects]
        
        try:
            logger.info(f"Executing snapshot for SLA {sla_id} with {len(workload_ids)} objects")
            
            mutation, variables = graphql.queries.take_on_demand_snapshot_mutation(
                sla_id=sla_id,
                workload_ids=workload_ids
            )
            
            response = request(access_token, mutation, variables)
            
            # Process response
            snapshot_results = _process_snapshot_response(
                response=response,
                objects_by_id={obj.id: obj for obj in objects},
                sla_id=sla_id
            )
            
            results[sla_id] = snapshot_results
            
        except Exception as e:
            logger.error(f"Failed to execute snapshot for SLA {sla_id}: {str(e)}")
            # Create error results for all objects in this SLA
            error_results = []
            for obj in objects:
                result = SnapshotResult(
                    object_id=obj.id,
                    object_name=obj.name,
                    sla_id=sla_id,
                    sla_name=obj.sla_name
                )
                result.status = "failed"
                result.error = str(e)
                error_results.append(result)
            
            results[sla_id] = error_results
    
    return results


def _process_snapshot_response(
    response: dict,
    objects_by_id: Dict[str, ProtectedObject],
    sla_id: str
) -> List[SnapshotResult]:
    """
    Process GraphQL response from takeOnDemandSnapshot mutation.
    
    Args:
        response: GraphQL response
        objects_by_id: Dictionary mapping object ID to ProtectedObject
        sla_id: SLA ID for this batch
        
    Returns:
        List of SnapshotResult objects
    """
    results = []
    
    try:
        data = response.get("data", {}).get("takeOnDemandSnapshot", {})
        
        # Track which objects were processed
        processed_ids = set()
        
        # Process successful taskchain UUIDs
        taskchain_uuids = data.get("taskchainUuids", [])
        for item in taskchain_uuids:
            object_id = item.get("objectId") or item.get("workloadId")
            if object_id:
                processed_ids.add(object_id)
                obj = objects_by_id.get(object_id)
                if obj:
                    result = SnapshotResult(
                        object_id=object_id,
                        object_name=obj.name,
                        sla_id=sla_id,
                        sla_name=obj.sla_name
                    )
                    result.taskchain_uuid = item.get("taskchainUuid")
                    result.status = "success"
                    results.append(result)
        
        # Process errors
        errors = data.get("errors", [])
        for error_item in errors:
            object_id = error_item.get("objectId") or error_item.get("workloadId")
            if object_id:
                processed_ids.add(object_id)
                obj = objects_by_id.get(object_id)
                if obj:
                    result = SnapshotResult(
                        object_id=object_id,
                        object_name=obj.name,
                        sla_id=sla_id,
                        sla_name=obj.sla_name
                    )
                    result.error = error_item.get("error", "Unknown error")
                    result.status = "failed"
                    results.append(result)
        
        # Create results for objects not in response (shouldn't happen, but just in case)
        for object_id, obj in objects_by_id.items():
            if object_id not in processed_ids:
                result = SnapshotResult(
                    object_id=object_id,
                    object_name=obj.name,
                    sla_id=sla_id,
                    sla_name=obj.sla_name
                )
                result.status = "unknown"
                result.error = "Object not found in response"
                results.append(result)
        
    except Exception as e:
        logger.error(f"Error processing snapshot response: {str(e)}")
        # Return error results for all objects
        for object_id, obj in objects_by_id.items():
            result = SnapshotResult(
                object_id=object_id,
                object_name=obj.name,
                sla_id=sla_id,
                sla_name=obj.sla_name
            )
            result.status = "error"
            result.error = f"Response parsing error: {str(e)}"
            results.append(result)
    
    return results
