# rubrik-rsc-search-for-protected-objects

A utility that searches Rubrik Security Cloud (RSC) protected objects (Physical Host, Volume Group, Oracle, SQL Server, Filesets, etc.) for a list of hostnames and exports matching results to CSV reports. With optional on-demand snapshot capability grouped by SLA ID.

## Highlights

- Search RSC for multiple protected-object types
- Load hostnames from simple CSV files
- Configurable via `configuration/config.json`
- Trigger on-demand snapshots grouped by SLA ID
- Outputs CSV reports to `reports/`
- Command-line argument support for flexible workflows

## Prerequisites

- Python 3.8+ (3.11 recommended)
- Git
- Network access to your Rubrik RSC tenant

Install dependencies:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# or Command Prompt
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Configuration

Copy and edit `configuration/config.json` with credentials for an RSC service account that has permission to query objects. Place the file in the `configuration/` folder.

Example `configuration/config.json`:

```json
{
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "name": "service_account_name",
    "access_token_uri": "https://yourdomain.my.rubrik.com/api/client_token",
    "graphql_url": "https://yourdomain.my.rubrik.com/api/graphql"
}
```

Field notes:

- `client_id`: service account client id
- `client_secret`: service account secret
- `name`: descriptive name for the account
- `access_token_uri` / `graphql_url`: replace `yourdomain` with your RSC tenant domain

## Input Data

### Preparing CSV Files

Place one or more CSV files containing hostnames in the `reports/input/` folder. Each file should contain one hostname per line (no header required):

```csv
hostname1
hostname2
hostname3
```

### File Format
- **Single column** - one hostname per line
- **No header row** - data starts immediately
- **Flexible delimiters** - supports comma, semicolon, or whitespace-separated values on a single line

Example variations that all work:

```csv
# One per line (recommended)
server1
server2
server3
```

```csv
# Comma-separated on single line
server1, server2, server3
```

## Usage

### Basic Usage

Run the script from the repository root:

```bash
python main.py
```

You will be prompted to:
1. Select one or more clusters to search
2. Optionally filter by object type
3. Optionally search for relic objects only
4. Select a CSV file from `reports/input/` (shows file size and modification date)

### Command-Line Usage

Specify a CSV file directly to skip the file selection menu:

```bash
python main.py --input hostname_list.csv
```

**Notes:**
- The CSV filename must match exactly (case-sensitive on Linux/Mac)
- File must be in `reports/input/` folder
- If filename not found, script shows available options and exits

### View Help

```bash
python main.py --help
```

## Workflow

1. **Search Phase**
   - Script connects to RSC
   - Searches for hostnames across selected clusters
   - Optionally filters by object type or relic status
   - Generates `Backup_Objects_[timestamp].csv` in `reports/`

2. **Snapshot Phase** (Optional)
   - Script prompts: "Do you want to take on-demand snapshots?"
   - Groups objects by SLA ID (automatically excludes unprotected objects)
   - For each SLA group, executes `takeOnDemandSnapshot` GraphQL mutation
   - Generates `Snapshot_Results_[timestamp].csv` with results

## Output Reports

### Search Results: `Backup_Objects_[timestamp].csv`

Columns:
- Search Term
- ID (Object ID)
- Name
- Object Type
- SLA ID
- SLA Name
- Location

### Snapshot Results: `Snapshot_Results_[timestamp].csv` (if snapshots executed)

Columns:
- SLA ID
- SLA Name
- Object ID
- Object Name
- Status (`success` / `failed` / `unknown`)
- Taskchain UUID (populated on success)
- Error (populated on failure)

**Note:** Objects without valid SLA assignment (UNPROTECTED, DO_NOT_PROTECT, or empty) are automatically excluded from snapshot operations.

## Troubleshooting

**Authentication errors:**
- Verify `configuration/config.json` values
- Ensure the service account has query permissions in RSC

**CSV file not found errors:**
- Verify files are in `reports/input/` folder
- Check filename spelling (case-sensitive on Linux/Mac)
- Use `python main.py --help` to see usage examples

**Network/DNS errors:**
- Check network connectivity to RSC tenant
- Verify firewall rules allow outbound HTTPS (port 443)
- Confirm `access_token_uri` and `graphql_url` are correct in config

**No objects found:**
- Verify hostnames in CSV file are accurate
- Confirm selected clusters contain these objects
- Check if objects are filtered out by type or relic settings

## License

See the `LICENSE` file for license information.
