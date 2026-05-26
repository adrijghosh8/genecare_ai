from datetime import datetime
from functools import wraps
from pathlib import Path
from uuid import uuid4
import json
import os
from flask import (
    Flask,
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('GENECARE_SECRET_KEY', 'gencare-local-dev-secret')

DATA_DIR = Path(__file__).resolve().parent / 'data'
ACCOUNTS_FILE = DATA_DIR / 'accounts.json'


PROFILE_FIELDS = [
    ('full_name', 'Full Name'),
    ('email', 'Email'),
    ('age', 'Age'),
    ('gender', 'Gender'),
    ('height', 'Height'),
    ('weight', 'Weight'),
    ('allergies', 'Allergies'),
    ('conditions', 'Existing Conditions'),
    ('medications', 'Medications'),
    ('family_history', 'Family History'),
    ('emergency_contact', 'Emergency Contact')
]


def load_accounts():
    if not ACCOUNTS_FILE.exists():
        return {}

    contents = ACCOUNTS_FILE.read_text(encoding='utf-8').strip()
    if not contents:
        return {}

    try:
        accounts = json.loads(contents)
    except json.JSONDecodeError:
        backup_name = f"accounts.corrupt-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        ACCOUNTS_FILE.replace(DATA_DIR / backup_name)
        return {}

    if not isinstance(accounts, dict):
        return {}

    for username, account in accounts.items():
        ensure_account_defaults(account, username)

    return accounts


def save_accounts(accounts):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary_file = DATA_DIR / f'.{ACCOUNTS_FILE.name}.tmp'
    with temporary_file.open('w', encoding='utf-8') as file:
        json.dump(accounts, file, indent=2)
    temporary_file.replace(ACCOUNTS_FILE)


def default_profile(full_name='', email=''):
    profile = {name: '' for name, _ in PROFILE_FIELDS}
    profile['full_name'] = full_name
    profile['email'] = email
    return profile


def ensure_account_defaults(account, username=''):
    profile = account.setdefault('profile', default_profile())
    for field, _ in PROFILE_FIELDS:
        profile.setdefault(field, '')

    if not profile.get('email') and account.get('email'):
        profile['email'] = account['email']
    if not profile.get('full_name') and account.get('full_name'):
        profile['full_name'] = account['full_name']

    account.setdefault('email', profile.get('email', ''))
    account.setdefault('full_name', profile.get('full_name') or username)
    account.setdefault('history', [])
    account.setdefault('notes', [])
    account.setdefault('reminders', [])
    account.setdefault('role', 'admin' if username == 'admin' else 'user')
    return account


def create_account(password_hash='', full_name='', email=''):
    return {
        'password_hash': password_hash,
        'email': email,
        'full_name': full_name,
        'profile': default_profile(full_name, email),
        'history': [],
        'notes': [],
        'reminders': [],
        'role': 'user'
    }


def current_user():
    username = session.get('username')
    if not username:
        return None

    account = load_accounts().get(username)
    if account is not None:
        ensure_account_defaults(account, username)

    return account


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get('username'):
            return redirect(url_for('login', next=request.path))

        return view(*args, **kwargs)

    return wrapped_view


@app.context_processor
def inject_user():
    username = session.get('username')
    account = get_account(username) if username else None
    return {
        'active_username': username,
        'active_display_name': (account or {}).get('full_name') or username
    }


def record_history(kind, title, content, metadata=None):
    username = session.get('username')
    if not username:
        return None

    accounts = load_accounts()
    account = accounts.get(username)
    if account is None:
        return None

    entry = {
        'id': uuid4().hex[:12],
        'kind': kind,
        'title': title,
        'content': content,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'metadata': metadata or {}
    }
    account.setdefault('history', []).insert(0, entry)
    account['history'] = account['history'][:80]
    save_accounts(accounts)
    return entry


def get_account(username=None):
    username = username or session.get('username')
    if not username:
        return None

    accounts = load_accounts()
    account = accounts.get(username)
    if account:
        ensure_account_defaults(account, username)
    return account


def update_account(username, updater):
    accounts = load_accounts()
    account = accounts.get(username)
    if not account:
        return None

    ensure_account_defaults(account, username)
    updater(account)
    save_accounts(accounts)
    return account


def is_admin(account=None):
    account = account or current_user()
    return bool(account and account.get('role') == 'admin')


YES_NO_OPTIONS = [
    {'label': 'Yes', 'value': '1'},
    {'label': 'No', 'value': '0'}
]

SMOKING_OPTIONS = [
    {'label': 'Smoker', 'value': '1'},
    {'label': 'Former smoker', 'value': '0.55'},
    {'label': 'Non-smoker', 'value': '0'}
]

FREQUENCY_OPTIONS = [
    {'label': 'Frequent', 'value': '1'},
    {'label': 'Occasional', 'value': '0.45'},
    {'label': 'Rare / Never', 'value': '0'}
]

SYMPTOM_OPTIONS = [
    {'label': 'Severe / frequent', 'value': '1'},
    {'label': 'Occasional / mild', 'value': '0.45'},
    {'label': 'None', 'value': '0'}
]

INTAKE_OPTIONS = [
    {'label': 'Low intake', 'value': '1'},
    {'label': 'Sometimes adequate', 'value': '0.45'},
    {'label': 'Usually adequate', 'value': '0'}
]


def metric(
    name, label, placeholder, unit, weight, insight,
    baseline=0, span=1, min_value=0, max_value=None, step='1',
    protective=False, target=None
):
    field = {
        'name': name,
        'label': label,
        'placeholder': placeholder,
        'unit': unit,
        'weight': weight,
        'insight': insight,
        'baseline': baseline,
        'span': span,
        'min': min_value,
        'step': step,
        'protective': protective
    }
    if max_value is not None:
        field['max'] = max_value
    if target is not None:
        field['target'] = target
    return field


def choice(name, label, options, weight, insight):
    return {
        'name': name,
        'label': label,
        'options': options,
        'weight': weight,
        'insight': insight
    }


DISEASE_CATEGORIES = [
    {
        'slug': 'cardiovascular',
        'title': 'Cardiovascular',
        'description': 'Heart, circulation, blood-pressure, and stroke-focused screening.'
    },
    {
        'slug': 'metabolic',
        'title': 'Metabolic and Endocrine',
        'description': 'Glucose, metabolism, and hormone-related patterns.'
    },
    {
        'slug': 'organ',
        'title': 'Organ and Respiratory Health',
        'description': 'Kidney, liver, and breathing-related risk indicators.'
    },
    {
        'slug': 'screening',
        'title': 'Screening and Bone Health',
        'description': 'Prevention, anemia, and bone-strength assessment areas.'
    }
]


DISEASES = {
    'heart-disease': {
        'slug': 'heart-disease',
        'title': 'Heart Disease',
        'category': 'cardiovascular',
        'subcategory': 'Coronary and heart health',
        'kicker': 'Cardiovascular',
        'description': 'Review modifiable and inherited indicators related to coronary heart health.',
        'summary': 'Blood pressure, cholesterol, tobacco use, activity, and family history.',
        'accent': '#0f766e',
        'checks': ['Blood pressure review', 'Lipid panel', 'Clinician cardiovascular risk discussion'],
        'guidance': ['Avoid tobacco exposure.', 'Aim for regular activity as advised by a clinician.', 'Discuss persistently high blood pressure or cholesterol results.'],
        'red_flags': ['Chest pressure or pain', 'Severe shortness of breath', 'Fainting or sudden collapse'],
        'fields': [
            metric('age', 'Age', '52', 'years', 0.10, 'Age provides context for cardiovascular risk review.', 35, 50, 0, 120),
            metric('systolic_bp', 'Systolic blood pressure', '140', 'mmHg', 0.20, 'Persistent elevated blood pressure should be confirmed clinically.', 115, 65, 50, 260),
            metric('cholesterol', 'Total cholesterol', '210', 'mg/dL', 0.18, 'A lipid panel gives a fuller cholesterol picture.', 160, 120, 50, 450),
            metric('bmi', 'Body mass index', '28.4', 'kg/m2', 0.10, 'BMI is one contextual measure and not a diagnosis.', 22, 18, 10, 70, '0.1'),
            choice('smoking', 'Tobacco exposure', SMOKING_OPTIONS, 0.15, 'Tobacco exposure is an important preventable heart risk factor.'),
            metric('exercise', 'Active days per week', '3', 'days', 0.10, 'Regular activity can support heart health.', 0, 5, 0, 7, '1', True, 5),
            choice('family_history', 'Close family heart history', YES_NO_OPTIONS, 0.17, 'Family history can guide earlier clinical assessment.')
        ]
    },
    'stroke-risk': {
        'slug': 'stroke-risk',
        'title': 'Stroke Risk',
        'category': 'cardiovascular',
        'subcategory': 'Brain circulation and warning factors',
        'kicker': 'Cardiovascular',
        'description': 'Assess common stroke-related factors and recognize urgent warning signs.',
        'summary': 'Blood pressure, rhythm history, diabetes, tobacco exposure, and previous TIA.',
        'accent': '#146c72',
        'checks': ['Blood pressure measurement', 'Diabetes screening as advised', 'Heart rhythm assessment when indicated'],
        'guidance': ['Control blood pressure with professional care.', 'Review irregular heart rhythm history with a clinician.', 'Know FAST stroke warning signs.'],
        'red_flags': ['Face drooping or one-sided weakness', 'Sudden speech difficulty', 'Sudden severe headache or vision loss'],
        'fields': [
            metric('age', 'Age', '60', 'years', 0.08, 'Age helps frame prevention discussions.', 40, 45, 0, 120),
            metric('systolic_bp', 'Systolic blood pressure', '145', 'mmHg', 0.20, 'Elevated blood pressure is a major modifiable indicator.', 115, 65, 50, 260),
            choice('smoking', 'Tobacco exposure', SMOKING_OPTIONS, 0.12, 'Smoking increases concern for vascular health.'),
            choice('diabetes', 'Diabetes diagnosis', YES_NO_OPTIONS, 0.12, 'Diabetes care affects stroke prevention planning.'),
            choice('atrial_fibrillation', 'Atrial fibrillation history', YES_NO_OPTIONS, 0.20, 'An irregular rhythm history needs clinician-guided prevention.'),
            choice('prior_tia', 'Previous TIA / mini-stroke', YES_NO_OPTIONS, 0.20, 'Prior transient symptoms warrant close medical follow-up.'),
            metric('cholesterol', 'Total cholesterol', '205', 'mg/dL', 0.08, 'Lipids add context to vascular assessment.', 160, 120, 50, 450)
        ]
    },
    'hypertension': {
        'slug': 'hypertension',
        'title': 'Hypertension',
        'category': 'cardiovascular',
        'subcategory': 'Blood pressure patterns',
        'kicker': 'Cardiovascular',
        'description': 'Track blood-pressure readings alongside everyday contributing factors.',
        'summary': 'Systolic and diastolic values, activity, diet pattern, stress, and history.',
        'accent': '#256d85',
        'checks': ['Repeat seated blood pressure readings', 'Medication review if prescribed', 'Clinician evaluation for persistent elevation'],
        'guidance': ['Measure blood pressure correctly and repeatedly.', 'Discuss sodium intake and activity with a professional.', 'Never change prescribed medication without medical advice.'],
        'red_flags': ['Very high reading with severe headache', 'Chest pain or breathing trouble', 'New weakness, confusion, or vision loss'],
        'fields': [
            metric('systolic_bp', 'Systolic blood pressure', '138', 'mmHg', 0.26, 'The upper blood-pressure number needs repeat confirmation.', 115, 65, 50, 260),
            metric('diastolic_bp', 'Diastolic blood pressure', '88', 'mmHg', 0.22, 'The lower blood-pressure number adds important context.', 75, 40, 30, 160),
            metric('bmi', 'Body mass index', '27.0', 'kg/m2', 0.10, 'BMI is one contextual measure for care planning.', 22, 18, 10, 70, '0.1'),
            choice('high_sodium_foods', 'High-sodium foods', FREQUENCY_OPTIONS, 0.10, 'Diet patterns can be discussed as part of blood-pressure care.'),
            metric('activity', 'Active days per week', '3', 'days', 0.10, 'Regular movement supports blood-pressure management.', 0, 5, 0, 7, '1', True, 5),
            choice('stress', 'High stress symptoms', SYMPTOM_OPTIONS, 0.08, 'Stress symptoms may affect measurements and self-care.'),
            choice('family_history', 'Family hypertension history', YES_NO_OPTIONS, 0.14, 'Family history can inform monitoring frequency.')
        ]
    },
    'diabetes': {
        'slug': 'diabetes',
        'title': 'Diabetes',
        'category': 'metabolic',
        'subcategory': 'Blood glucose and type 2 risk',
        'kicker': 'Metabolic',
        'description': 'Review blood-glucose indicators and common type 2 diabetes risk factors.',
        'summary': 'Fasting glucose, BMI, activity, blood pressure, symptoms, and history.',
        'accent': '#1d5f9f',
        'checks': ['Fasting blood glucose or HbA1c', 'Blood pressure review', 'Clinician follow-up for symptoms or raised results'],
        'guidance': ['Record laboratory values accurately.', 'Build sustainable movement and nutrition habits with care advice.', 'Discuss thirst, frequent urination, or unexplained weight change.'],
        'red_flags': ['Vomiting with marked thirst or confusion', 'Severe drowsiness', 'Rapid breathing with very high glucose'],
        'fields': [
            metric('age', 'Age', '45', 'years', 0.08, 'Age supports screening context.', 35, 50, 0, 120),
            metric('fasting_sugar', 'Fasting glucose', '126', 'mg/dL', 0.27, 'Use a laboratory measurement when available.', 85, 90, 20, 450),
            metric('bmi', 'Body mass index', '30.2', 'kg/m2', 0.16, 'BMI is only one part of metabolic assessment.', 22, 18, 10, 70, '0.1'),
            metric('systolic_bp', 'Systolic blood pressure', '132', 'mmHg', 0.09, 'Blood pressure is relevant to overall metabolic care.', 115, 65, 50, 260),
            metric('activity', 'Active days per week', '2', 'days', 0.12, 'Activity is a modifiable prevention factor.', 0, 5, 0, 7, '1', True, 5),
            choice('symptoms', 'Thirst / frequent urination', SYMPTOM_OPTIONS, 0.12, 'Symptoms require clinical assessment rather than self-diagnosis.'),
            choice('family_history', 'Family diabetes history', YES_NO_OPTIONS, 0.16, 'Family history may support earlier screening.')
        ]
    },
    'metabolic-syndrome': {
        'slug': 'metabolic-syndrome',
        'title': 'Metabolic Syndrome',
        'category': 'metabolic',
        'subcategory': 'Combined metabolic indicators',
        'kicker': 'Metabolic',
        'description': 'Bring together waist, blood pressure, glucose, triglycerides, and HDL patterns.',
        'summary': 'Waist size, fasting glucose, blood pressure, triglycerides, HDL, and activity.',
        'accent': '#3666a5',
        'checks': ['Waist measurement', 'Fasting lipid panel', 'Glucose and blood-pressure review'],
        'guidance': ['Discuss combined abnormal measurements with a clinician.', 'Build an achievable activity plan.', 'Recheck laboratory results on professional advice.'],
        'red_flags': ['Chest pain or breathlessness', 'Fainting', 'Symptoms of severe high blood glucose'],
        'fields': [
            metric('waist', 'Waist circumference', '98', 'cm', 0.15, 'Waist thresholds differ by individual and should be clinically interpreted.', 80, 45, 30, 180, '0.1'),
            metric('fasting_sugar', 'Fasting glucose', '112', 'mg/dL', 0.20, 'A confirmed lab result is more meaningful than estimation.', 85, 90, 20, 450),
            metric('systolic_bp', 'Systolic blood pressure', '132', 'mmHg', 0.17, 'Repeat elevated blood-pressure readings with a clinician.', 115, 65, 50, 260),
            metric('triglycerides', 'Triglycerides', '180', 'mg/dL', 0.18, 'A fasting lipid panel can establish the full pattern.', 100, 220, 20, 800),
            metric('hdl', 'HDL cholesterol', '42', 'mg/dL', 0.17, 'Lower HDL can add to a metabolic pattern assessment.', 0, 35, 0, 130, '1', True, 60),
            metric('activity', 'Active days per week', '2', 'days', 0.13, 'Movement is a relevant modifiable factor.', 0, 5, 0, 7, '1', True, 5)
        ]
    },
    'thyroid-disorder': {
        'slug': 'thyroid-disorder',
        'title': 'Thyroid Disorder',
        'category': 'metabolic',
        'subcategory': 'Thyroid symptom patterns',
        'kicker': 'Endocrine',
        'description': 'Organize symptoms and history that may prompt thyroid testing.',
        'summary': 'Symptoms, heart rate, swelling, laboratory history, and autoimmune context.',
        'accent': '#4d659f',
        'checks': ['TSH and thyroid hormone testing if advised', 'Neck examination for swelling', 'Medication and autoimmune history review'],
        'guidance': ['Symptoms alone cannot confirm thyroid disease.', 'Report neck swelling or persistent palpitations.', 'Seek laboratory interpretation from a clinician.'],
        'red_flags': ['Rapid heartbeat with chest pain', 'Severe confusion or collapse', 'Neck swelling affecting breathing'],
        'fields': [
            metric('age', 'Age', '40', 'years', 0.08, 'Age provides background rather than diagnosis.', 35, 50, 0, 120),
            choice('symptom_burden', 'Fatigue / weight / temperature symptoms', SYMPTOM_OPTIONS, 0.22, 'Symptoms have many causes and require examination.'),
            metric('resting_pulse', 'Resting pulse', '92', 'beats/min', 0.12, 'Persistent unusual pulse should be medically reviewed.', 70, 60, 30, 220),
            choice('abnormal_test', 'Previous abnormal thyroid test', YES_NO_OPTIONS, 0.24, 'Previous testing is important clinical context.'),
            choice('autoimmune_history', 'Autoimmune condition history', YES_NO_OPTIONS, 0.14, 'Autoimmune history may guide testing decisions.'),
            choice('neck_swelling', 'Neck swelling / fullness', YES_NO_OPTIONS, 0.20, 'New or growing neck swelling should be examined.')
        ]
    },
    'cancer-risk': {
        'slug': 'cancer-risk',
        'title': 'Cancer Risk',
        'category': 'screening',
        'subcategory': 'General prevention and screening',
        'kicker': 'Screening',
        'description': 'Review broad prevention factors and screening conversations; this cannot detect cancer.',
        'summary': 'Tobacco, alcohol, exposure history, family history, and screening gaps.',
        'accent': '#5960a8',
        'checks': ['Age-appropriate screening discussion', 'Family-history review', 'Evaluation of persistent new symptoms'],
        'guidance': ['Follow recommended screening schedules with a clinician.', 'Avoid tobacco exposure.', 'Have unexplained persistent symptoms assessed.'],
        'red_flags': ['Unexplained severe bleeding', 'A rapidly changing lump or lesion', 'Persistent symptoms with significant weight loss'],
        'fields': [
            metric('age', 'Age', '50', 'years', 0.10, 'Screening recommendations often vary with age and context.', 35, 50, 0, 120),
            choice('smoking', 'Tobacco exposure', SMOKING_OPTIONS, 0.20, 'Tobacco prevention is relevant across several cancers.'),
            choice('alcohol', 'Alcohol frequency', FREQUENCY_OPTIONS, 0.09, 'Alcohol pattern is one prevention discussion point.'),
            metric('bmi', 'Body mass index', '27.5', 'kg/m2', 0.07, 'BMI offers limited context and is not a cancer test.', 22, 18, 10, 70, '0.1'),
            choice('family_history', 'Close family cancer history', YES_NO_OPTIONS, 0.23, 'Family history may change personalized screening advice.'),
            choice('exposure', 'Known occupational / radiation exposure', YES_NO_OPTIONS, 0.16, 'Specific exposure concerns should be documented for care.'),
            metric('screening_gap', 'Years since advised screening', '3', 'years', 0.15, 'This applies only when screening was advised for you.', 1, 9, 0, 50)
        ]
    },
    'kidney-disease': {
        'slug': 'kidney-disease',
        'title': 'Kidney Disease',
        'category': 'organ',
        'subcategory': 'Chronic kidney disease indicators',
        'kicker': 'Renal',
        'description': 'Review kidney-related risk indicators and laboratory follow-up needs.',
        'summary': 'Blood pressure, glucose, creatinine, swelling, diabetes, and history.',
        'accent': '#0e7490',
        'checks': ['Creatinine/eGFR blood test', 'Urine albumin test', 'Blood pressure and diabetes review'],
        'guidance': ['Kidney function is assessed with clinical tests.', 'Discuss diabetes or hypertension management.', 'Report new swelling or reduced urine output.'],
        'red_flags': ['Sudden severe swelling or breathing trouble', 'Very low urine output', 'Confusion with significant illness'],
        'fields': [
            metric('age', 'Age', '48', 'years', 0.07, 'Age is supporting context.', 35, 50, 0, 120),
            metric('systolic_bp', 'Systolic blood pressure', '145', 'mmHg', 0.17, 'Blood pressure control is relevant to kidney health.', 115, 65, 50, 260),
            metric('fasting_sugar', 'Fasting glucose', '130', 'mg/dL', 0.13, 'Glucose history adds kidney risk context.', 85, 90, 20, 450),
            metric('creatinine', 'Serum creatinine', '1.2', 'mg/dL', 0.22, 'Laboratory interpretation should include eGFR.', 0.8, 2.5, 0, 20, '0.1'),
            choice('diabetes', 'Diabetes diagnosis', YES_NO_OPTIONS, 0.13, 'Diabetes is relevant to kidney screening plans.'),
            choice('swelling', 'Swelling / fluid retention', YES_NO_OPTIONS, 0.13, 'Swelling should be assessed for its cause.'),
            choice('family_history', 'Family kidney disease history', YES_NO_OPTIONS, 0.15, 'Family history may guide screening.')
        ]
    },
    'liver-disease': {
        'slug': 'liver-disease',
        'title': 'Liver Disease',
        'category': 'organ',
        'subcategory': 'Liver function and exposure factors',
        'kicker': 'Hepatic',
        'description': 'Organize metabolic, exposure, and liver-test indicators for follow-up.',
        'summary': 'Alcohol use, liver enzymes, bilirubin, BMI, diabetes, and hepatitis exposure.',
        'accent': '#b7791f',
        'checks': ['Liver function blood tests', 'Hepatitis testing when indicated', 'Clinician review of medicines and alcohol history'],
        'guidance': ['Liver enzyme results require clinical interpretation.', 'Discuss hepatitis exposure and prevention.', 'Seek assessment for jaundice or persistent abdominal symptoms.'],
        'red_flags': ['Yellow skin with severe illness', 'Vomiting blood or black stools', 'Marked confusion or abdominal swelling'],
        'fields': [
            metric('age', 'Age', '44', 'years', 0.05, 'Age offers background context.', 35, 50, 0, 120),
            choice('alcohol', 'Alcohol frequency', FREQUENCY_OPTIONS, 0.15, 'Alcohol pattern should be discussed honestly in care.'),
            metric('bmi', 'Body mass index', '29.1', 'kg/m2', 0.10, 'Metabolic factors may matter for liver health.', 22, 18, 10, 70, '0.1'),
            metric('alt', 'ALT / SGPT', '45', 'U/L', 0.22, 'An elevated liver enzyme should be interpreted clinically.', 20, 100, 0, 1000),
            metric('bilirubin', 'Total bilirubin', '1.1', 'mg/dL', 0.18, 'Bilirubin results need context from a clinician.', 0.6, 3, 0, 30, '0.1'),
            choice('diabetes', 'Diabetes diagnosis', YES_NO_OPTIONS, 0.12, 'Diabetes can add metabolic context.'),
            choice('hepatitis', 'Possible hepatitis exposure', YES_NO_OPTIONS, 0.18, 'Potential exposure warrants professional testing advice.')
        ]
    },
    'copd': {
        'slug': 'copd',
        'title': 'COPD',
        'category': 'organ',
        'subcategory': 'Chronic lung and breathing symptoms',
        'kicker': 'Respiratory',
        'description': 'Review long-term respiratory symptoms and inhaled exposure history.',
        'summary': 'Smoking, exposure, cough, breathlessness, flare-ups, and oxygen level.',
        'accent': '#087f8c',
        'checks': ['Clinical breathing evaluation', 'Spirometry if advised', 'Oxygen saturation assessment for concerning symptoms'],
        'guidance': ['Avoid tobacco and harmful inhaled exposures.', 'Persistent cough or breathlessness deserves evaluation.', 'Follow prescribed inhaler plans only with professional care.'],
        'red_flags': ['Severe trouble breathing', 'Blue lips or confusion', 'Chest pain or rapidly worsening symptoms'],
        'fields': [
            metric('age', 'Age', '55', 'years', 0.05, 'Age provides respiratory screening context.', 35, 50, 0, 120),
            choice('smoking', 'Tobacco exposure', SMOKING_OPTIONS, 0.27, 'Smoking history is a central respiratory risk indicator.'),
            choice('dust_exposure', 'Dust / chemical fume exposure', YES_NO_OPTIONS, 0.13, 'Occupational exposures should be documented.'),
            choice('breathlessness', 'Breathlessness', SYMPTOM_OPTIONS, 0.19, 'Breathlessness requires assessment of cause and severity.'),
            choice('chronic_cough', 'Long-term cough', YES_NO_OPTIONS, 0.13, 'Persistent cough should be reviewed clinically.'),
            metric('flare_ups', 'Breathing flare-ups in past year', '1', 'episodes', 0.13, 'Repeated flare-ups need a care plan.', 0, 4, 0, 20),
            metric('oxygen_saturation', 'Oxygen saturation', '97', '%', 0.10, 'Low readings with symptoms require urgent assessment.', 0, 10, 60, 100, '1', True, 97)
        ]
    },
    'anemia': {
        'slug': 'anemia',
        'title': 'Anemia',
        'category': 'screening',
        'subcategory': 'Low hemoglobin indicators',
        'kicker': 'Hematology',
        'description': 'Review symptoms and test values that may prompt anemia evaluation.',
        'summary': 'Hemoglobin, fatigue, bleeding, diet, chronic disease, and symptoms.',
        'accent': '#9b4f64',
        'checks': ['Complete blood count', 'Iron studies if advised', 'Assessment for bleeding or nutritional causes'],
        'guidance': ['Do not start iron supplements without appropriate advice.', 'Report heavy bleeding or persistent fatigue.', 'Laboratory testing is needed to confirm anemia.'],
        'red_flags': ['Fainting or chest pain', 'Severe shortness of breath', 'Heavy active bleeding or black stools'],
        'fields': [
            metric('hemoglobin', 'Hemoglobin', '11.0', 'g/dL', 0.29, 'A blood count is required to interpret this value.', 0, 6, 0, 22, '0.1', True, 13),
            choice('fatigue', 'Fatigue / weakness', SYMPTOM_OPTIONS, 0.14, 'Fatigue has many possible causes.'),
            choice('breathlessness', 'Breathlessness on activity', SYMPTOM_OPTIONS, 0.12, 'Breathlessness should be medically assessed.'),
            choice('heavy_bleeding', 'Heavy or ongoing bleeding', YES_NO_OPTIONS, 0.20, 'Bleeding can require prompt care.'),
            choice('iron_diet', 'Iron-rich food intake', INTAKE_OPTIONS, 0.09, 'Diet is one possible contributor.'),
            choice('chronic_disease', 'Chronic health condition', YES_NO_OPTIONS, 0.10, 'Existing illness can affect blood counts.'),
            choice('pregnancy', 'Pregnant / recently postpartum', YES_NO_OPTIONS, 0.06, 'Pregnancy-related symptoms and labs need tailored care.')
        ]
    },
    'osteoporosis': {
        'slug': 'osteoporosis',
        'title': 'Osteoporosis',
        'category': 'screening',
        'subcategory': 'Bone strength and fracture risk',
        'kicker': 'Bone Health',
        'description': 'Review fracture-related history and factors relevant to bone-strength screening.',
        'summary': 'Age, fractures, steroid use, menopause, calcium intake, exercise, and history.',
        'accent': '#97613d',
        'checks': ['Bone-density screening discussion', 'Medication and steroid review', 'Calcium and vitamin D advice from a clinician'],
        'guidance': ['Discuss fractures after minor falls.', 'Use safe weight-bearing activity when appropriate.', 'Review long-term steroid treatment with your clinician.'],
        'red_flags': ['New severe back pain after minor injury', 'Possible hip fracture after a fall', 'Sudden loss of mobility'],
        'fields': [
            metric('age', 'Age', '62', 'years', 0.15, 'Age helps guide screening discussions.', 45, 40, 0, 120),
            choice('prior_fracture', 'Prior low-impact fracture', YES_NO_OPTIONS, 0.23, 'Previous fracture is important clinical history.'),
            choice('steroid_use', 'Long-term steroid medicine', YES_NO_OPTIONS, 0.17, 'Long-term steroid use can influence bone assessment.'),
            choice('menopause', 'Post-menopause', YES_NO_OPTIONS, 0.12, 'Hormonal history may affect screening advice.'),
            choice('calcium_intake', 'Calcium-rich food intake', INTAKE_OPTIONS, 0.09, 'Nutrition planning should be individualized.'),
            metric('exercise', 'Weight-bearing activity days', '2', 'days/week', 0.10, 'Appropriate movement can support bone health.', 0, 4, 0, 7, '1', True, 4),
            choice('family_history', 'Family hip-fracture history', YES_NO_OPTIONS, 0.14, 'Family history supports screening conversations.')
        ]
    }
}


def clamp(value, low=0, high=1):
    return max(low, min(value, high))


def disease_groups():
    groups = []
    for category in DISEASE_CATEGORIES:
        groups.append({
            **category,
            'diseases': [
                disease for disease in DISEASES.values()
                if disease['category'] == category['slug']
            ]
        })
    return groups


def format_metric_value(field, submitted_value):
    if 'options' in field:
        return next(
            (option['label'] for option in field['options'] if option['value'] == submitted_value),
            submitted_value
        )
    return f"{submitted_value} {field.get('unit', '')}".strip()


def detailed_prediction(data, submitted, disease):
    total_weight = sum(field['weight'] for field in disease['fields'])
    weighted_score = 0
    metrics = []

    for field in disease['fields']:
        value = data[field['name']]
        if 'options' in field:
            influence = clamp(value)
        elif field.get('protective'):
            influence = clamp((field.get('target', 0) - value) / field['span'])
        else:
            influence = clamp((value - field.get('baseline', 0)) / field['span'])

        contribution = influence * field['weight']
        weighted_score += contribution

        if influence >= 0.70:
            status = 'Elevated influence'
            tone = 'high'
        elif influence >= 0.35:
            status = 'Review'
            tone = 'moderate'
        else:
            status = 'Lower influence'
            tone = 'low'

        metrics.append({
            'label': field['label'],
            'value': format_metric_value(field, submitted[field['name']]),
            'impact': round(influence * 100),
            'points': round((contribution / total_weight) * 100, 1),
            'status': status,
            'tone': tone,
            'insight': field['insight']
        })

    percentage = round(clamp(weighted_score / total_weight) * 100)
    if percentage >= 60:
        risk = 'High Risk'
        color = '#b42318'
        summary = 'Several entered factors deserve timely clinical review.'
    elif percentage >= 30:
        risk = 'Moderate Risk'
        color = '#b7791f'
        summary = 'Some factors are worth discussing or monitoring with a clinician.'
    else:
        risk = 'Low Risk'
        color = '#0f766e'
        summary = 'The entered factors show a lower index, but symptoms still need appropriate care.'

    metrics.sort(key=lambda item: item['points'], reverse=True)
    return {
        'risk': risk,
        'percentage': percentage,
        'color': color,
        'label': 'Screening Risk Index',
        'summary': summary,
        'metrics': metrics,
        'top_drivers': metrics[:3],
        'checks': disease['checks'],
        'guidance': disease['guidance'],
        'red_flags': disease['red_flags']
    }


def local_ai_doctor_reply(message):
    text = message.strip().lower()

    emergency_terms = [
        'chest pain',
        'trouble breathing',
        'shortness of breath',
        'severe bleeding',
        'fainting',
        'stroke',
        'suicidal',
        'confusion',
        'blue lips'
    ]
    if any(term in text for term in emergency_terms):
        return (
            'This could be urgent. Please seek emergency medical care now or call your local emergency number. '
            'If possible, stay with someone while you get help. I can help you organize symptoms, but I cannot '
            'replace emergency care.'
        )

    topics = [
        {
            'keywords': ['fever', 'temperature', 'chills', 'body ache'],
            'reply': (
                'For fever or chills, track your temperature, drink fluids, rest, and watch for warning signs such '
                'as breathing trouble, stiff neck, persistent fever, rash, dehydration, or symptoms lasting more '
                'than 3 days. A clinician can check whether infection testing or medication is needed.'
            )
        },
        {
            'keywords': ['cough', 'cold', 'sore throat', 'congestion'],
            'reply': (
                'For cough or cold symptoms, note how long it has been going on, whether there is fever, chest '
                'tightness, wheezing, or colored mucus. Warm fluids, rest, and avoiding smoke can help, but seek '
                'care quickly for breathing difficulty, chest pain, high fever, or symptoms that worsen.'
            )
        },
        {
            'keywords': ['headache', 'migraine', 'dizziness'],
            'reply': (
                'For headache or dizziness, note the location, severity, triggers, hydration, sleep, vision changes, '
                'and blood pressure if available. Sudden severe headache, weakness, confusion, fainting, or vision '
                'loss needs urgent medical evaluation.'
            )
        },
        {
            'keywords': ['stomach', 'vomit', 'nausea', 'diarrhea', 'abdominal'],
            'reply': (
                'For stomach upset, vomiting, or diarrhea, focus on hydration and note food exposure, pain location, '
                'blood in stool or vomit, fever, and duration. Severe abdominal pain, dehydration, blood, pregnancy, '
                'or symptoms lasting beyond 24-48 hours should be checked by a clinician.'
            )
        },
        {
            'keywords': ['sugar', 'diabetes', 'thirst', 'urination'],
            'reply': (
                'For diabetes-related concerns, track fasting and post-meal sugar values, thirst, urination, weight '
                'changes, blurred vision, and medication use. Very high sugar with vomiting, confusion, deep breathing, '
                'or dehydration requires urgent care.'
            )
        },
        {
            'keywords': ['blood pressure', 'bp', 'hypertension'],
            'reply': (
                'For blood pressure concerns, record readings after resting for 5 minutes and include the time, '
                'medications, salt intake, stress, and symptoms. Very high readings with chest pain, severe headache, '
                'weakness, confusion, or breathlessness need emergency care.'
            )
        },
        {
            'keywords': ['skin', 'rash', 'itch', 'allergy'],
            'reply': (
                'For skin or allergy concerns, note when it started, new foods or medicines, itching, swelling, fever, '
                'pain, or spreading redness. Swelling of lips or throat, breathing trouble, or rapidly spreading rash '
                'needs urgent care.'
            )
        }
    ]

    for topic in topics:
        if any(keyword in text for keyword in topic['keywords']):
            return topic['reply']

    return (
        'Tell me more about what you are feeling: when it started, severity from 1 to 10, your age, temperature or '
        'blood pressure if known, medicines you take, and anything that makes it better or worse. I can help you '
        'prepare clear next steps and questions for a qualified doctor.'
    )


def ai_doctor_reply(message, account):
    return local_ai_doctor_reply(message), 'Built-in health assistant'


def dashboard_data(account):
    history = account.get('history', [])
    assessments = [item for item in history if item.get('kind') == 'assessment']
    chats = [item for item in history if item.get('kind') == 'chat']
    reminders = [item for item in account.get('reminders', []) if not item.get('completed')]
    notes = account.get('notes', [])

    trend_items = []
    for item in reversed(assessments[:8]):
        metadata = item.get('metadata', {})
        trend_items.append({
            'title': item.get('title', 'Assessment'),
            'score': metadata.get('percentage', 0),
            'created_at': item.get('created_at', '')
        })

    high_risk_count = sum(
        1 for item in assessments
        if item.get('metadata', {}).get('risk') == 'High Risk'
    )

    return {
        'history': history[:6],
        'assessments': assessments,
        'chats': chats,
        'reminders': reminders[:5],
        'notes': notes[:4],
        'trend_items': trend_items,
        'stats': {
            'assessments': len(assessments),
            'chats': len(chats),
            'reminders': len(reminders),
            'notes': len(notes),
            'high_risk': high_risk_count
        }
    }


def generate_pdf(lines):
    escaped_lines = [
        line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        for line in lines
    ]
    text_commands = ['BT', '/F1 12 Tf', '50 780 Td', '16 TL']
    for index, line in enumerate(escaped_lines):
        if index == 0:
            text_commands.append(f'({line}) Tj')
        else:
            text_commands.append(f'T* ({line}) Tj')
    text_commands.append('ET')
    stream = '\n'.join(text_commands).encode('latin-1', errors='replace')

    objects = [
        b'1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj',
        b'2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj',
        b'3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj',
        b'4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj',
        b'5 0 obj << /Length ' + str(len(stream)).encode('ascii') + b' >> stream\n' + stream + b'\nendstream endobj'
    ]

    pdf = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj + b'\n')

    xref_start = len(pdf)
    pdf.extend(f'xref\n0 {len(objects) + 1}\n'.encode('ascii'))
    pdf.extend(b'0000000000 65535 f \n')
    for offset in offsets[1:]:
        pdf.extend(f'{offset:010d} 00000 n \n'.encode('ascii'))
    pdf.extend(
        f'trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF'.encode('ascii')
    )
    return bytes(pdf)


def find_history_entry(account, entry_id):
    for item in account.get('history', []):
        if item.get('id') == entry_id:
            return item

    return None


@app.route('/')
def home():
    return render_template(
        'index.html',
        categories=disease_groups(),
        disease_count=len(DISEASES)
    )


@app.route('/diseases/<disease_slug>', methods=['GET', 'POST'])
def disease_page(disease_slug):
    disease = DISEASES.get(disease_slug)

    if disease is None:
        abort(404)

    result = None
    submitted = {}

    if request.method == 'POST':
        submitted = {
            field['name']: request.form[field['name']]
            for field in disease['fields']
        }
        data = {
            field['name']: float(submitted[field['name']])
            for field in disease['fields']
        }

        result = detailed_prediction(data, submitted, disease)
        record_history(
            'assessment',
            disease['title'],
            f"{result['risk']} with a {result['percentage']} screening index",
            {
                'disease_slug': disease['slug'],
                'category': disease['category'],
                'risk': result['risk'],
                'percentage': result['percentage'],
                'inputs': submitted,
                'top_drivers': result['top_drivers'],
                'checks': result['checks']
            }
        )

    return render_template(
        'disease.html',
        disease=disease,
        related=[
            item for item in DISEASES.values()
            if item['category'] == disease['category']
        ],
        result=result,
        submitted=submitted
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        action = request.form.get('action', 'login')
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()

        if not username or not password:
            flash('Enter a username and password.')
            return redirect(url_for('login'))

        accounts = load_accounts()

        if action == 'register':
            if username in accounts:
                flash('That username already exists. Sign in instead.')
                return redirect(url_for('login'))

            accounts[username] = create_account(
                password_hash=generate_password_hash(password),
                full_name=full_name or username,
                email=email
            )
            if username == 'admin':
                accounts[username]['role'] = 'admin'
            save_accounts(accounts)
            session['username'] = username
            return redirect(url_for('complete_profile'))

        account = accounts.get(username)
        if account is None or not check_password_hash(account['password_hash'], password):
            flash('Invalid username or password.')
            return redirect(url_for('login'))

        session['username'] = username
        return redirect(request.args.get('next') or url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    account = current_user() or {}
    return render_template('dashboard.html', data=dashboard_data(account), profile=account.get('profile', {}))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    username = session['username']
    account = get_account(username)

    if request.method == 'POST':
        def updater(item):
            profile_data = item.setdefault('profile', default_profile())
            for field, _ in PROFILE_FIELDS:
                profile_data[field] = request.form.get(field, '').strip()
            item['full_name'] = profile_data.get('full_name') or username
            item['email'] = profile_data.get('email', '')

        account = update_account(username, updater)
        flash('Profile saved.')
        return redirect(url_for('dashboard'))

    return render_template('profile.html', profile=account.get('profile', {}), profile_fields=PROFILE_FIELDS)


@app.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    if request.method == 'POST':
        return profile()

    account = current_user() or {}
    return render_template(
        'profile.html',
        profile=account.get('profile', {}),
        profile_fields=PROFILE_FIELDS,
        onboarding=True
    )


@app.route('/chat')
@login_required
def chat():
    account = current_user() or {'history': []}
    chat_items = [
        item for item in account.get('history', [])
        if item.get('kind') == 'chat'
    ][:20]
    return render_template('chat.html', chat_items=chat_items)


@app.route('/chat/message', methods=['POST'])
@login_required
def chat_message():
    payload = request.get_json(silent=True) or {}
    message = payload.get('message', '').strip()

    if not message:
        return jsonify({'error': 'Message is required.'}), 400

    account = current_user() or {}
    reply, provider = ai_doctor_reply(message, account)
    record_history('chat', message[:80], reply, {'provider': provider})

    return jsonify({
        'reply': reply,
        'provider': provider,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
    })


@app.route('/history')
@login_required
def history():
    account = current_user() or {'history': []}
    query = request.args.get('q', '').strip().lower()
    kind = request.args.get('kind', '').strip()
    items = account.get('history', [])

    if kind:
        items = [item for item in items if item.get('kind') == kind]
    if query:
        items = [
            item for item in items
            if query in item.get('title', '').lower() or query in item.get('content', '').lower()
        ]

    return render_template('history.html', history_items=items, query=query, kind=kind)


@app.route('/reports/<entry_id>.pdf')
@login_required
def report_pdf(entry_id):
    account = current_user() or {}
    entry = find_history_entry(account, entry_id)

    if not entry or entry.get('kind') != 'assessment':
        abort(404)

    metadata = entry.get('metadata', {})
    lines = [
        'GeneCare AI Health Report',
        f"User: {account.get('full_name') or session.get('username')}",
        f"Assessment: {entry.get('title')}",
        f"Date: {entry.get('created_at')}",
        f"Result: {metadata.get('risk', 'N/A')}",
        f"Screening Risk Index: {metadata.get('percentage', 'N/A')}",
        '',
        'Inputs'
    ]
    for key, value in metadata.get('inputs', {}).items():
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    if metadata.get('top_drivers'):
        lines.extend(['', 'Most influential entered factors'])
        for driver in metadata['top_drivers']:
            lines.append(f"- {driver['label']}: {driver['value']} ({driver['points']} index points)")
    if metadata.get('checks'):
        lines.extend(['', 'Suggested follow-up discussion points'])
        for check in metadata['checks']:
            lines.append(f"- {check}")
    lines.extend([
        '',
        'Important: This report is educational and does not replace care from a qualified medical professional.'
    ])

    pdf = generate_pdf(lines)
    filename = f"gencare-{entry.get('title', 'report').lower().replace(' ', '-')}.pdf"
    return Response(
        pdf,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@app.route('/reminders', methods=['GET', 'POST'])
@login_required
def reminders():
    username = session['username']

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        due_date = request.form.get('due_date', '').strip()
        category = request.form.get('category', '').strip()

        if title:
            def updater(account):
                account.setdefault('reminders', []).insert(0, {
                    'id': uuid4().hex[:10],
                    'title': title,
                    'due_date': due_date,
                    'category': category,
                    'completed': False,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                })

            update_account(username, updater)
            flash('Reminder added.')

        return redirect(url_for('reminders'))

    account = current_user() or {}
    return render_template('reminders.html', reminders=account.get('reminders', []))


@app.route('/reminders/<reminder_id>/complete', methods=['POST'])
@login_required
def complete_reminder(reminder_id):
    def updater(account):
        for reminder in account.get('reminders', []):
            if reminder.get('id') == reminder_id:
                reminder['completed'] = True

    update_account(session['username'], updater)
    return redirect(url_for('reminders'))


@app.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    username = session['username']

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        body = request.form.get('body', '').strip()

        if title and body:
            def updater(account):
                account.setdefault('notes', []).insert(0, {
                    'id': uuid4().hex[:10],
                    'title': title,
                    'body': body,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                })

            update_account(username, updater)
            flash('Doctor note saved.')

        return redirect(url_for('notes'))

    account = current_user() or {}
    return render_template('notes.html', notes=account.get('notes', []))


@app.route('/admin')
@login_required
def admin():
    account = current_user()
    if not is_admin(account):
        abort(403)

    accounts = load_accounts()
    users = list(accounts.items())
    total_history = sum(len(item.get('history', [])) for _, item in users)
    total_chats = sum(
        1 for _, item in users
        for history_item in item.get('history', [])
        if history_item.get('kind') == 'chat'
    )
    total_assessments = sum(
        1 for _, item in users
        for history_item in item.get('history', [])
        if history_item.get('kind') == 'assessment'
    )
    high_risk = sum(
        1 for _, item in users
        for history_item in item.get('history', [])
        if history_item.get('metadata', {}).get('risk') == 'High Risk'
    )

    return render_template(
        'admin.html',
        users=users,
        stats={
            'users': len(users),
            'history': total_history,
            'chats': total_chats,
            'assessments': total_assessments,
            'high_risk': high_risk
        }
    )


if __name__ == '__main__':
    app.run(debug=True)
