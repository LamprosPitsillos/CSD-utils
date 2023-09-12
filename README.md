[Eng Readme](./README_en.md) 
# CSD-utils
Μια συλλογή cli tools για φοιτητές CSD του Πανεπιστημίου Κρήτης

# PRE-ALPHA ΕΡΓΑΛΕΙΟ

Αυτό δημιουργήθηκε για να διευκολύνει λίγο τη ζωή, τίποτα σοβαρό
## Notes:

+ Η επίλυση των εξαρτήσεων ήταν δύσκολη, επειδή δεν υπάρχει συνέπεια στο πως ειναι γραμμένες
+ Δεν αναλαμβάνω καμία ευθύνη για οτιδήποτε. Χρησιμοποιήστε το με δική σας ευθύνη!

## Απαιτήσεις

+ Python >3.9
+ Firefox για τη λήψη των βαθμολογιών (Το Chrome μπορεί να λειτουργήσει, δεν έχει δοκιμαστεί)

## Εκτέλεση

+ Clone repo
+ `cd CSD-utils`
+ `pip install -r requirements.txt`
+ `python src/scraper.py --help`

# Λήψη προόδου στην ολοκλήρωση του βαθμού

+ `python src/scraper.py degree --help`
    
# Εξαγωγή προγράμματος σεμιναρίου σε εύκολο μορφή για επεξεργασία

+ `python src/scraper.py courses --help`

## Παράδειγμα:

+ `❯ python src/scraper.py courses --format csv > possible_courses.csv`
+ Ανοίξτε το `libreoffice` ή το `google docs` και εισαγάγετε το CSV με διαχωριστικό '|'
+ Δημιουργήστε το πρόγραμμά σας όπως θέλετε
