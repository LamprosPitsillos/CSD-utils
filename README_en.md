# CSD-utils
A collection of cli tools for UOC CSD students

# PRE-ALPHA TOOL

This was made to make life a bit easier , nothing serious 
## Notes

+ Solving for dependencies was aufull , because the is no consistency in the way they're given
+ I take no responability for anything. Use at your own risk !

## Requirements

+ Python >3.9
+ Firefox to fetch grades ( Chrome might work, not tested )
+ Tested on Linux 

## Running

+ Clone repo
+ `cd CSD-utils`
+ `pip install -r requirements.txt`
+ `python src/scraper.py --help`

# Get progression on Degree completion

+ `python src/scraper.py degree --help`
    
# Export semester's scedule in an easy to work with format

+ `python src/scraper.py courses --help`

## Example:

+ `❯ python src/scraper.py courses --format csv > possible_courses.csv`
+ Open `libreoffice` or `google docs` and import csv with delimiter '|'
+ Make your schedule however you like
