"""
Realistic Epidemiological Outbreak Linelist and OCHA COD-AB P-Code Reference Generator.
"""

import os
import random
import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


def generate_ocha_pcode_reference_nigeria() -> pd.DataFrame:
    """
    Generates standard OCHA COD-AB style P-Code reference dataset for Borno & Yobe states (Nigeria).
    Includes Admin1 (State), Admin2 (LGA), Admin3 (Ward), and Locality/Settlement levels with coordinates.
    """
    data = [
        # Maiduguri LGA
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Maiduguri", "Admin2_Pcode": "NG008018", "Admin3_Name": "Bolori I", "Admin3_Pcode": "NG008018001", "Locality_Name": "Custom House IDP Camp", "Locality_Pcode": "NG008018001001", "Latitude": 11.8333, "Longitude": 13.1500},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Maiduguri", "Admin2_Pcode": "NG008018", "Admin3_Name": "Bolori II", "Admin3_Pcode": "NG008018002", "Locality_Name": "El-Miskin Camp", "Locality_Pcode": "NG008018002001", "Latitude": 11.8450, "Longitude": 13.1620},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Maiduguri", "Admin2_Pcode": "NG008018", "Admin3_Name": "Gwange I", "Admin3_Pcode": "NG008018003", "Locality_Name": "Gwange Central", "Locality_Pcode": "NG008018003001", "Latitude": 11.8210, "Longitude": 13.1780},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Maiduguri", "Admin2_Pcode": "NG008018", "Admin3_Name": "Gwange II", "Admin3_Pcode": "NG008018004", "Locality_Name": "Stadium Camp", "Locality_Pcode": "NG008018004001", "Latitude": 11.8290, "Longitude": 13.1850},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Maiduguri", "Admin2_Pcode": "NG008018", "Admin3_Name": "Maisandari", "Admin3_Pcode": "NG008018005", "Locality_Name": "Bakasi Camp", "Locality_Pcode": "NG008018005001", "Latitude": 11.8100, "Longitude": 13.1200},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Maiduguri", "Admin2_Pcode": "NG008018", "Admin3_Name": "Shehuri North", "Admin3_Pcode": "NG008018006", "Locality_Name": "Monday Market Community", "Locality_Pcode": "NG008018006001", "Latitude": 11.8390, "Longitude": 13.1490},

        # Jere LGA
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Jere", "Admin2_Pcode": "NG008013", "Admin3_Name": "Muna", "Admin3_Pcode": "NG008013001", "Locality_Name": "Muna Garage IDP Camp", "Locality_Pcode": "NG008013001001", "Latitude": 11.8680, "Longitude": 13.2200},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Jere", "Admin2_Pcode": "NG008013", "Admin3_Name": "Muna", "Admin3_Pcode": "NG008013001", "Locality_Name": "Muna Da'alti", "Locality_Pcode": "NG008013001002", "Latitude": 11.8720, "Longitude": 13.2250},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Jere", "Admin2_Pcode": "NG008013", "Admin3_Name": "Mashamari", "Admin3_Pcode": "NG008013002", "Locality_Name": "Farm Center Camp", "Locality_Pcode": "NG008013002001", "Latitude": 11.8540, "Longitude": 13.1900},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Jere", "Admin2_Pcode": "NG008013", "Admin3_Name": "Dusuman", "Admin3_Pcode": "NG008013003", "Locality_Name": "Dusuman Village", "Locality_Pcode": "NG008013003001", "Latitude": 11.9100, "Longitude": 13.2400},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Jere", "Admin2_Pcode": "NG008013", "Admin3_Name": "Galtimari", "Admin3_Pcode": "NG008013004", "Locality_Name": "Galtimari Settlement", "Locality_Pcode": "NG008013004001", "Latitude": 11.8020, "Longitude": 13.1890},

        # Konduga LGA
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Konduga", "Admin2_Pcode": "NG008015", "Admin3_Name": "Konduga Central", "Admin3_Pcode": "NG008015001", "Locality_Name": "Konduga General Clinic", "Locality_Pcode": "NG008015001001", "Latitude": 11.6500, "Longitude": 13.4180},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Konduga", "Admin2_Pcode": "NG008015", "Admin3_Name": "Dalori", "Admin3_Pcode": "NG008015002", "Locality_Name": "Dalori I IDP Camp", "Locality_Pcode": "NG008015002001", "Latitude": 11.7800, "Longitude": 13.2600},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Konduga", "Admin2_Pcode": "NG008015", "Admin3_Name": "Dalori", "Admin3_Pcode": "NG008015002", "Locality_Name": "Dalori II IDP Camp", "Locality_Pcode": "NG008015002002", "Latitude": 11.7850, "Longitude": 13.2680},

        # Gwoza LGA
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Gwoza", "Admin2_Pcode": "NG008010", "Admin3_Name": "Gwoza Town", "Admin3_Pcode": "NG008010001", "Locality_Name": "Gwoza Transit Camp", "Locality_Pcode": "NG008010001001", "Latitude": 11.0833, "Longitude": 13.6944},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Gwoza", "Admin2_Pcode": "NG008010", "Admin3_Name": "Pulka", "Admin3_Pcode": "NG008010002", "Locality_Name": "Pulka Camp IV", "Locality_Pcode": "NG008010002001", "Latitude": 11.2200, "Longitude": 13.7800},

        # Bama LGA
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Bama", "Admin2_Pcode": "NG008003", "Admin3_Name": "Shehuri Bama", "Admin3_Pcode": "NG008003001", "Locality_Name": "Bama GSSS Camp", "Locality_Pcode": "NG008003001001", "Latitude": 11.5200, "Longitude": 13.6800},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Bama", "Admin2_Pcode": "NG008003", "Admin3_Name": "Kasugula", "Admin3_Pcode": "NG008003002", "Locality_Name": "Kasugula IDP Camp", "Locality_Pcode": "NG008003002001", "Latitude": 11.5150, "Longitude": 13.6900},

        # Monguno LGA
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Monguno", "Admin2_Pcode": "NG008021", "Admin3_Name": "Monguno Town", "Admin3_Pcode": "NG008021001", "Locality_Name": "Waterboard Camp", "Locality_Pcode": "NG008021001001", "Latitude": 12.6700, "Longitude": 13.6100},
        {"Admin1_Name": "Borno", "Admin1_Pcode": "NG008", "Admin2_Name": "Monguno", "Admin2_Pcode": "NG008021", "Admin3_Name": "Monguno Town", "Admin3_Pcode": "NG008021001", "Locality_Name": "GSSS Monguno Camp", "Locality_Pcode": "NG008021001002", "Latitude": 12.6750, "Longitude": 13.6150},

        # Damaturu LGA (Yobe State)
        {"Admin1_Name": "Yobe", "Admin1_Pcode": "NG036", "Admin2_Name": "Damaturu", "Admin2_Pcode": "NG036006", "Admin3_Name": "Damaturu Central", "Admin3_Pcode": "NG036006001", "Locality_Name": "Kukumare Settlement", "Locality_Pcode": "NG036006001001", "Latitude": 11.7470, "Longitude": 11.9610},
        {"Admin1_Name": "Yobe", "Admin1_Pcode": "NG036", "Admin2_Name": "Damaturu", "Admin2_Pcode": "NG036006", "Admin3_Name": "Maisandari Damaturu", "Admin3_Pcode": "NG036006002", "Locality_Name": "Nayakare Community", "Locality_Pcode": "NG036006002001", "Latitude": 11.7550, "Longitude": 11.9700},
        {"Admin1_Name": "Yobe", "Admin1_Pcode": "NG036", "Admin2_Name": "Potiskum", "Admin2_Pcode": "NG036014", "Admin3_Name": "Bolewa A", "Admin3_Pcode": "NG036014001", "Locality_Name": "Potiskum General Area", "Locality_Pcode": "NG036014001001", "Latitude": 11.7100, "Longitude": 11.0700},
    ]
    return pd.DataFrame(data)


def generate_cholera_borno_linelist(n_cases: int = 180, seed: int = 42) -> pd.DataFrame:
    """
    Generates realistic field cholera outbreak linelist with spelling errors on localities/LGAs
    specifically designed to test the 5-level spatial fallback cascade and WHO EpiWeeks.
    """
    random.seed(seed)
    np.random.seed(seed)

    base_date = datetime.date(2023, 8, 10)
    first_names_m = ["Ibrahim", "Musa", "Abubakar", "Aliyu", "Usman", "Mohammed", "Sani", "Mustapha", "Bukar"]
    first_names_f = ["Fatima", "Aisha", "Hauwa", "Maryam", "Zainab", "Hadiza", "Khadija", "Halima", "Bintu"]
    last_names = ["Katsina", "Gana", "Modu", "Bukar", "Kyari", "Goni", "Shettima", "Grema", "Lawal", "Garba"]

    rows = []
    for i in range(1, n_cases + 1):
        is_female = random.random() < 0.51
        first = random.choice(first_names_f if is_female else first_names_m)
        last = random.choice(last_names)
        full_name = f"{first} {last}"
        sex_raw = random.choice(["F", "f", "Female", "2", "FEMALE"] if is_female else ["M", "m", "Male", "1", "MALE"])

        # Age
        age_rnd = random.random()
        if age_rnd < 0.25:
            age_raw = f"{random.randint(6, 48)} mos"
        elif age_rnd < 0.35:
            age_raw = f"{random.randint(10, 28)}d"
        elif age_rnd < 0.90:
            age_raw = str(random.randint(5, 75))
        else:
            age_raw = random.choice(["NA", "-99", "unknown"])

        # Dates
        day_offset = random.randint(0, 50)
        d_onset = base_date + datetime.timedelta(days=day_offset)
        d_admit = d_onset + datetime.timedelta(days=random.choice([0, 1, 2]))

        # Dates in messy formats
        date_styles = [
            d_admit.strftime("%d/%m/%Y"),
            d_admit.strftime("%Y-%m-%d"),
            d_admit.strftime("%d-%b-%Y"),
            d_admit.strftime("%d/%m/%y"),
            str((d_admit - datetime.date(1899, 12, 30)).days) if random.random() < 0.1 else d_admit.strftime("%d/%m/%Y")
        ]
        d_admit_str = random.choice(date_styles)

        # Spatial scenario
        spatial_tier = random.random()

        if spatial_tier < 0.35:
            locality = random.choice(["Custom House IDP Camp", "Muna Garage IDP Camp", "Bakasi Camp", "Stadium Camp", "Dalori I IDP Camp", "Waterboard Camp"])
            ward = "Bolori I"
            lga = "Maiduguri"
            state = "Borno"
        elif spatial_tier < 0.60:
            locality = random.choice([
                "Muna IDP Camp", "Customs House Camp", "Bakassi Camp", "El Miskin settlement",
                "Dalori 1 Camp", "Farm Cntr IDP", "Gwoza Transit", "Kukumare village"
            ])
            ward = random.choice(["Muna", "Bolori 1", "Maisandari", "Dalori"])
            lga = random.choice(["Jerre", "Maidugury", "Konduga", "Gwoza"])
            state = "Borno"
        elif spatial_tier < 0.75:
            locality = random.choice(["", "N/A", "Unknown", "-", "Village near river"])
            ward = random.choice(["Gwange I", "Gwange II", "Bolori II", "Dusuman", "Dalori", "Bolewa A"])
            lga = random.choice(["Maiduguri", "Jere", "Konduga", "Potiskum"])
            state = random.choice(["Borno", "Yobe"])
        elif spatial_tier < 0.90:
            locality = ""
            ward = "N/A"
            lga = random.choice(["Maiduguri LGA", "Jere District", "Kondoga", "Bama LGA", "Monguno", "Damaturu"])
            state = "Borno State"
        elif spatial_tier < 0.95:
            locality = None
            ward = None
            lga = "Unspecified LGA"
            state = random.choice(["Borno State", "Yobe Province", "Adamawa Region"])
        else:
            locality = "Camp X Outside Border"
            ward = "Zone 99"
            lga = "Unknown Area"
            state = "Foreign Territory"

        outcome_rnd = random.random()
        if outcome_rnd < 0.03:
            outcome = random.choice(["Died", "Dead", "Deceased", "DCD"])
        elif outcome_rnd < 0.85:
            outcome = random.choice(["Discharged", "Recovered", "Cured", "Alive"])
        else:
            outcome = random.choice(["LAMA", "Transferred", "Active"])

        row = {
            "Patient_ID": f"CHO-BOR-{2023}-{i:04d}",
            "Patient_Name": full_name,
            "Gender": sex_raw,
            "Patient_Age": age_raw,
            "Admission_Date": d_admit_str,
            "State_Province": state,
            "LGA_District": lga,
            "Ward_SubDistrict": ward,
            "Locality_Village": locality,
            "Severe_Dehydration": random.choice(["Yes", "1", "Oui", "No", "0"]),
            "Vomiting": random.choice(["Yes", "1", "true", "No", "0"]),
            "Watery_Diarrhea": "Yes",
            "RDT_Cholera": random.choice(["Positive", "Pos", "Negative", "Inconclusive"]),
            "Clinical_Outcome": outcome,
            "Case_Classification": random.choice(["Confirmed", "Probable", "Suspect"])
        }
        rows.append(row)

    return pd.DataFrame(rows)


def generate_cholera_linelist(n_cases: int = 150, seed: int = 42) -> pd.DataFrame:
    """Generates realistic messy cholera outbreak linelist (Kivu/Haiti-style)."""
    random.seed(seed)
    np.random.seed(seed)

    base_date = datetime.date(2023, 8, 1)
    facilities = ["Hopital General de Reference", "Centre de Sante Kyeshero", "CSB Majengo", "CTC Birere", "Hopital provincial du Nord-Kivu"]
    districts = ["Goma", "Karisimbi", "Nyiragongo", "Masisi"]
    first_names_m = ["Jean", "Pierre", "Michel", "Pascal", "Emmanuel", "David", "Claude", "Moise", "Alain"]
    first_names_f = ["Marie", "Jeanne", "Aline", "Chantal", "Esperance", "Dorcas", "Neema", "Bahati"]
    last_names = ["Kambale", "Muhindo", "Kakule", "Paluku", "Kasereka", "Kavira", "Masika", "Kahindo", "Mumbere"]

    rows = []
    for i in range(1, n_cases + 1):
        is_female = random.random() < 0.52
        sex_raw = random.choice(["F", "f", "Femme", "Female", "2", "FEMININ"] if is_female else ["M", "m", "Homme", "Male", "1", "MASCULIN"])
        first = random.choice(first_names_f if is_female else first_names_m)
        last = random.choice(last_names)
        full_name = f"{first} {last}"

        age_type = random.choice(["years", "months", "days", "str_y"])
        if age_type == "months":
            age_raw = f"{random.randint(2, 23)} mois"
        elif age_type == "days":
            age_raw = f"{random.randint(10, 28)} jours"
        elif age_type == "str_y":
            age_raw = f"{random.randint(2, 75)} ans"
        else:
            age_raw = random.choice([str(random.randint(1, 80)), "NA", "-99", "inconnu"])

        day_offset = random.randint(0, 45)
        d_onset = base_date + datetime.timedelta(days=day_offset)
        d_consult = d_onset + datetime.timedelta(days=random.choice([0, 0, 1, 1, 2, 3]))
        d_admit = d_consult if random.random() < 0.85 else None
        
        outcome_rand = random.random()
        if outcome_rand < 0.04:
            outcome_raw = random.choice(["DCD", "Decede", "Mort", "Dead", "décédé"])
            d_discharge = None
            d_death = (d_admit or d_consult) + datetime.timedelta(days=random.randint(0, 3))
        elif outcome_rand < 0.88:
            outcome_raw = random.choice(["Gueri", "Guérie", "Recovered", "Sortie", "Discharged", "gueri"])
            d_discharge = (d_admit or d_consult) + datetime.timedelta(days=random.randint(1, 5))
            d_death = None
        else:
            outcome_raw = random.choice(["Evade", "LAMA", "Transfere", "En cours", "NA"])
            d_discharge = None
            d_death = None

        def format_messy_date(d):
            if d is None:
                return random.choice(["", "NA", "null", "-", ""])
            style = random.choice(["iso", "dmy_slash", "dmy_dash", "text_fr", "excel_num"])
            if style == "iso":
                return d.strftime("%Y-%m-%d")
            elif style == "dmy_slash":
                return d.strftime("%d/%m/%Y")
            elif style == "dmy_dash":
                return d.strftime("%d-%m-%Y")
            elif style == "text_fr":
                months_fr = ["janv", "fevr", "mars", "avr", "mai", "juin", "juil", "aout", "sept", "oct", "nov", "dec"]
                return f"{d.day} {months_fr[d.month-1]} {d.year}"
            elif style == "excel_num":
                return str((d - datetime.date(1899, 12, 30)).days)

        classif = random.choice(["Confirme", "CONF", "PCR+", "Probable", "Suspect", "SUSP", "Non-cas"])

        if random.random() < 0.06:
            d_consult_str = format_messy_date(d_onset - datetime.timedelta(days=5))
        else:
            d_consult_str = format_messy_date(d_consult)

        row = {
            "ID_Patient": f"CHO-2023-{i:04d}",
            "Nom_et_Prenom": full_name,
            "Sexe": sex_raw,
            "Age": age_raw,
            "Zone_de_Sante": random.choice(districts),
            "Structure_Sante": random.choice(facilities),
            "Date_Debut_Symptomes": format_messy_date(d_onset),
            "Date_Consultation": d_consult_str,
            "Date_Admission_CTC": format_messy_date(d_admit),
            "Date_Sortie": format_messy_date(d_discharge),
            "Date_Deces": format_messy_date(d_death),
            "Diarrhee_Aqueuse": random.choice(["Oui", "O", "1", "yes", "true", "+"]),
            "Vomissements": random.choice(["Oui", "Non", "1", "0", "O", "N", "NA"]),
            "Deshydratation_Severe": random.choice(["Oui", "Non", "O", "N", "1", "0"]),
            "Statut_Vaccinal_OCV": random.choice(["1 dose", "2 doses", "Non", "0", "Inconnu", "NA"]),
            "Classification_Finale": classif,
            "Issue_Clinique": outcome_raw,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    dup_row = df.iloc[5].to_dict()
    df.loc[len(df)] = dup_row
    dup_fuzzy = df.iloc[12].to_dict()
    dup_fuzzy["ID_Patient"] = f"CHO-2023-9991"
    dup_fuzzy["Nom_et_Prenom"] = dup_fuzzy["Nom_et_Prenom"] + " Jr"
    df.loc[len(df)] = dup_fuzzy

    return df


def generate_covid19_linelist(n_cases: int = 120, seed: int = 101) -> pd.DataFrame:
    """Generates realistic messy COVID-19 surveillance linelist."""
    random.seed(seed)
    np.random.seed(seed)

    base_date = datetime.date(2022, 1, 15)
    provinces = ["Metro Region", "Northern District", "Coast Valley", "Eastern Highlands"]
    facilities = ["City Memorial Hospital", "St. Jude Medical Center", "North Clinic", "Community Health Center"]

    rows = []
    for i in range(1, n_cases + 1):
        is_female = random.random() < 0.50
        sex_raw = random.choice(["Female", "F", "f", "woman", "2"] if is_female else ["Male", "M", "m", "man", "1"])
        age_raw = random.choice([str(random.randint(1, 95)), f"{random.randint(18, 85)} yo", "6 mos", "NA", "999"])

        d_onset = base_date + datetime.timedelta(days=random.randint(0, 60))
        d_sample = d_onset + datetime.timedelta(days=random.choice([0, 1, 2, 3]))
        d_result = d_sample + datetime.timedelta(days=random.choice([1, 2, 4]))
        is_hosp = random.random() < 0.25
        d_admit = d_onset + datetime.timedelta(days=random.randint(2, 6)) if is_hosp else None
        
        outcome_rand = random.random()
        if outcome_rand < 0.08:
            outcome_raw = random.choice(["Died", "Dead", "Deceased", "death"])
            d_death = (d_admit or d_onset) + datetime.timedelta(days=random.randint(3, 14))
            d_disc = None
        elif is_hosp:
            outcome_raw = random.choice(["Discharged", "Recovered", "Alive"])
            d_disc = d_admit + datetime.timedelta(days=random.randint(3, 12))
            d_death = None
        else:
            outcome_raw = random.choice(["Recovered", "Active", "Alive", "Home Isolation"])
            d_disc = None
            d_death = None

        def fmt_date(d):
            if d is None:
                return random.choice(["", "N/A", "null", "."])
            fmt = random.choice(["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%b-%Y"])
            return d.strftime(fmt)

        row = {
            "case_id": f"COV-{2022}-{i:05d}",
            "patient_name": f"Patient_{i}",
            "gender": sex_raw,
            "patient_age": age_raw,
            "province": random.choice(provinces),
            "reporting_facility": random.choice(facilities),
            "symptom_onset_date": fmt_date(d_onset),
            "specimen_collection_date": fmt_date(d_sample),
            "lab_result_date": fmt_date(d_result),
            "rt_pcr_result": random.choice(["Positive", "PCR+", "Pos", "Negative", "Inconclusive"]),
            "hospitalized_yn": "Yes" if is_hosp else random.choice(["No", "0", "false", "N"]),
            "admission_date": fmt_date(d_admit),
            "discharge_date": fmt_date(d_disc),
            "death_date": fmt_date(d_death),
            "fever": random.choice(["Yes", "1", "true", "No", "0"]),
            "cough": random.choice(["Yes", "1", "true", "No", "0"]),
            "vaccine_doses": random.choice(["0", "1", "2", "3", "Booster", "Unvaccinated", "unknown"]),
            "final_outcome": outcome_raw,
            "case_status": random.choice(["Confirmed", "Probable", "Suspect"])
        }
        rows.append(row)

    return pd.DataFrame(rows)


def generate_ebola_linelist(n_cases: int = 100, seed: int = 777) -> pd.DataFrame:
    """Generates realistic messy Ebola Virus Disease (EVD) linelist."""
    random.seed(seed)
    np.random.seed(seed)

    base_date = datetime.date(2021, 5, 10)
    villages = ["Bikoro Center", "Ikoko Impenge", "Wangata", "Mbandaka Ville", "Bolenge"]
    etcs = ["ETC Bikoro - MSF", "ETC Wangata", "CTE General Hospital", "Isolation Ward 2"]

    rows = []
    for i in range(1, n_cases + 1):
        is_female = random.random() < 0.48
        sex_raw = random.choice(["M", "Male", "homme", "1"] if not is_female else ["F", "Female", "femme", "2"])
        age_raw = random.choice([str(random.randint(2, 70)), f"{random.randint(1, 11)}m", "NA"])

        d_onset = base_date + datetime.timedelta(days=random.randint(0, 40))
        d_admit = d_onset + datetime.timedelta(days=random.choice([1, 2, 3, 4]))
        
        is_death = random.random() < 0.45
        if is_death:
            outcome_raw = random.choice(["Dead", "Decede", "Mort", "DCD"])
            d_death = d_admit + datetime.timedelta(days=random.randint(1, 7))
            d_disc = None
        else:
            outcome_raw = random.choice(["Cured", "Gueri", "Discharged", "Survivor"])
            d_disc = d_admit + datetime.timedelta(days=random.randint(10, 25))
            d_death = None

        def fmt_date(d):
            if d is None:
                return ""
            return d.strftime(random.choice(["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]))

        row = {
            "num_cas_ebola": f"EVD-2021-{i:03d}",
            "nom_prenom": f"Subject_{i}",
            "sexe": sex_raw,
            "age": age_raw,
            "village_origine": random.choice(villages),
            "centre_traitement": random.choice(etcs),
            "date_debut": fmt_date(d_onset),
            "date_admission": fmt_date(d_admit),
            "date_sortie": fmt_date(d_disc),
            "date_deces": fmt_date(d_death),
            "fievre_hemorragique": random.choice(["Oui", "1", "O", "Non", "0"]),
            "saignement_inexplique": random.choice(["Oui", "Non", "1", "0", "NA"]),
            "contact_avec_cas_confirme": random.choice(["Oui", "Non", "Inconnu"]),
            "statut_cas": random.choice(["Confirme", "Probable", "Suspect"]),
            "issue": outcome_raw
        }
        rows.append(row)

    return pd.DataFrame(rows)


def generate_measles_linelist(n_cases: int = 100, seed: int = 555) -> pd.DataFrame:
    """Generates realistic messy measles pediatric linelist."""
    random.seed(seed)
    np.random.seed(seed)

    base_date = datetime.date(2023, 3, 1)
    districts = ["District Nord", "District Sud", "District Est", "District Ouest"]

    rows = []
    for i in range(1, n_cases + 1):
        is_female = random.random() < 0.50
        sex_raw = random.choice(["F", "Female", "fille"] if is_female else ["M", "Male", "garcon"])
        
        if random.random() < 0.60:
            age_raw = f"{random.randint(3, 59)} mois"
        else:
            age_raw = f"{random.randint(5, 14)} ans"

        d_rash = base_date + datetime.timedelta(days=random.randint(0, 50))
        d_consult = d_rash + datetime.timedelta(days=random.choice([0, 1, 2, 3]))

        row = {
            "ID_Epid": f"MEA-2023-{i:04d}",
            "Nom_Enfant": f"Child_{i}",
            "Sexe": sex_raw,
            "Age": age_raw,
            "District": random.choice(districts),
            "Date_Debut_Eruption": d_rash.strftime("%d/%m/%Y"),
            "Date_Notification": d_consult.strftime("%Y-%m-%d"),
            "Fievre": random.choice(["Oui", "1", "O", "Yes"]),
            "Eruption_Cutanee": "Oui",
            "Toux": random.choice(["Oui", "Non", "O", "N"]),
            "Conjonctivite": random.choice(["Oui", "Non", "NA", "0"]),
            "Vaccine_Rougeole": random.choice(["0 dose", "1 dose", "2 doses", "Inconnu"]),
            "Statut": random.choice(["Confirme", "Epidemiologiquement lie", "Suspect", "Descarte"]),
            "Evolution": random.choice(["Gueri", "Gueri", "Gueri", "Decede", "Inconnu"])
        }
        rows.append(row)

    return pd.DataFrame(rows)


def save_all_sample_datasets():
    """Generates and writes all sample datasets to disk."""
    dataset_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(dataset_dir, exist_ok=True)

    df_pcode_ng = generate_ocha_pcode_reference_nigeria()
    df_pcode_ng.to_csv(os.path.join(dataset_dir, "ocha_pcode_reference_nigeria.csv"), index=False)

    df_borno_cholera = generate_cholera_borno_linelist(180, seed=42)
    df_borno_cholera.to_csv(os.path.join(dataset_dir, "cholera_borno_field_linelist.csv"), index=False)

    df_cholera = generate_cholera_linelist(150, seed=42)
    df_cholera.to_csv(os.path.join(dataset_dir, "cholera_outbreak_messy.csv"), index=False)

    df_covid = generate_covid19_linelist(120, seed=101)
    df_covid.to_csv(os.path.join(dataset_dir, "covid19_surveillance_messy.csv"), index=False)

    df_ebola = generate_ebola_linelist(100, seed=777)
    df_ebola.to_csv(os.path.join(dataset_dir, "ebola_evd_messy.csv"), index=False)

    df_measles = generate_measles_linelist(100, seed=555)
    df_measles.to_csv(os.path.join(dataset_dir, "measles_outbreak_messy.csv"), index=False)


if __name__ == "__main__":
    save_all_sample_datasets()
