import pandas as pd
import os
from datetime import datetime
from configuration.configuration import get_root_dir
from services.snapshot_service import SnapshotResult


def generate_snapshot_report(results_dict: dict) -> str:
    """
    Generate a CSV report from snapshot execution results.
    
    Args:
        results_dict: Dictionary with SLA ID as key and list of SnapshotResult as value
        
    Returns:
        Path to the generated CSV file
    """
    
    # Flatten results
    all_results = []
    for sla_id, results in results_dict.items():
        for result in results:
            all_results.append({
                'SLA ID': result.sla_id,
                'SLA Name': result.sla_name,
                'Object ID': result.object_id,
                'Object Name': result.object_name,
                'Status': result.status,
                'Taskchain UUID': result.taskchain_uuid if result.taskchain_uuid else '',
                'Error': result.error if result.error else ''
            })
    
    if not all_results:
        raise ValueError("No snapshot results to report")
    
    # Create DataFrame
    df = pd.DataFrame(all_results)
    
    # Generate filename with timestamp
    now = datetime.now().strftime("%d-%m-%Y_%H_%M_%S")
    file_name = f'Snapshot_Results_{now}.csv'
    report_path = os.path.join(get_root_dir(), 'reports', file_name)
    
    # Save as CSV
    df.to_csv(report_path, index=False)
    
    return report_path
