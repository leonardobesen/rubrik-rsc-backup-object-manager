import connection.connect as connect
import file_manager.write_to_file as write_to_file
import configuration.configuration as config
from controller import controller
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    # Establish connection with Rubrik RSC
    rsc_access_token = connect.open_session()

    # User Menus
    selected_clusters, object_types, is_relic, is_share_stale = controller.show_menu(rsc_access_token)
    csv_data = controller.parse_csv_files()

    print("Collecting Data...")
    objects_info = controller.search_list_objects(
        access_token = rsc_access_token,
        selected_clusters = selected_clusters,
        csv_data = csv_data,
        filter_obj_type = object_types,
        is_relic = is_relic,
        is_nas_share_stale = is_share_stale
    )

    print("Writing to file...")
    file_path = write_to_file.generate_report(
        report_name="Backup_Objects",
        objs=objects_info
    )

    print(f"Saved to file {file_path}")

    # Close session
    connect.close_session(rsc_access_token)
