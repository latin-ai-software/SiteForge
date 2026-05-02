from cryptography.fernet import Fernet

key = b"fRJNJuUuJyX001nAQnsLS7sVgf-xEyCL7cy9qgHSX18="
f = Fernet(key)

for path in ["data\\settings.json", "data\\users.json", "data\\posts_metadata.json", "data\\comments.json", "data\\analytics.json"]:
    with open(path, "rb") as f_in:
        data = f_in.read()
    decrypted = f.decrypt(data)
    with open(path.replace(".enc", ""), "wb") as f_out:
        f_out.write(decrypted)