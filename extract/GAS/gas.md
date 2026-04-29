# GAS

## Random code

```sh
="aud-"&LOWER(DEC2HEX(RANDBETWEEN(0, 4294967295), 8))
```

## Prompt

I have a GAS attached to a spreadsheet. Looks like this:

- A audit_id
- B CITY/TOWN
- C YEAR
- D NEIGHBORHOOD
- E SUMMARY
- F LONG TERM RECOMMENDATIONS
- G SHORT TERM RECOMMENDATIONS
- H STREETS, INNTERSECTIONS + AREA COVERED
- I THEMES
- J VIEW
- K FACILITATOR/AUTHOR
- L ORGANIZATIONS

In Column J, View, the content always says "PDF" but contains a hyperlink to the actual PDF.

In services, I enabled Drive v3.

### Task

Iterate over every row. Get the link pdf.

Create a new folder.

Inside my "output" folder: <https://drive.google.com/drive/folders/1P1WA-XSYyN0t1trstik1AiCWX9M8sAs>_

Create or use the folder CITY/TOWN + "/" + YEAR + "/" + audit_id.

Inside that folder, make a copy of the pdf.

Then, convert to a google doc and put the doc inside that folder, too.

## Formulas

```sh
# audit date
=GEMINI("Identify the exact date the walk audit took place given the provided text. Return the date in YYYY-MM-DD format, or empty string if unclear. If only the day and month are available, use the first day of that month. The date must match the project year: " & C2, M2)

# report date
=GEMINI("Identify the date written on the report using the provided text. Return the date in YYYY-MM-DD format, or empty string if unclear. If only the day and month are available, use the first day of that month. The date must match the project year: " & C2, M2)

# start address
=GEMINI("Identify the exact start address of the walk audit using the text provided in " & M2 & ". Use the city in " & D2 & " and the state MA to return a complete address. If unclear, return an empty string.", M2)

# neighborhood
=GEMINI("Identify the neighborhood of the walk audit using the text provided in " & M2 & ". It should be a sub-region of the given city " & D2 & " in the state MA. Just return the neighborhood name, or empty string if missing or unclear", M2)
```
