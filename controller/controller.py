import logging
import os
import sys
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
    list_relic = input("Do you want to list relic objects? (yes/no): ").strip().lower()
    is_relic = list_relic in ["yes", "y"]

    # If NasShare is selected, ask about stale NAS shares
    is_stale_nas = None
    if filter_object_type == "NasShare":
        list_stale = input("Do you want to list stale NAS shares? (yes/no): ").strip().lower()
        is_stale_nas = list_stale in ["yes", "y"]

    return selected_ids, filter_object_type, is_relic, is_stale_nas


def parse_csv_files():
    # Ensure the directory exists
    directory = conf.report_input_path()

    if not os.path.isdir(directory):
        print(f"Directory does not exist: {directory}")
        sys.exit(1)

    # List all .csv files
    csv_files = [f for f in os.listdir(
        directory) if f.lower().endswith('.csv')]

    if not csv_files:
        print(f"No CSV files found in: {directory}")
        sys.exit(1)

    print("Select a CSV file to use:")
    for idx, filename in enumerate(csv_files):
        print(f"{idx + 1}. {filename}")

    try:
        selection = int(input("Your choice: ")) - 1
        if selection < 0 or selection >= len(csv_files):
            print("Invalid selection.")
            sys.exit(1)
    except ValueError:
        print("Invalid input. Please enter a number.")
        sys.exit(1)

    selected_file = os.path.join(directory, csv_files[selection])
    print(f"You selected: {selected_file}")

    # Read file line-by-line as hostnames
    try:
        with open(selected_file, mode='r', encoding='utf-8') as f:
            hostnames = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Failed to read CSV file: {e}")
        sys.exit(1)

    return hostnames


def search_list_objects(access_token: str,
                        selected_clusters: list[str],
                        csv_data: str,
                        filter_obj_type: str = None,
                        is_relic: bool = False,
                        is_nas_share_stale: bool = None) -> list[ProtectedObject]:
    objects = data_parser.get_all_protected_objects(
        access_token, selected_clusters, csv_data, filter_obj_type, is_relic, is_nas_share_stale
    )

    return objects
