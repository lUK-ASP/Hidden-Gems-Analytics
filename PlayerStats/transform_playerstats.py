import pandas as pd
import extract_playerstats

def transform_playerstats(driver,url,file_path,team_name):
    statslist=extract_playerstats.extract_playerstats(driver,url,file_path)
    df = pd.DataFrame(statslist)

    cols_to_drop = list(range(1, 4)) + [7, 10, 11] + list(range(16, 22))

    df = df.drop(df.columns[cols_to_drop], axis=1)
    df.insert(0, "saison", "2025-2026")
    df.insert(1, "team", team_name.lower())
    return df

