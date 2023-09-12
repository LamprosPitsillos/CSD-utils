[Eng Readme](./README_en.md) 
# CSD-utils
Μια συλλογή cli tools για φοιτητές CSD του Πανεπιστημίου Κρήτης

# PRE-ALPHA ΕΡΓΑΛΕΙΟ ⚠️

Αυτό δημιουργήθηκε για να διευκολύνει λίγο τη ζωή, τίποτα σοβαρό
## Notes:

+ Η επίλυση των εξαρτήσεων ήταν δύσκολη, επειδή δεν υπάρχει συνέπεια στο πως ειναι γραμμένες
+ Δεν αναλαμβάνω καμία ευθύνη για οτιδήποτε. Χρησιμοποιήστε το με δική σας ευθύνη!

## Απαιτήσεις

+ Python >3.9
+ Firefox για τη λήψη των βαθμολογιών (Το Chrome μπορεί να λειτουργήσει, δεν έχει δοκιμαστεί)
+ Tested on Linux 

## Εκτέλεση

+ Clone repo
+ `cd CSD-utils`
+ `pip install -r requirements.txt`
+ `python src/scraper.py --help`

# Λήψη προόδου στην ολοκλήρωση του βαθμού

+ `python src/scraper.py degree --help`
   ![image](https://github.com/LamprosPitsillos/CSD-utils/assets/61395246/8aa42cb3-ebbc-49ea-bb53-53a0cb533c9b)

# Εξαγωγή προγράμματος σεμιναρίου σε εύκολο μορφή για επεξεργασία

+ `python src/scraper.py courses --help`

## Παράδειγμα:

+ `❯ python src/scraper.py courses --format csv > possible_courses.csv`
+ Ανοίξτε το `libreoffice` ή το `google sheets` και εισαγάγετε το CSV με διαχωριστικό '|'
+ Δημιουργήστε το πρόγραμμά σας όπως θέλετε
![image](https://github.com/LamprosPitsillos/CSD-utils/assets/61395246/7908dfda-8a4c-4661-b600-124e04970810)
