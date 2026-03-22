"""
Configuration - static constants for the application.
"""

DEPARTMENT_NAME = "FOREX"

TO_RECIPIENT = "zeeshan@gmail.com"

EMAIL_LISTS = {
    "APAC": [
        "chen.yun@gmail.com",
        "akira.tanaka@apacmail.com",
        "priya.sharma@apacmail.com",
        "min.ji.kim@apacmail.com",
        "ali.hassan@emeamail.com",
    ],
    "EMEA": [
        "sophie.dubois@emeamail.com",
        "ali.hassan@emeamail.com",
        "tom.schmidt@emeamail.com",
        "lucas.nielsen@emeamail.com",
        "anastasia.popov@emeamail.com",
    ],
    "AMERICAS": [
        "michael.smith@americasmail.com",
        "carla.martinez@americasmail.com",
        "kevin.johnson@americasmail.com",
        "daniela.gomez@americasmail.com",
        "thiago.silva@americasmail.com",
    ],
}

SERVICES = ["BD", "MR V", "MR L", "RN", "RN SN", "DGT", "SAM", "CRT", "RXL"]

USERS = ["GLOBAL", "APAC", "EMEA", "AMERICAS"]

SERVICE_STATUSES = ["Degraded", "Unavailable", "Under Observation", "Available"]