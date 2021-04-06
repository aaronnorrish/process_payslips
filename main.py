import re
import fileinput
import pandas as pd
import os.path

from openpyxl import load_workbook

def process():
    # fields of interest: pay period, net pay, wage, tax, leave, super
    
    fields = ['Period Start', 'Period End', 'Hours Worked', 'Pay', 'Tax', 'Super',
       'Leave', 'Net Pay', 'Pay Rate', 'Notes']
    data = dict.fromkeys(fields)

    leave = "0.0"

    super_guar_it = 0.0
    super_guar_ad = 0.0
    tax = 0.0

    for line in fileinput.input():
        line = line.rstrip()
        pay_rate_exp = re.search("Hourly Rate:\s+\$([\d,]+\.\d+)", line)
        if pay_rate_exp is not None:
            pay_rate = re.sub(",", "", pay_rate_exp.group(1))

        pay_period = re.search("Pay Period\s+From:\s+(\d{1,2})/(\d{1,2})/(\d{4})\s+To:\s+(\d{1,2})/(\d{1,2})/(\d{4})", line)
        if pay_period is not None:
            start_date = '{0}/{1}/{2}'.format(pay_period.group(1), pay_period.group(2), pay_period.group(3))
            end_date = '{0}/{1}/{2}'.format(pay_period.group(4), pay_period.group(5), pay_period.group(6))

        net_pay_exp = re.search("NET PAY:\s+\$([\d,]+\.\d+)", line)
        if net_pay_exp is not None:
            net_pay = re.sub(",", "", net_pay_exp.group(1))
    
        wages_exp = re.search("Base Hourly\s+(\d+\.\d+)\s+\$([\d,]+\.\d+)\s+\$([\d,]+\.\d+)\s+\$([\d,]+\.\d+)\s+Wages\s*$", line)
        if wages_exp is not None:
            hours = wages_exp.group(1)
            wages = re.sub(",", "", wages_exp.group(3)) 

        wages_exp = re.search("Base Salary\s+\$([\d,]+\.\d+)\s+\$([\d,]+\.\d+)\s+Wages\s*$", line)
        if wages_exp is not None:
            wages = re.sub(",", "", wages_exp.group(1)) 
            hours = str(float(wages)/float(pay_rate))

        tax_exp = re.search("PAYG Withholding\s+(-?\$[\d,]+\.\d+)\s+(-?\$[\d,]+\.\d+)\s+Tax\s*$", line)
        if tax_exp is not None:
            tax_exp = re.sub(",", "", tax_exp.group(1)) 
            tax = re.sub("\$", "", tax_exp)

        leave_exp = re.search("Holiday Leave Accrual\s+(\d+\.\d+)\s+([\d,]+\.\d+)\s+Entitlements\s*$", line)
        if leave_exp is not None:
            leave = leave_exp.group(1) 

        super_exp = re.search("Super Guarantee.*?IT.*?\s+\$([\d,]+\.\d+)\s+\$([\d,]+\.\d+)\s+Superannuation Expenses\s*$", line)
        if super_exp is not None:
            super_guar_it = re.sub(",", "", super_exp.group(1)) 

        super_exp = re.search("Super Guarantee.*?Admin.*?\s+\$([\d,]+\.\d+)\s+\$([\d,]+\.\d+)\s+Superannuation Expenses\s*$", line)
        if super_exp is not None:
            super_guar_ad = re.sub(",", "", super_exp.group(1)) 

    notes = "" 

    data['Period Start'] = [start_date]
    data['Period End'] = [end_date]
    data['Hours Worked'] = [float(hours)]
    data['Pay'] = [float(wages)]
    data['Tax'] = [float(tax)]
    data['Super'] = [float(super_guar_it) + float(super_guar_ad)]
    data['Leave'] = [float(leave)]
    data['Net Pay'] = [float(net_pay)] 
    data['Pay Rate'] = [float(pay_rate)] 
    data['Notes'] = [notes]

    return data

def determine_sheet(date):
    date_exp = re.search("^(\d{1,2})/(\d{1,2})/(\d{4})\s*$", date)
    month = date_exp.group(2)
    year = date_exp.group(3)
    if int(month) >= 7:
        return year + "-" + str(int(year[-2:])+1)
    else:
        return str(int(year)-1) + "-" + year[-2:]

def output(data, excel_file):
    fields = ['Period Start', 'Period End', 'Hours Worked', 'Pay', 'Tax', 'Super', 'Leave', 'Net Pay',  'Pay Rate', 'Notes']
    req_sheet = determine_sheet(data['Period Start'][0])

    new_df = pd.DataFrame.from_dict(data)

    if os.path.isfile(excel_file):
        ws_dict = pd.read_excel(excel_file, sheet_name=None)
        if req_sheet in ws_dict.keys():
            ws_dict[req_sheet] = pd.concat([ws_dict[req_sheet], new_df], ignore_index=True, sort=False)
            ws_dict[req_sheet]['Period Start'] = pd.to_datetime(ws_dict[req_sheet]['Period Start'], format='%d/%m/%Y')
            ws_dict[req_sheet] = ws_dict[req_sheet].sort_values(by='Period Start',ascending=True)
            ws_dict[req_sheet]['Period Start'] = ws_dict[req_sheet]['Period Start'].dt.strftime('%d/%m/%Y')
        else:
            new_df = new_df[fields]
            ws_dict[req_sheet] = new_df
    else:
        new_df = new_df[fields] 
        ws_dict = {}
        ws_dict[req_sheet] = new_df


    writer = pd.ExcelWriter(excel_file, engine='openpyxl')
    for ws_name, df_sheet in ws_dict.items():
        df_sheet.to_excel(writer, sheet_name=ws_name, index=False)
    writer.save()
    writer.close()

if __name__== "__main__":
    output(process(), "test.xlsx")
