import pandas as pd
from faker import Faker
import random
import os
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)
random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

NUM_PATIENTS = 50
NUM_VISITS = 150
NUM_BILLS = 150

def generate_patients(n):
    patients = []
    for _ in range(n):
        patients.append({
            "patient_id": fake.uuid4(),
            "name": fake.name(),
            "age": random.randint(18, 90),
            "gender": random.choice(["Male", "Female", "Other"]),
            "chronic_condition": random.choice(["None", "Diabetes", "Hypertension", "Asthma", "Heart Disease", "Arthritis"]),
            "registration_date": fake.date_between(start_date='-5y', end_date='today').isoformat()
        })
    return pd.DataFrame(patients)

def generate_visits(patients_df, n):
    visits = []
    patient_ids = patients_df["patient_id"].tolist()
    
    for _ in range(n):
        pid = random.choice(patient_ids)
        v_date = fake.date_between(start_date='-2y', end_date='today')
        visits.append({
            "visit_id": fake.uuid4(),
            "patient_id": pid,
            "visit_date": v_date.isoformat(),
            "diagnosis": random.choice(["Flu", "Checkup", "Fracture", "Viral Infection", "Covid-19", "Migraine", "Sprain"]),
            "procedure": random.choice(["Consultation", "X-Ray", "Blood Test", "Vaccination", "MRI", "Surgery"]),
            "doctor_name": "Dr. " + fake.last_name()
        })
    return pd.DataFrame(visits)

def generate_billing(visits_df, n):
    billing = []
    visit_ids = visits_df["visit_id"].tolist()
    
    # Not every visit results in a bill in this simplistic model, or maybe 1-to-1. Let's do 1-to-1 mostly.
    # Actually let's just make bills for existing visits.
    for vid in visit_ids:
        billing.append({
            "bill_id": fake.uuid4(),
            "visit_id": vid,
            "amount": round(random.uniform(50.0, 5000.0), 2),
            "status": random.choice(["Paid", "Pending", "Insurance Processed", "Overdue"]),
            "payment_date": fake.date_between(start_date='-1y', end_date='today').isoformat()
        })
    return pd.DataFrame(billing)

def main():
    print(f"Generating synthetic data in {DATA_DIR}...")
    
    patients_df = generate_patients(NUM_PATIENTS)
    patients_path = os.path.join(DATA_DIR, "patients.csv")
    patients_df.to_csv(patients_path, index=False)
    print(f"Saved {len(patients_df)} patients to {patients_path}")

    visits_df = generate_visits(patients_df, NUM_VISITS)
    visits_path = os.path.join(DATA_DIR, "visits.csv")
    visits_df.to_csv(visits_path, index=False)
    print(f"Saved {len(visits_df)} visits to {visits_path}")

    billing_df = generate_billing(visits_df, NUM_BILLS)
    billing_path = os.path.join(DATA_DIR, "billing.csv")
    billing_df.to_csv(billing_path, index=False)
    print(f"Saved {len(billing_df)} bills to {billing_path}")

if __name__ == "__main__":
    main()
