import random
from datetime import datetime, timedelta
from supabase import create_client, Client

SUPABASE_URL = "https://rwcvjhpjnelefeuoajkq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3Y3ZqaHBqbmVsZWZldW9hamtxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkyMTM3ODcsImV4cCI6MjEwNDc4OTc4N30.8XkTZys3WGP5JiJIo6-MlQeCmtlMJJS0EwRvFcIj-8I"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

first_names = ["Juan", "Maria", "Jose", "Ana", "Carlos", "Rosa", "Pedro", "Elena", "Miguel", "Lucia"]
last_names = ["Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Aquino", "Garcia", "Mendoza", "Torres", "Flores"]
doctors = ["Dr. Smith", "Dr. Cruz", "Dr. Reyes", "Dr. Santos"]
statuses = ["Completed", "Waiting", "Cancelled"]

print("Seeding 300 records into Supabase PostgreSQL...")

for i in range(1, 301):
    patient_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    doctor_id = random.choice(doctors)
    
    random_days = random.randint(-30, 30)
    appointment_date = (datetime.now() + timedelta(days=random_days)).strftime("%Y-%m-%d")
    status = random.choice(statuses)
    
    data = {
        "patient_name": patient_name,
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "status": status
    }
    
    supabase.table("appointments").insert(data).execute()

print("Successfully seeded 300 records into your Supabase database!")
