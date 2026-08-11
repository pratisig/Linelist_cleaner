"""
Standard Epidemiological Variable Dictionary & Synonyms.

Provides standard canonical epidemiological variable names, descriptions, data types,
and common synonyms/aliases across English, French, Spanish, and standard public health surveillance systems.
"""

from typing import Dict, List, Any

# Standard Canonical Variable Tags
CANONICAL_TAGS: Dict[str, Dict[str, Any]] = {
    "case_id": {
        "label": "Case Identifier",
        "description": "Unique identifier for the patient/case record",
        "type": "string",
        "category": "identifier",
        "synonyms": [
            "case_id", "patient_id", "id", "id_patient", "num_cas", "numero_cas",
            "record_id", "subject_id", "subjid", "identifiant", "case_number",
            "case_no", "no_cas", "patient_code", "code_patient", "id_number",
            "id_num", "epid_number", "epid_no", "no_epid", "numero_epid", "cid", "pid"
        ],
    },
    "full_name": {
        "label": "Full Name",
        "description": "Patient's full name or combined first and last names",
        "type": "string",
        "category": "demographic_pii",
        "synonyms": [
            "full_name", "patient_name", "name", "nom_complet", "nom_et_prenom",
            "nom_prenom", "nom", "nombre_completo", "nombre", "client_name", "case_name"
        ],
    },
    "first_name": {
        "label": "First Name",
        "description": "Patient's given or first name",
        "type": "string",
        "category": "demographic_pii",
        "synonyms": [
            "first_name", "firstname", "prenom", "given_name", "primer_nombre", "fname"
        ],
    },
    "last_name": {
        "label": "Last Name",
        "description": "Patient's family name or surname",
        "type": "string",
        "category": "demographic_pii",
        "synonyms": [
            "last_name", "lastname", "nom_famille", "nom_de_famille", "surname",
            "family_name", "apellido", "apellidos", "lname"
        ],
    },
    "age": {
        "label": "Age",
        "description": "Patient's age at onset or consultation",
        "type": "numeric",
        "category": "demographic",
        "synonyms": [
            "age", "age_years", "age_ans", "edad", "patient_age", "age_yr",
            "age_an", "age_patient", "age_in_years", "age_yrs"
        ],
    },
    "age_unit": {
        "label": "Age Unit",
        "description": "Unit of measurement for age (Years, Months, Days)",
        "type": "categorical",
        "category": "demographic",
        "synonyms": [
            "age_unit", "age_units", "unite_age", "unite_d_age", "unidad_edad",
            "age_type", "unit_age", "unite"
        ],
    },
    "date_birth": {
        "label": "Date of Birth",
        "description": "Patient's birth date",
        "type": "date",
        "category": "demographic",
        "synonyms": [
            "date_birth", "dob", "birth_date", "date_naissance", "date_de_naissance",
            "fecha_nacimiento", "birthdate", "dt_birth", "d_o_b", "ddn"
        ],
    },
    "sex": {
        "label": "Sex / Gender",
        "description": "Biological sex or gender of patient",
        "type": "categorical",
        "category": "demographic",
        "synonyms": [
            "sex", "gender", "sexe", "genre", "sexo", "gender_code", "sexe_patient"
        ],
    },
    "date_onset": {
        "label": "Date of Symptom Onset",
        "description": "Date when the patient first experienced symptoms",
        "type": "date",
        "category": "timeline",
        "synonyms": [
            "date_onset", "onset_date", "date_debut", "date_debut_symptomes",
            "date_of_onset", "symptom_onset", "date_symptomes", "fecha_inicio",
            "fecha_inicio_sintomas", "dt_onset", "onset", "date_first_symptom"
        ],
    },
    "date_consultation": {
        "label": "Date of Consultation / Visit",
        "description": "Date patient first consulted a healthcare provider or facility",
        "type": "date",
        "category": "timeline",
        "synonyms": [
            "date_consultation", "consult_date", "date_visite", "visit_date",
            "date_consult", "fecha_consulta", "fecha_visita", "date_of_consultation",
            "date_consultation_medicale", "consultation_date"
        ],
    },
    "date_admission": {
        "label": "Date of Hospital Admission",
        "description": "Date patient was admitted to inpatient care / hospital",
        "type": "date",
        "category": "timeline",
        "synonyms": [
            "date_admission", "hosp_date", "date_hosp", "date_hospitalisation",
            "admission_date", "date_entree", "fecha_ingreso", "fecha_hospitalizacion",
            "dt_admission", "date_admit", "date_inpatient"
        ],
    },
    "date_discharge": {
        "label": "Date of Discharge",
        "description": "Date patient was discharged from inpatient care",
        "type": "date",
        "category": "timeline",
        "synonyms": [
            "date_discharge", "discharge_date", "date_sortie", "date_de_sortie",
            "fecha_alta", "fecha_egreso", "dt_discharge", "date_liberation"
        ],
    },
    "date_death": {
        "label": "Date of Death",
        "description": "Date when the patient died",
        "type": "date",
        "category": "timeline",
        "synonyms": [
            "date_death", "death_date", "date_deces", "date_de_deces", "date_mort",
            "fecha_defuncion", "fecha_muerte", "fecha_fallecimiento", "dt_death", "dod"
        ],
    },
    "date_sample_collected": {
        "label": "Date Specimen Collected",
        "description": "Date laboratory specimen/sample was obtained from patient",
        "type": "date",
        "category": "laboratory",
        "synonyms": [
            "date_sample_collected", "specimen_date", "sample_date", "date_prelevement",
            "date_de_prelevement", "date_echantillon", "fecha_toma_muestra",
            "date_collection", "dt_sample"
        ],
    },
    "date_lab_result": {
        "label": "Date Laboratory Result",
        "description": "Date laboratory diagnostic test result was reported",
        "type": "date",
        "category": "laboratory",
        "synonyms": [
            "date_lab_result", "lab_date", "result_date", "date_resultat",
            "date_resultat_labo", "fecha_resultado", "date_labo", "dt_result"
        ],
    },
    "case_definition": {
        "label": "Case Classification",
        "description": "Epidemiological case classification (Confirmed, Probable, Suspect, Discarded)",
        "type": "categorical",
        "category": "clinical",
        "synonyms": [
            "case_definition", "classification", "case_classification", "case_status",
            "statut_cas", "classification_cas", "case_class", "status", "statut",
            "clasificacion", "case_def", "diagnostic", "final_classification"
        ],
    },
    "outcome": {
        "label": "Patient Outcome / Vital Status",
        "description": "Final patient outcome (Alive, Dead, Recovered, Discharged, Transferred, LAMA)",
        "type": "categorical",
        "category": "clinical",
        "synonyms": [
            "outcome", "issue", "evolution", "vital_status", "statut_vital",
            "etat_sortie", "issue_clinique", "condicion_egreso", "patient_outcome",
            "status_final", "final_outcome", "outcome_status"
        ],
    },
    "hospitalized": {
        "label": "Hospitalized (Yes/No)",
        "description": "Whether the patient was admitted to hospital",
        "type": "binary",
        "category": "clinical",
        "synonyms": [
            "hospitalized", "hospitalisation", "hospitalise", "admitted",
            "hospitalizado", "is_hospitalized", "inpatient", "hospitalized_yn"
        ],
    },
    "lab_result": {
        "label": "Laboratory Test Result",
        "description": "Result of diagnostic test (Positive, Negative, Inconclusive)",
        "type": "categorical",
        "category": "laboratory",
        "synonyms": [
            "lab_result", "resultat_labo", "resultat_laboratoire", "test_result",
            "pcr_result", "rdt_result", "resultat_pcr", "resultat_tdr",
            "resultado_laboratorio", "lab_status", "laboratory_result"
        ],
    },
    "health_facility": {
        "label": "Health Facility / Hospital",
        "description": "Name or code of the treating healthcare facility",
        "type": "string",
        "category": "geographic",
        "synonyms": [
            "health_facility", "facility", "structure_sante", "hopital", "hospital",
            "centre_sante", "cs", "csb", "fosa", "centro_salud", "facility_name",
            "treatment_center", "cte", "ctc", "hospital_name"
        ],
    },
    "admin1": {
        "label": "Admin Level 1 (Province / Region / State)",
        "description": "Primary administrative division",
        "type": "string",
        "category": "geographic",
        "synonyms": [
            "admin1", "province", "region", "state", "departement", "estado",
            "provincia", "adm1", "admin_level_1", "region_sanitaire"
        ],
    },
    "admin2": {
        "label": "Admin Level 2 (District / County / Zone)",
        "description": "Secondary administrative division",
        "type": "string",
        "category": "geographic",
        "synonyms": [
            "admin2", "district", "zone_sante", "zone_de_sante", "county",
            "commune", "municipality", "distrito", "adm2", "admin_level_2", "district_sanitaire"
        ],
    },
    "admin3": {
        "label": "Admin Level 3 (Village / Subcounty / Aire)",
        "description": "Tertiary administrative division or village",
        "type": "string",
        "category": "geographic",
        "synonyms": [
            "admin3", "village", "aire_sante", "aire_de_sante", "subcounty",
            "neighborhood", "quartier", "localite", "adm3", "admin_level_3", "community"
        ],
    },
    "vaccinated": {
        "label": "Vaccination Status",
        "description": "Whether the patient was vaccinated against target disease",
        "type": "binary",
        "category": "clinical",
        "synonyms": [
            "vaccinated", "vaccination", "vaccine", "statut_vaccinal", "vaccine_status",
            "is_vaccinated", "vaccine_yn", "vacunado", "vaccin"
        ],
    },
    "vaccine_doses": {
        "label": "Number of Vaccine Doses",
        "description": "Total doses of target vaccine received by patient",
        "type": "numeric",
        "category": "clinical",
        "synonyms": [
            "vaccine_doses", "doses", "doses_count", "nb_doses", "nombre_doses",
            "dose_number", "dosis", "doses_recues"
        ],
    },
    "pregnant": {
        "label": "Pregnancy Status",
        "description": "Whether the patient is pregnant",
        "type": "binary",
        "category": "clinical",
        "synonyms": [
            "pregnant", "pregnancy", "grossesse", "enceinte", "embarazada",
            "embarazo", "is_pregnant", "pregnant_yn"
        ],
    },
    "fever": {
        "label": "Fever Symptom",
        "description": "Patient had fever symptom (Yes/No)",
        "type": "binary",
        "category": "symptom",
        "synonyms": ["fever", "fievre", "fiebre", "temp", "temperature", "febrile"],
    },
    "cough": {
        "label": "Cough Symptom",
        "description": "Patient had cough symptom (Yes/No)",
        "type": "binary",
        "category": "symptom",
        "synonyms": ["cough", "toux", "tos", "coughing"],
    },
    "diarrhea": {
        "label": "Diarrhea Symptom",
        "description": "Patient had diarrhea symptom (Yes/No)",
        "type": "binary",
        "category": "symptom",
        "synonyms": ["diarrhea", "diarrhoea", "diarrhee", "diarrea", "watery_diarrhea"],
    },
    "vomiting": {
        "label": "Vomiting Symptom",
        "description": "Patient had vomiting symptom (Yes/No)",
        "type": "binary",
        "category": "symptom",
        "synonyms": ["vomiting", "vomissements", "vomissement", "vomitos", "vomito", "emesis"],
    },
    "bleeding": {
        "label": "Bleeding / Hemorrhagic Symptom",
        "description": "Patient had unexplained bleeding/hemorrhage (Yes/No)",
        "type": "binary",
        "category": "symptom",
        "synonyms": ["bleeding", "saignement", "hemorragie", "sangrado", "hemorrhage"],
    },
    "rash": {
        "label": "Rash Symptom",
        "description": "Patient had skin rash (Yes/No)",
        "type": "binary",
        "category": "symptom",
        "synonyms": ["rash", "eruption", "eruption_cutanee", "erupcion", "skin_rash"],
    },
    "phone": {
        "label": "Phone Number",
        "description": "Contact phone number (PII)",
        "type": "string",
        "category": "demographic_pii",
        "synonyms": [
            "phone", "telephone", "tel", "phone_number", "contact_phone",
            "numero_telephone", "cell", "mobile"
        ],
    },
}

# Standard categorical mappings
SEX_MAPPINGS: Dict[str, str] = {
    # Male
    "m": "Male",
    "male": "Male",
    "homme": "Male",
    "h": "Male",
    "masculin": "Male",
    "masculino": "Male",
    "man": "Male",
    "boy": "Male",
    "garcon": "Male",
    "garçon": "Male",
    "hom": "Male",
    "masc": "Male",
    "1": "Male",
    # Female
    "f": "Female",
    "female": "Female",
    "femme": "Female",
    "feminin": "Female",
    "féminin": "Female",
    "femenino": "Female",
    "woman": "Female",
    "girl": "Female",
    "fille": "Female",
    "fem": "Female",
    "muj": "Female",
    "mujer": "Female",
    "2": "Female",
    # Other / Intersex
    "o": "Other",
    "other": "Other",
    "autre": "Other",
    "otro": "Other",
    "intersex": "Other",
    "non-binary": "Other",
    # Explicit Unknown
    "u": "Unknown",
    "unknown": "Unknown",
    "inconnu": "Unknown",
    "desconocido": "Unknown",
    "unk": "Unknown",
    "nr": "Unknown",
}

CASE_DEFINITION_MAPPINGS: Dict[str, str] = {
    # Confirmed
    "confirmed": "Confirmed",
    "confirme": "Confirmed",
    "confirmé": "Confirmed",
    "confirmado": "Confirmed",
    "conf": "Confirmed",
    "c": "Confirmed",
    "pcr+": "Confirmed",
    "pcr_pos": "Confirmed",
    "positive": "Confirmed",
    "pos": "Confirmed",
    "lab_confirmed": "Confirmed",
    "1": "Confirmed",
    # Probable
    "probable": "Probable",
    "prob": "Probable",
    "p": "Probable",
    "epi_linked": "Probable",
    "epilinked": "Probable",
    "lien_epi": "Probable",
    "2": "Probable",
    # Suspect
    "suspect": "Suspect",
    "suspected": "Suspect",
    "sospechoso": "Suspect",
    "susp": "Suspect",
    "s": "Suspect",
    "possible": "Suspect",
    "under_investigation": "Suspect",
    "3": "Suspect",
    # Discarded / Non-case
    "discarded": "Discarded",
    "non-case": "Discarded",
    "non_case": "Discarded",
    "exclu": "Discarded",
    "descarte": "Discarded",
    "descartado": "Discarded",
    "invalid": "Discarded",
    "invalide": "Discarded",
    "negative": "Discarded",
    "neg": "Discarded",
    "4": "Discarded",
    # Explicit Unknown
    "unknown": "Unknown",
    "inconnu": "Unknown",
    "unk": "Unknown",
}

OUTCOME_MAPPINGS: Dict[str, str] = {
    # Dead
    "dead": "Dead",
    "died": "Dead",
    "deceased": "Dead",
    "death": "Dead",
    "mort": "Dead",
    "morte": "Dead",
    "decede": "Dead",
    "décédé": "Dead",
    "décédée": "Dead",
    "fallecido": "Dead",
    "fallecida": "Dead",
    "muerto": "Dead",
    "muerte": "Dead",
    "dcd": "Dead",
    "d": "Dead",
    # Recovered / Cured
    "recovered": "Recovered",
    "gueri": "Recovered",
    "guéri": "Recovered",
    "guérie": "Recovered",
    "cured": "Recovered",
    "curado": "Recovered",
    "recuperado": "Recovered",
    "recupere": "Recovered",
    "recupéré": "Recovered",
    "r": "Recovered",
    # Discharged
    "discharged": "Discharged",
    "discharge": "Discharged",
    "sortie": "Discharged",
    "sorti": "Discharged",
    "alta": "Discharged",
    "egreso": "Discharged",
    # Transferred
    "transferred": "Transferred",
    "transfer": "Transferred",
    "transfere": "Transferred",
    "transféré": "Transferred",
    "refere": "Transferred",
    "référé": "Transferred",
    "transferido": "Transferred",
    # Left Against Medical Advice (LAMA)
    "lama": "LAMA",
    "left against medical advice": "LAMA",
    "fuite": "LAMA",
    "evade": "LAMA",
    "évadé": "LAMA",
    "abandon": "LAMA",
    # Alive / Inpatient / Active
    "alive": "Alive",
    "vivant": "Alive",
    "vivante": "Alive",
    "vivo": "Alive",
    "viva": "Alive",
    "active": "Alive",
    "hospitalized": "Alive",
    "in_care": "Alive",
    "en_soins": "Alive",
    "hospitalise": "Alive",
    "hospitalisé": "Alive",
    # Explicit Unknown
    "unknown": "Unknown",
    "inconnu": "Unknown",
    "desconocido": "Unknown",
    "unk": "Unknown",
}

BINARY_MAPPINGS: Dict[str, str] = {
    # Yes
    "yes": "Yes",
    "y": "Yes",
    "oui": "Yes",
    "o": "Yes",
    "si": "Yes",
    "s": "Yes",
    "true": "Yes",
    "t": "Yes",
    "vrai": "Yes",
    "v": "Yes",
    "1": "Yes",
    "1.0": "Yes",
    "+": "Yes",
    "pos": "Yes",
    "positive": "Yes",
    # No
    "no": "No",
    "n": "No",
    "non": "No",
    "false": "No",
    "f": "No",
    "faux": "No",
    "0": "No",
    "0.0": "No",
    "-": "No",
    "neg": "No",
    "negative": "No",
    # Explicit Unknown
    "unknown": "Unknown",
    "inconnu": "Unknown",
    "desconocido": "Unknown",
    "unk": "Unknown",
}

# Standard Missing Sentinel Values (Missing / Null)
MISSING_SENTINELS = [
    "",
    " ",
    "  ",
    "nan",
    "na",
    "n/a",
    "n.a.",
    "n_a",
    "null",
    "none",
    "nil",
    "--",
    "---",
    "-99",
    "-999",
    "999",
    "9999",
    "?",
    "??",
    ".",
    "/",
    "missing",
    "manquant",
    "sin dato",
    "sd",
    "non renseigne",
    "non renseigné",
    "n.r.",
    "nsp",
    "not applicable",
    "unspecified",
]
