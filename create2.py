import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "陳彥閔",
  "mail": "bruce20060120@gmail.com",
  "lab": 801
}

doc_ref = db.collection("靜宜資管").document("MINNN01")
doc_ref.set(doc)
