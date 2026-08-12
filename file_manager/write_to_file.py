import pandas as pd
import os
from datetime import datetime
from configuration.configuration import get_root_dir
from model.protected_object import ProtectedObject


def _create_empty_file(report_name: str) -> str:
    # Get current datetime formatted
    now = datetime.now().strftime("%d-%m-%Y_%H_%M_%S")
    # CSV file instead of Excel
    file_name = f'{report_name}_{now}.csv'
    report_path = os.path.join(get_root_dir(), 'reports', file_name)

    return report_path


def generate_report(report_name: str, objs: list[ProtectedObject]) -> str:
    report_file = _create_empty_file(report_name)

    # Convert objects to DataFrame
    df = pd.DataFrame([{
        'Search Term': o.search_term,
        'ID': o.id,
        'Name': o.name,
        'Object Type': o.object_type,
        'SLA ID': o.sla_id,
        'SLA Name': o.sla_name,
        'Location': o.location
    } for o in objs])

    # Save as CSV
    df.to_csv(report_file, index=False)

    return report_file
