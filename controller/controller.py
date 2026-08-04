import logging
import re
import sys
from pathlib import Path
import configuration.configuration as conf
from model.protected_object import ProtectedObject
import data.data_parser as data_parser

logger = logging.getLogger(__name__)


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
    print("Select a CSV file to use:")
    for idx, path in enumerate(csv_files, start=1):
        print(f"{idx}. {path.name}")

    try:
        selection = int(input("Your choice: ")) - 1
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


def parse_csv_files():
    directory = Path(conf.report_input_path())

    if not directory.is_dir():
        print(f"Directory does not exist: {directory}")
        sys.exit(1)

    csv_files = sorted(directory.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in: {directory}")
        sys.exit(1)

    selected_file = _prompt_file_selection(csv_files)
    print(f"You selected: {selected_file}")

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
