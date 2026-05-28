import pandas as pd
from config import METADATA_CSV_2020, METADATA_CSV_2019

# ISIC2019 multi-class label mapping
ISIC2019_LABEL_NAMES = {
    0: 'MEL', 1: 'NV', 2: 'BCC', 3: 'AK',
    4: 'BKL', 5: 'DF', 6: 'VASC', 7: 'SCC'
}
# Malignant classes in ISIC2019
ISIC2019_MALIGNANT = {0, 2, 7}  # MEL, BCC, SCC

_df_2020 = None
_df_2019 = None


def _sanitize(val):
    """Convert NaN/Inf to None for JSON."""
    if pd.isna(val):
        return None
    if isinstance(val, float) and not (-1e308 < val < 1e308):
        return None
    return val


def load_metadata():
    global _df_2020, _df_2019

    if _df_2020 is None:
        _df_2020 = pd.read_csv(METADATA_CSV_2020)
        _df_2020.set_index("image_name", inplace=True, drop=False)

    if _df_2019 is None:
        _df_2019 = pd.read_csv(METADATA_CSV_2019)
        _df_2019.set_index("image", inplace=True, drop=False)


def get_metadata(image_id: str, db: str = "isic2020") -> dict:
    load_metadata()

    if db == "isic2019":
        if image_id not in _df_2019.index:
            return {}
        row = _df_2019.loc[image_id]
        label = int(row.get("label", -1))
        label_name = ISIC2019_LABEL_NAMES.get(label, str(label))
        is_malignant = 1 if label in ISIC2019_MALIGNANT else 0
        return {
            "image_name": str(row["image"]),
            "patient_id": None,
            "sex": str(row.get("sex", "")) if pd.notna(row.get("sex")) else "",
            "age_approx": _sanitize(row.get("age_approx")),
            "anatom_site": str(row.get("anatom_site_general", "")) if pd.notna(row.get("anatom_site_general")) else "",
            "diagnosis": str(row.get("diagnosis_full", "")) if pd.notna(row.get("diagnosis_full")) else "",
            "benign_malignant": "malignant" if is_malignant else "benign",
            "target": is_malignant,
            "label_name": label_name,
        }

    # isic2020
    if image_id not in _df_2020.index:
        return {}
    row = _df_2020.loc[image_id]
    return {
        "image_name": str(row["image_name"]),
        "patient_id": str(row.get("patient_id", "")) if pd.notna(row.get("patient_id")) else "",
        "sex": str(row.get("sex", "")) if pd.notna(row.get("sex")) else "",
        "age_approx": _sanitize(row.get("age_approx")),
        "anatom_site": str(row.get("anatom_site_general_challenge", "")) if pd.notna(row.get("anatom_site_general_challenge")) else "",
        "diagnosis": str(row.get("diagnosis", "")) if pd.notna(row.get("diagnosis")) else "",
        "benign_malignant": str(row.get("benign_malignant", "")) if pd.notna(row.get("benign_malignant")) else "",
        "target": int(row.get("target", -1)),
    }
