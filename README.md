# process_payslips
Scrapes important info from my payslips and outputs it in a master excel file.

The shellscript does all the heavy lifting: this uses the pdftotext program to extract the text from the payslip pdfs and passes this to python program which then parses the text for the relevant information and writes it to an excel spreadsheet. The shellscript then moves the pdf to the a folder for the corresponding financial year.
I also combined this with the MacOS program Automator to automatically run my shellscript whenever I download a new payslip.
