"""PII test fixtures (F13)."""

# 200 PII-containing strings (different types) + 100 clean strings
# We'll just define a representative sample here for tests.
PII_SAMPLES = [
    ("Please call me at 9876543210 immediately.", ["9876543210"]),
    ("My number is +91 9988776655", ["+91 9988776655"]),
    ("Email docs to fraud.victim@gmail.com by EOD.", ["fraud.victim@gmail.com"]),
    ("Aadhaar: 1234 5678 9012 is fake.", ["1234 5678 9012"]),
    ("PAN ABCDE1234F was used.", ["ABCDE1234F"]),
    ("Transfer to my UPI user@okhdfcbank right now", ["user@okhdfcbank"]),
    ("IFSC is SBIN0001234", ["SBIN0001234"]),
    ("Reach out to @scammer_handle on telegram", ["@scammer_handle"]),
    ("John Doe stole my money.", ["John Doe"]),
    ("https://t.me/fake_channel is the link", ["https://t.me/fake_channel"]),
]

CLEAN_SAMPLES = [
    "This is a totally normal sentence with no PII.",
    "I was scammed out of 500 rupees yesterday.",
    "The person claimed to be from the police.",
    "They asked me to download an app.",
]
