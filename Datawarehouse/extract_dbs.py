import sqlite3
import pandas as pd
from google.cloud import bigquery
import io
import time
import os
import json
from google.oauth2 import service_account

def extract_dbs(Dataset_Name,db_path):
# Einstellungen
    SQLITE_DB = db_path
    BQ_PROJECT = "466517016150"
    BQ_DATASET = Dataset_Name
    # Dataset erstellen falls nicht vorhanden

    CREDENTIALS_FILE = "\\Users\\vollm\\Downloads\\business-inteligence-490515-b6c96d4e150a.json"

    # Verbindungen aufbauen
    conn = sqlite3.connect(SQLITE_DB)


    if os.path.exists(r"C:\Users\vollm\Downloads\business-inteligence-490515-b6c96d4e150a.json"):
        client = bigquery.Client.from_service_account_json(
            r"C:\Users\vollm\Downloads\business-inteligence-490515-b6c96d4e150a.json",
            project="business-inteligence-490515"
        )
    else:
        credentials_json = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        client = bigquery.Client(
            credentials=credentials,
            project="business-inteligence-490515"
        )

    dataset_id = f"{BQ_PROJECT}.{BQ_DATASET}"
    dataset = bigquery.Dataset(dataset_id)


    try:
        client.create_dataset(dataset, exists_ok=True)
        print(f"✓ Dataset '{BQ_DATASET}' bereit!")
    except Exception as e:
        print(f"✗ Dataset Fehler: {e}")

    tabellen = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table'",
        conn
    )["name"].tolist()


    def upload_tabelle(client, df, table_id, versuch=1, max_versuche=5):
        try:
            csv_data = df.to_csv(index=False).encode('utf-8')
            csv_buffer = io.BytesIO(csv_data)

            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.CSV,
                skip_leading_rows=1,
                autodetect=True,
                write_disposition="WRITE_TRUNCATE",
                create_disposition="CREATE_IF_NEEDED",
            )

            job = client.load_table_from_file(
                csv_buffer,
                table_id,
                job_config=job_config,
                size=len(csv_data)
            )
            job.result()
            return True

        except Exception as e:
            if versuch < max_versuche:
                wartezeit = versuch * 10  # 10s, 20s, 30s, 40s
                print(f"  ⚠ Versuch {versuch} fehlgeschlagen – warte {wartezeit}s..."+
                      e)
                time.sleep(wartezeit)
                return upload_tabelle(client, df, table_id, versuch + 1, max_versuche)
            else:
                raise e


    for tabelle in tabellen:
        print(f"\nExportiere: {tabelle}...")

        try:
            df = pd.read_sql(f"SELECT * FROM '{tabelle}'", conn)

            # Datentypen bereinigen
            for col in df.columns:
                if df[col].dtype == object:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='raise')
                    except:
                        df[col] = df[col].astype(str).replace('None', '')

            print(f"  → {len(df)} Zeilen, {len(df.columns)} Spalten")

            table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{tabelle}"
            upload_tabelle(client, df, table_id)

            print(f"  ✓ '{tabelle}' erfolgreich importiert!")

        except Exception as e:
            print(f"  ✗ Fehler bei '{tabelle}': {e}")

    conn.close()
    print("\nAlle Tabellen fertig!")
extract_dbs("Spieldateb","../storage_DBs/staging_spiel_daten.db")