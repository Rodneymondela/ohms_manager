"""
seed_schedules.py
=================
Populates the Stressor library with common occupational hygiene stressors
including OEL values, units, references, and sampling methods.

Run from the project root:
    flask shell -c "exec(open('seed_schedules.py').read())"
  OR
    python seed_schedules.py
"""

from app import create_app, db
from app.schedules.models import Stressor

app = create_app()

STRESSORS = [
    # ── Chemical ────────────────────────────────────────────────────────────────
    {
        "name":            "Respirable Crystalline Silica (RCS)",
        "category":        "Chemical",
        "oel_value":       0.05,
        "oel_unit":        "mg/m³",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-TWA (2023)",
        "sampling_method": "NIOSH 7500 / 7602 (XRF or IR); cyclone gravimetric pre-separator",
    },
    {
        "name":            "Respirable Dust (inert)",
        "category":        "Chemical",
        "oel_value":       3.0,
        "oel_unit":        "mg/m³",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-TWA",
        "sampling_method": "Gravimetric — cyclone pre-separator, 37 mm filter",
    },
    {
        "name":            "Inhalable Dust (total)",
        "category":        "Chemical",
        "oel_value":       10.0,
        "oel_unit":        "mg/m³",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-TWA",
        "sampling_method": "Gravimetric — IOM sampler, 37 mm filter",
    },
    {
        "name":            "Diesel Particulate Matter (DPM / EC)",
        "category":        "Chemical",
        "oel_value":       0.02,
        "oel_unit":        "mg/m³ EC",
        "oel_text":        None,
        "oel_reference":   "MHSA / NIOSH REL (elemental carbon)",
        "sampling_method": "NIOSH 5040 (thermal-optical EC analysis); SKC carbon sampler",
    },
    {
        "name":            "Lead (inorganic)",
        "category":        "Chemical",
        "oel_value":       0.05,
        "oel_unit":        "mg/m³",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-TWA (2023)",
        "sampling_method": "NIOSH 7082 / 7105 — air filter ICP-AES; biological monitoring (blood-Pb)",
    },
    {
        "name":            "Manganese (dust & fume)",
        "category":        "Chemical",
        "oel_value":       0.02,
        "oel_unit":        "mg/m³",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-TWA (inhalable fraction)",
        "sampling_method": "NIOSH 7300 — ICP-AES; personal sampler with IOM head",
    },
    {
        "name":            "Carbon Monoxide (CO)",
        "category":        "Chemical",
        "oel_value":       20.0,
        "oel_unit":        "ppm",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-TWA",
        "sampling_method": "Electrochemical direct-reading detector; NIOSH 6604 sorbent tube",
    },
    {
        "name":            "Nitrogen Dioxide (NO₂)",
        "category":        "Chemical",
        "oel_value":       0.2,
        "oel_unit":        "ppm",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-TWA (2023)",
        "sampling_method": "Triethanolamine badge or NIOSH 6014; colorimetric / IC analysis",
    },
    {
        "name":            "Welding Fume (total)",
        "category":        "Chemical",
        "oel_value":       1.0,
        "oel_unit":        "mg/m³",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-TWA",
        "sampling_method": "Gravimetric — 37 mm PVC filter in closed-face cassette",
    },
    {
        "name":            "Asbestos (all forms)",
        "category":        "Chemical",
        "oel_value":       0.1,
        "oel_unit":        "f/cm³",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-TWA; MHSA Reg 7",
        "sampling_method": "NIOSH 7400 phase-contrast microscopy (PCM); TEM for speciation",
    },
    {
        "name":            "Isocyanates (TDI / MDI)",
        "category":        "Chemical",
        "oel_value":       0.005,
        "oel_unit":        "ppm",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-C (ceiling)",
        "sampling_method": "NIOSH 5522 impinger/filter; HPLC-UV analysis",
    },
    {
        "name":            "Benzene",
        "category":        "Chemical",
        "oel_value":       0.5,
        "oel_unit":        "ppm",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-TWA (A1 carcinogen)",
        "sampling_method": "NIOSH 1501 charcoal tube / GC-FID; passive badge",
    },
    {
        "name":            "Formaldehyde",
        "category":        "Chemical",
        "oel_value":       0.1,
        "oel_unit":        "ppm",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV-C (2023)",
        "sampling_method": "DNPH cartridge; HPLC-UV analysis (NIOSH 2016)",
    },

    # ── Physical ─────────────────────────────────────────────────────────────────
    {
        "name":            "Occupational Noise",
        "category":        "Physical",
        "oel_value":       85.0,
        "oel_unit":        "dB(A) TWA-8h",
        "oel_text":        None,
        "oel_reference":   "SANS 10083 / MHSA Reg 9.2",
        "sampling_method": "Personal noise dosimetry (IEC 61252); sound level mapping",
    },
    {
        "name":            "Hand-Arm Vibration (HAV)",
        "category":        "Physical",
        "oel_value":       2.5,
        "oel_unit":        "m/s² A(8)",
        "oel_text":        None,
        "oel_reference":   "EU Directive 2002/44/EC action value",
        "sampling_method": "ISO 5349-1/2 tri-axial accelerometer on tool handle",
    },
    {
        "name":            "Whole-Body Vibration (WBV)",
        "category":        "Physical",
        "oel_value":       0.5,
        "oel_unit":        "m/s² A(8)",
        "oel_text":        None,
        "oel_reference":   "EU Directive 2002/44/EC action value",
        "sampling_method": "ISO 2631-1 seat-pad accelerometer measurement",
    },
    {
        "name":            "Heat Stress (WBGT)",
        "category":        "Physical",
        "oel_value":       28.0,
        "oel_unit":        "°C WBGT",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV (moderate work, acclimatised)",
        "sampling_method": "Wet-bulb globe thermometer (ISO 7243); physiological monitoring",
    },
    {
        "name":            "Illuminance (Lighting)",
        "category":        "Physical",
        "oel_value":       None,
        "oel_unit":        "lux",
        "oel_text":        "Task-dependent — see SANS 10114",
        "oel_reference":   "SANS 10114:2005",
        "sampling_method": "Calibrated lux meter grid survey",
    },
    {
        "name":            "Non-Ionising Radiation (UV)",
        "category":        "Physical",
        "oel_value":       30.0,
        "oel_unit":        "J/m²",
        "oel_text":        None,
        "oel_reference":   "ACGIH TLV (effective irradiance, 270 nm)",
        "sampling_method": "Radiometric measurement; polysulphone badge dosimetry",
    },
    {
        "name":            "Ionising Radiation",
        "category":        "Physical",
        "oel_value":       20.0,
        "oel_unit":        "mSv/year",
        "oel_text":        None,
        "oel_reference":   "ICRP 103 / NNR Act 47 of 1999",
        "sampling_method": "TLD badge / OSL dosimetry; area monitoring",
    },

    # ── Biological ───────────────────────────────────────────────────────────────
    {
        "name":            "Bioaerosols (total viable)",
        "category":        "Biological",
        "oel_value":       None,
        "oel_unit":        "CFU/m³",
        "oel_text":        "Guideline: <10 000 CFU/m³ (general industry)",
        "oel_reference":   "ACGIH Bioaerosol Guidelines",
        "sampling_method": "Andersen impactor / RCS centrifugal sampler; culture & count",
    },
    {
        "name":            "Legionella (water systems)",
        "category":        "Biological",
        "oel_value":       None,
        "oel_unit":        "CFU/L",
        "oel_text":        "Action level: >100 CFU/L",
        "oel_reference":   "HSE ACoP L8 / SANS 10400",
        "sampling_method": "Water sampling — ISO 11731 culture method; PCR rapid test",
    },

    # ── Ergonomic ────────────────────────────────────────────────────────────────
    {
        "name":            "Manual Handling / Lifting",
        "category":        "Ergonomic",
        "oel_value":       None,
        "oel_unit":        None,
        "oel_text":        "NIOSH Lifting Equation — LI > 1 requires intervention",
        "oel_reference":   "NIOSH 94-110 / ISO 11228-1",
        "sampling_method": "NIOSH Lifting Equation; REBA / RULA posture assessment",
    },
    {
        "name":            "Repetitive Upper-Limb Movements",
        "category":        "Ergonomic",
        "oel_value":       None,
        "oel_unit":        None,
        "oel_text":        "OCRA Index > 2.2 = yellow; > 3.5 = red",
        "oel_reference":   "ISO 11228-3 / OCRA checklist",
        "sampling_method": "OCRA checklist / RULA rapid assessment; video analysis",
    },
    {
        "name":            "Awkward Postures",
        "category":        "Ergonomic",
        "oel_value":       None,
        "oel_unit":        None,
        "oel_text":        "REBA score > 7 requires immediate action",
        "oel_reference":   "REBA / RULA / ISO 11226",
        "sampling_method": "Postural observation (REBA); electrogoniometry",
    },

    # ── Psychosocial ─────────────────────────────────────────────────────────────
    {
        "name":            "Occupational Stress",
        "category":        "Psychosocial",
        "oel_value":       None,
        "oel_unit":        None,
        "oel_text":        "Qualitative — HSE Management Standards",
        "oel_reference":   "HSE Management Standards Indicator Tool",
        "sampling_method": "HSE Indicator Tool survey; COPSOQ questionnaire",
    },
    {
        "name":            "Workplace Fatigue",
        "category":        "Psychosocial",
        "oel_value":       None,
        "oel_unit":        None,
        "oel_text":        "Qualitative — shift schedule analysis + Samn-Perelli scale",
        "oel_reference":   "FRMS guidelines; ICAO / IATA fatigue risk management",
        "sampling_method": "Samn-Perelli fatigue scale; actigraphy; shift schedule review",
    },
]


def seed():
    with app.app_context():
        db.create_all()
        added = 0
        skipped = 0
        for data in STRESSORS:
            exists = Stressor.query.filter_by(name=data["name"]).first()
            if exists:
                skipped += 1
                continue
            s = Stressor(**data, is_active=True)
            db.session.add(s)
            added += 1
        db.session.commit()
        print(f"Seed complete — {added} stressors added, {skipped} already existed.")


if __name__ == "__main__":
    seed()
