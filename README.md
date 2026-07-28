# rubrik-rsc-search-for-protected-objects

A small utility that searches Rubrik Security Cloud (RSC) protected objects (Physical Host, Volume Group, Oracle, SQL Server, Filesets, etc.) for a list of hostnames and exports matching results to CSV reports.

**Highlights**
- Search RSC for multiple protected-object types
- Load hostnames from simple CSV files
- Configurable via `configuration/config.json`
- Outputs CSV reports to `reports/`

**Prerequisites**
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

Configuration
-------------
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

Input hostnames
---------------
Place one or more CSV files containing hostnames (single column, no header) in `reports/input/`. Example file contents:

```
hostname1
hostname2
hostname3
```

Usage
-----
Run the main script from the repository root:

```bash
python main.py
```

By default the script will read CSV files from `reports/input/`, query RSC, and write results to `reports/` as CSV files.

Output
------
Generated CSV reports are placed in the `reports/` folder. Filenames include timestamps so multiple runs don't overwrite previous results.

Troubleshooting
---------------
- If you see authentication errors, verify `configuration/config.json` values and that the service account has the correct permissions.
- Network or DNS errors usually mean the machine running the script cannot reach your RSC tenant—check routing and firewall rules.
- If dependencies fail to install, ensure your Python version is compatible and that `pip` is current (`pip install --upgrade pip`).

Contributing
------------
Pull requests are welcome. If you add features, please include tests and update this README with usage examples.

License
-------
See the `LICENSE` file for license information.

---

If you'd like, I can also add a short example `scripts/run_example.sh` or a small CLI wrapper — tell me which you'd prefer.
