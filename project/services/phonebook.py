import os
import csv

class PhonebookService:
    
    def __init__(self, path):
        self.n2p = {} # name to phone mapping
        self.p2n = {} # phone to name mapping
        self.load(path)

    def load(self, path: str):
        if not os.path.exists(path):
            raise Exception("[error] Phonebook file not found")
        if not path.endswith(".csv"):
            raise Exception("[error] Phonebook service only suppports csv files")
        with open(path, 'r', encoding='utf-8', errors='ignore') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            
            for row in reader:
                try:
                    first_name = row.get('First Name')
                    display_name = row.get('Display Name')
                    
                    phone_home = row.get('Home Phone')
                    phone_business = row.get('Business Phone')
                    phone_mobile = row.get('Mobile Phone')

                    phones = []
                    names = []

                    if first_name and first_name.strip():
                        names.append(first_name.lower())

                    if display_name and display_name.strip():
                        names.append(display_name.lower())


                    if phone_home and phone_home.strip():
                        if not phone_home.startswith("+91"):
                            phone_home = f"+91{phone_home}"
                        phones.append(phone_home.lower().strip().replace("-", "").replace(" ", ""))

                    if phone_business and phone_business.strip():
                        if not phone_business.startswith("+91"):
                            phone_business = f"+91{phone_business}"
                        phones.append(phone_business.lower().strip().replace("-", "").replace(" ", ""))

                    if phone_mobile and phone_mobile.strip():
                        if not phone_mobile.startswith("+91"):
                            phone_mobile = f"+91{phone_mobile}"
                        phones.append(phone_mobile.lower().strip().replace("-", "").replace(" ", ""))

                    for p in phones:
                        self.p2n[p] = names

                    for n in names:
                        self.n2p[n] = phones

                    
                except Exception as e:
                    print(f"[error] Skipping row due to error: {e}")
            

    def list_entries(self):
        # print(self.p2n)
        # print(self.n2p)
        return self.p2n, self.n2p

    def find_by_name(self, name: str):
        try:
            return self.n2p[name]
        except KeyError:
            return None

    def find_by_id(self, id: str):
        try:
            return self.p2n[id]
        except KeyError:
            return None
