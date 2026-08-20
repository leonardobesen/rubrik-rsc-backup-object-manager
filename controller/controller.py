import logging
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
import configuration.configuration as conf
from model.protected_object import ProtectedObject
import data.data_parser as data_parser
from services.snapshot_service import execute_on_demand_snapshots

logger = logging.getLogger(__name__)


def parse_command_line_args():
    """
    Parse command-line arguments.
    
    Returns:
        Namespace with parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Search Rubrik Security Cloud for protected objects and optionally trigger on-demand snapshots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --input hostname_list.csv
        """
    )
    
    parser.add_argument(
        "--input",
        help="CSV filename to use (must be in reports/input/ folder)",
        required=False
    )
    
    return parser.parse_args()


def show_menu(access_token: str) -> tuple[list[str], str | None, bool, bool | None]:
    """Show user a menu to select cluster(s) and optionally filter by object type."""
    clusters = data_parser.get_all_cluster_info(access_token)

    if not clusters:
        print("No clusters available.")
        return [], None, False, None

    print("Select the numbers of clusters you want to search the objects (comma-separated for multiple):")
    for idx, cluster in enumerate(clusters):
        print(f"{idx + 1}. {cluster.name}")

    selection = input("Your choice: ")

    try:
        selected_indices = [int(i.strip()) - 1 for i in selection.split(",")]
    except ValueError:
        print("Invalid input. Please enter only numbers separated by commas.")
        return [], None, False, None

    valid_indices = [i for i in selected_indices if 0 <= i < len(clusters)]
    if not valid_indices:
        print("No valid selections.")
        return [], None, False, None

    selected_ids = [clusters[i].id for i in valid_indices]

    # Ask if the user wants to filter by object type
    filter_choice = input("Do you want to filter by a specific object type? (yes/no): ").strip().lower()

    object_types = [
        "PhysicalHost",
        "Mssql",
        "OracleDatabase",
        "LinuxFileset",
        "WindowsFileset",
        "NasShare",
        "VolumeGroup",
        "ManagedVolume",
        "MssqlInstance",
        "OracleHost",
        "ORACLE_DATA_GUARD_GROUP",
        "MssqlAvailabilityGroup"
    ]

    if filter_choice in ["yes", "y"]:
        print("\nAvailable Object Types:")
        for idx, obj_type in enumerate(object_types, start=1):
            print(f"{idx}. {obj_type}")

        obj_selection = input("Type the number or name of the object type you want to filter: ").strip()

        # Try numeric selection first
        if obj_selection.isdigit():
            obj_index = int(obj_selection) - 1
            if 0 <= obj_index < len(object_types):
                filter_object_type = object_types[obj_index]
            else:
                print("Invalid selection. No object type filter applied.")
                filter_object_type = None
        else:
            if obj_selection in object_types:
                filter_object_type = obj_selection
            else:
                print("Invalid object type name. No filter applied.")
                filter_object_type = None
    else:
        filter_object_type = None

    # Ask if the user wants to list relic objects
    list_relic = input("Do you want to search for ONLY relic objects? (yes/no): ").strip().lower()
    is_relic = list_relic in ["yes", "y"]

    # If NasShare is selected, ask about stale NAS shares
    is_stale_nas = False
    if filter_object_type == "NasShare":
        list_stale = input("Do you want to search for ONLY stale NAS shares? (yes/no): ").strip().lower()
        is_stale_nas = list_stale in ["yes", "y"]

    return selected_ids, filter_object_type, is_relic, is_stale_nas


def _prompt_file_selection(csv_files: list[Path]) -> Path:
    """
    Display a formatted list of CSV files with metadata and prompt user to select.
    Auto-selects if only one file exists.
    """
    if len(csv_files) == 1:
        print(f"Using: {csv_files[0].name}")
        return csv_files[0]
    
    print("\nAvailable CSV files:")
    print(f"{'#':<3} {'Filename':<40} {'Size':<12} {'Modified':<20}")
    print("-" * 75)
    
    for idx, path in enumerate(csv_files, start=1):
        size = path.stat().st_size
        mod_time = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size_str = f"{size:,} B" if size < 1024 else f"{size/1024:.1f} KB"
        print(f"{idx:<3} {path.name:<40} {size_str:<12} {mod_time:<20}")
    
    print("-" * 75)
    try:
        selection = int(input("Select a CSV file (enter number): ")) - 1
    except ValueError:
        print("Invalid input. Please enter a number.")
        sys.exit(1)

    if selection not in range(len(csv_files)):
        print("Invalid selection.")
        sys.exit(1)

    return csv_files[selection]


def _read_hostnames_from_file(csv_file: Path) -> list[str]:
    try:
        content = csv_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Failed to read CSV file: {e}")
        sys.exit(1)

    return [value.strip() for value in re.split(r"[\s,;:]+", content) if value.strip()]


def parse_csv_files(csv_filename: str = None):
    """
    Parse CSV files from reports/input directory.
    
    Args:
        csv_filename: Optional specific filename to use. If not provided, user will be prompted.
        
    Returns:
        List of hostnames extracted from the CSV file
    """
    directory = Path(conf.report_input_path())

    if not directory.is_dir():
        print(f"Directory does not exist: {directory}")
        sys.exit(1)

    csv_files = sorted(directory.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in: {directory}")
        sys.exit(1)

    # If specific filename provided via command line, try to use it
    if csv_filename:
        matching_file = next((f for f in csv_files if f.name == csv_filename), None)
        if matching_file:
            print(f"Using specified file: {matching_file.name}")
            selected_file = matching_file
        else:
            print(f"Error: CSV file '{csv_filename}' not found in {directory}")
            print(f"Available files: {', '.join(f.name for f in csv_files)}")
            sys.exit(1)
    else:
        # No filename specified, prompt user
        selected_file = _prompt_file_selection(csv_files)

    print(f"Selected: {selected_file}")
    return _read_hostnames_from_file(selected_file)


def search_list_objects(access_token: str,
                        selected_clusters: list[str],
                        csv_data: str,
                        filter_obj_type: str = None,
                        is_relic: bool = False,
                        is_nas_share_stale: bool = False) -> list[ProtectedObject]:
    objects = data_parser.get_all_protected_objects(
        access_token = access_token, 
        selected_clusters = selected_clusters, 
        csv_data = csv_data, 
        filter_object_type = filter_obj_type, 
        is_relic = is_relic, 
        is_nas_share_stale = is_nas_share_stale
    )

    return objects


def prompt_and_execute_snapshots(access_token: str, protected_objects: list[ProtectedObject]) -> dict | None:
    """
    Prompt user if they want to take on-demand snapshots and execute if confirmed.
    Objects without a valid SLA ID (UNPROTECTED or DO_NOT_PROTECT) are excluded.
    
    Args:
        access_token: RSC API access token
        protected_objects: List of protected objects to snapshot
        
    Returns:
        Dictionary with snapshot results or None if user declines
    """
    if not protected_objects:
        print("No objects available to snapshot.")
        return None
    
    # Separate objects with and without valid SLA IDs
    objects_with_sla = [obj for obj in protected_objects 
                        if obj.sla_id and obj.sla_id.upper() not in ["UNPROTECTED", "DO_NOT_PROTECT"]]
    objects_without_sla = [obj for obj in protected_objects 
                           if not obj.sla_id or obj.sla_id.upper() in ["UNPROTECTED", "DO_NOT_PROTECT"]]
    
    if not objects_with_sla:
        print("\nNo objects with valid SLA assignments found.")
        if objects_without_sla:
            print(f"Note: {len(objects_without_sla)} objects are marked as UNPROTECTED or DO_NOT_PROTECT and will be skipped.")
        return None
    
    # Display summary
    print(f"\n{'='*60}")
    print("Snapshot Eligibility Summary")
    print(f"{'='*60}")
    print(f"Objects with valid SLA: {len(objects_with_sla)}")
    if objects_without_sla:
        print(f"Objects to skip (UNPROTECTED/DO_NOT_PROTECT): {len(objects_without_sla)}")
    print(f"{'='*60}\n")
    
    response = input("Do you want to take on-demand snapshots for objects with valid SLA? (yes/no): ").strip().lower()
    
    if response not in ["yes", "y"]:
        print("Snapshot operation cancelled.")
        return None
    
    print("\nExecuting on-demand snapshots...")
    try:
        results = execute_on_demand_snapshots(access_token, objects_with_sla)
        
        # Print summary
        total_objects = sum(len(r) for r in results.values())
        successful = sum(1 for r_list in results.values() for r in r_list if r.status == "success")
        failed = sum(1 for r_list in results.values() for r in r_list if r.status == "failed")
        
        print(f"\n{'='*60}")
        print(f"Snapshot Execution Summary")
        print(f"{'='*60}")
        print(f"Total Objects Processed: {total_objects}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Number of SLA Groups: {len(results)}")
        if objects_without_sla:
            print(f"Objects Skipped (No Valid SLA): {len(objects_without_sla)}")
        
        # Print details per SLA
        for sla_id, result_list in results.items():
            successful_in_sla = sum(1 for r in result_list if r.status == "success")
            failed_in_sla = sum(1 for r in result_list if r.status == "failed")
            sla_name = result_list[0].sla_name if result_list else "Unknown"
            print(f"\nSLA: {sla_name} ({sla_id})")
            print(f"  ✓ Successful: {successful_in_sla}, ✗ Failed: {failed_in_sla}")
            
            # Print failed objects details
            for result in result_list:
                if result.status == "failed" and result.error:
                    print(f"    - {result.object_name}: {result.error}")
        
        print(f"\n{'='*60}")
        
        return results
    
    except Exception as e:
        print(f"Error executing snapshots: {str(e)}")
        logger.exception("Failed to execute snapshots")
        return None

