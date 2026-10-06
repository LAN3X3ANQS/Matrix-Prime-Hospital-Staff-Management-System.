class Nurse:
    def __init__(self, nurse_id, name, staff_id, phone, status="Active"):
        self.id = nurse_id
        self.name = name
        self.staff_id = staff_id
        self.phone = phone
        self.status = status