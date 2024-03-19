import os
import csv
import time
from google.cloud import firestore


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../webapp/clipboard-service-account.json"

db = firestore.Client()

with open("stats.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    stats = list(reader)[-1]
    for stat in stats:
        stats[stat] = int(stats[stat])


new_stats = {"timestamp": int(time.time())}
users = db.collection(u"users").stream()
users = list(users)
new_stats["users"] = len(users)

verified_users = [user for user in users if user.to_dict()[
    "email_token"] == "verified"]
new_stats["verified_users"] = len(verified_users)

clipboards = db.collection(u"clipboards").stream()
clipboards = list(clipboards)
new_stats["active_clipboards"] = len(clipboards)

hours_old = (time.time() - stats["timestamp"]) / (60 * 60)
minutes_old = ((time.time() - stats["timestamp"]) / 60) % 60
print(f"last run {int(hours_old)} hours, {int(minutes_old)} minutes, ago:")
for stat in stats:
    if stat == "timestamp":
        continue
    print(f"{stat}: {new_stats[stat]} +{new_stats[stat] - stats[stat]}")

with open('stats.csv', 'a') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([new_stats[stat] for stat in new_stats])
