import base64
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

app = FastAPI()

# --- CONFIGURATION ---
PRIVATE_KEY_PATH = "student_private.pem"
# FOR LOCAL WINDOWS TESTING: Use "." (current folder). 
# FOR DOCKER (Later): Change this back to "/data"
DATA_DIR = "." 
SEED_FILE = os.path.join(DATA_DIR, "seed.txt")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# --- DATA MODELS ---
class DecryptRequest(BaseModel):
    encrypted_seed: str

# --- CORE LOGIC ---
def decrypt_seed_logic(encrypted_seed_b64: str):
    try:
        # 1. Load Private Key
        if not os.path.exists(PRIVATE_KEY_PATH):
            raise FileNotFoundError(f"Could not find {PRIVATE_KEY_PATH}")

        with open(PRIVATE_KEY_PATH, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )

        # 2. Decode Base64 Input
        # Clean up any newlines just in case
        encrypted_seed_b64 = encrypted_seed_b64.strip()
        ciphertext = base64.b64decode(encrypted_seed_b64)

        # 3. Decrypt using RSA-OAEP
        decrypted_bytes = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # 4. Decode to String and Validate
        decrypted_seed = decrypted_bytes.decode('utf-8')
        
        if len(decrypted_seed) != 64:
            raise ValueError("Decrypted seed length is not 64 characters")
        
        return decrypted_seed

    except Exception as e:
        print(f"Decryption Logic Error: {str(e)}")
        raise e

# --- ENDPOINTS ---

@app.post("/decrypt-seed")
async def decrypt_seed_endpoint(request: DecryptRequest):
    try:
        print(f"🔹 Received decryption request...")
        seed = decrypt_seed_logic(request.encrypted_seed)
        
        with open(SEED_FILE, "w") as f:
            f.write(seed)
            
        print("✅ Seed decrypted and saved to seed.txt")
        return {"status": "ok"}
        
    except Exception as e:
        print(f"❌ Endpoint Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Decryption failed")

@app.get("/")
def health_check():
    return {"status": "running"}