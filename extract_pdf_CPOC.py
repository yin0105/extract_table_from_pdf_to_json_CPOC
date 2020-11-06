import tabula
import pdfplumber
import pandas as pd
import sys
import os
from datetime import datetime
import time
import re  


def write_into_file(content):
    my_file.write(content)

# Change multiline of a cell to json
def multiline_to_json(s):
    rr = ""
    for ss in s.splitlines():
        if ss.find(":") > -1:
            sss = '"' + remove_special_characters(ss.split(":", 1)[0]) + '": "' + remove_special_characters(ss.split(":", 1)[1]) + '"'
        else:
            sss = '"' + remove_special_characters(ss) + '": ""'
        if rr != "" and sss != "": rr += ", "
        rr += sss
    return rr

def remove_special_characters(content):
    # return ''.join(e for e in content if e.isalnum() or e == ' ')
    return content.replace('"', '\\"').strip()

def remove_space(ss):
    s = list(ss)
    s = [i.strip() for i in s]
    return "".join(s)
    

# datetime object containing current date and time
now = datetime.now()
dt_string = now.strftime("%Y-%m-%d_%H-%M-%S")

# Get pdf file name from command line
if len(sys.argv) == 1:
    print("INPUT TYPE: python extract_pdf.py pdf_file_name [output_path]")
    exit()
elif len(sys.argv) >= 2:
    pdf_file = sys.argv[1]
    output_path = "."
    if len(sys.argv) > 2: output_path = sys.argv[2]

filename = os.path.basename(pdf_file)
filename = filename[:filename.rfind(".")] + ".json"
already_defined_report_header = False

# Get row data of the tables in a pdf file using tabula and Save them as array
df = tabula.read_pdf(pdf_file, pages="all", guess = False, multiple_tables = True) 
t_word = []
for a in df:
    t_word_page = []
    for i in range(len(a.index)):
        count = 0
        t_word_tmp = []
        for c in a:
            ss = str(a.loc[i, c])
            if ss != "nan" and ss.strip() != "":
                t_word_tmp.append(" ".join(ss.splitlines()))
        t_word_page.append(t_word_tmp)
        
    t_word.append(t_word_page)

# 19/10/2020 - To add missing attributes

field_name = t_word[0][00][0].split(' ')[0]
branch_name = ""
if len(t_word[0][00][0].split(' ')) > 2 : branch_name = t_word[0][00][0].split(' ')[1] + ' ' + t_word[0][00][0].split(' ')[2]
start_depth = ""
if len(t_word[0][00][0].split(' ')) > 3 : start_depth = t_word[0][00][0].split(' ')[3]
rig_name = "DEEP DRILLER 4"
well_name = t_word[0][3][0].split(rig_name)[0].strip()
if t_word[0][3][0][-14:] == rig_name:
    phase = t_word[0][3][1]
else:
    phase = t_word[0][3][0].split(rig_name)[1].replace('"', '\\"')
company_representatives = f"{t_word[0][1][1]}, {t_word[0][2][1]}"
# report_no = t_word[0][0][2].split('RPT #:')[1].strip()
report_no = ''.join(t_word[0][0]).split('RPT #:')[1].strip()
well_name = t_word[0][3][0].split(rig_name)[0].strip()
next_ = " ".join(t_word[0][2])
next_ = next_[next_.find("Next :") + 6:next_.find("Midnight Depth")]
next_ = next_.strip()
midnight = " ".join(t_word[0][3]).split(" ")
midnight_1 = ""
midnight_2 = ""

if (type(midnight[-1]) == int or float) and (type(midnight[-2]) == int or float):
    midnight_1 = midnight[-2]
    midnight_2 = midnight[-1]

# ['Melati Original Hole 103.74', 'Company Man', 'OD (in) Depth (mMD/mTVD) RPT #: 1']
# ['Melati Original Hole 190.00', 'Company Man', 'OD (in)', 'Depth (mMD/mTVD) RPT #:', '5']

# Make json structure for the report header
report_header_info = '"ReportHeader":{' \
    + f'"Field Name":"{field_name}",' \
    + f'"Branch Name":"{branch_name}",' \
    + f'"Start Depth (m)":"{start_depth}",' \
    + f'"Well Name":"{well_name}",' \
    + f'"Rig":"{rig_name}",' \
    + f'"Phase":"{phase}",' \
    + f'"Company Representatives":"{company_representatives}",' \
    + f'"Report No":"{report_no}",' \
    + f'"Next":"{next_}",' \
    + f'"Midnight Depth mMD":"{midnight_1}",' \
    + f'"Midnight Depth mTVD":"{midnight_2}"' \
    + '}, \n'

# Parse a pdf file with pdfplumber
pdf = pdfplumber.open(pdf_file) 

# Open output text file
# filename = "output.json"
my_file = open(f"{output_path}\\temp.txt", "w", encoding="utf8")
write_into_file("{\n")

# Main Working Flow
page_num = 0 # current page number (1 ~ )
find_page_num = 0
write_started = False # Whether writing started


# Iterate through pages
for p0 in pdf.pages:
    page_num += 1 # Increase current page
    find_page_num += 1
    cell = [] # An array of index of cell data
    word = [] # An array of cell data
    # Parse the tables of PDF
    table = p0.extract_table(table_settings={"vertical_strategy": "lines"})    
    # Change table to DataFrame of Pandas
    df = pd.DataFrame(table[0:], columns=table[0])

    # Set an array of index of cell data and an array of cell data
    # Iterate through rows
    bit_data_flag = False
    
    vess_start = False
    survey_data_start = False
    for i in range(len(df.index)):
        # my_file.write("line " + str(i) + " : ")
        count = 1
        cell_temp = []
        
        # Iterate through columns
        for j in  range(len(df.columns)):
            
            ss = str(df.iloc[i, j])
            # my_file.write(str(j) + ":" + ss + "  ")          
            if ss != "None" :
                word.append(ss)
                count += 1
                if j == 15 and ss == "Vessel Name":
                    vess_start = True
                if j == 20 and ss == "Survey Data":
                    survey_data_start = True
                if ss == "Operation Summary": survey_data_start = False
                # if not (ss == "" and word[len(word) - 1] == "Time Log"):
                #     word.append(ss)
                #     count += 1
                #     if j == 15 and ss == "Vessel Name":
                #         vess_start = True
            else:
                # if word[len(word) - 1] == "Time Log": print("ok" + str(j))
                # if j == 20 and word[len(word) - 1] == "Time Log" : print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                if j == 0 or (j == 20 and word[len(word) - 1] == "6.00") or (i == 10 and j == 33) or (j == 15 and vess_start) or (j == 20 and survey_data_start) or (j == 33 and word[len(word) - 1] == "Summary/Remarks") or (j == 20 and word[len(word) - 1] == "Time Log") or (j == 20 and word[len(word) - 1] == "Dur (hr)") or (j == 20 and word[len(word) - 1] == "Dur (hr)") or (j == 30 and word[len(word) - 1].find("Current Direction (°)") == 0)or (j == 20 and word[len(word) - 1].find("Cum Dur") == 0):
                    word.append("")
                    count += 1

            cell_temp.append( len(word) - 1)
        cell.append(cell_temp)
        # my_file.write("\n")

    # Main Working Flow
    # Iterate through rows
    for i in range(len(df.index) - 1):  
        # Iterate through columns
        for j in  range(len(df.columns)):
            ss = ""
            if cell[i][j] == -1: continue
            # Get cell number of data
            for k in range(j + 1, len(df.columns)): 
                if cell[i][k] != cell[i][j]: break
            else:
                if k == len(df.columns) - 1: k = len(df.columns)
            k -= 1
            # data (or key of group)
            ww_2 = " ".join(word[cell[i][j]].splitlines()) 
            if ww_2 == "": 
                cell[i][j] = -1
                continue
            # Whether data is group
            # print("ww_2 = " + ww_2 + " i = " + str(i) + " j = " + str(j) + " k = " + str(k))
            if i < len(df.index) - 2 and k > j: 
                if (j == 0 or (j > 0 and cell[i+1][j-1] != cell[i+1][j])) and (k == len(df.columns) - 1 or (k < len(df.columns) - 1 and (cell[i+1][k] != cell[i+1][k+1])) or ww_2 in ["Time Log", "Summary/Remarks"]) and (cell[i+1][j] != cell[i+1][k] or ww_2 in ["Mud", "Time Log", "Survey Data", "Operation Summary", "Variable Load", "Well Status at 6:00 am", "Planned Operation", "Safety Drills", "Accidents", "Mud Total", "Mud Cum to Date", "Cum to Date", "Day Total", "Personnel", "Weather Conditions", "Summary/Remarks", "Standby Boat", "Variable Load"]) :
                    # Get the number of rows in a group
                    for ii in range(i+2, len(df.index) - 1): 
                        if ww_2 == "Mud" and word[cell[ii][j]] == "Mud Products": break
                        if ww_2 == "Supply Boats" and word[cell[ii][j]] == "Weather Conditions": break
                        if ww_2 == "Time Log" and word[cell[ii][j]] == "Operation Summary": break
                        if ww_2 == "Survey Data" and word[cell[ii][j]] == "Summary/Remarks": break

                        if ww_2 == "Weather Conditions" and word[cell[ii][j]] == "Anchors": break
                        if ww_2 == "BHA Information" and word[cell[ii][j]] == "Drilling Parameters": break
                        if ww_2 == "Drilling Parameters" and word[cell[ii][j]] == "Directional": break
                        if ww_2 == "Leak Off and Formation Integrity Tests" and word[cell[ii][j]] == "Casing Pressure Tests": break
                        if ww_2 == "Casing Pressure Tests" and word[cell[ii][j]] == "BOP Pressure Tests": break
                        if ww_2 == "BOP Pressure Tests" and word[cell[ii][j]] == "Equipment Pressure Test Data": break
                        if ww_2 == "Standby Boat" and word[cell[ii][j]] == "Variable Load": break
                        if ww_2 == "Variable Load" and word[cell[ii][j]] == "Weather Conditions": break
                        if not ((j == 0 or (j > 0 and cell[ii][j-1] != cell[ii][j]) or (j > 0 and cell[ii][j-1] == cell[ii][j] and cell[ii][j] == cell[ii][k])) and (k == len(df.columns) - 1 or (k < len(df.columns) - 1 and (cell[ii][k] != cell[ii][k+1] or (cell[ii][k] == cell[ii][k+1] and ww_2 in ["Time Log", "Survey Data", "Summary/Remarks"])))) and (cell[ii][j] != cell[ii][k] or ww_2 in ["Mud", "Time Log", "Survey Data", "Operation Summary", "Variable Load", "Planned Operation", "Accidents", "Cum to Date", "Mud Total", "Mud Cum to Date", "Day Total", "Safety Drills", "Well Status at 6:00 am", "Personnel", "Supply Boats", "Standby Boat", "Weather Conditions", "Summary/Remarks"])) and (ww_2 == "Mud Products" and cell[ii][j]!=cell[ii][k]) : break
                        if not(ww_2 in ["Mud", "Time Log", "Survey Data", "Operation Summary", "Variable Load", "Planned Operation", "Accidents", "Mud Total", "Mud Cum to Date", "Day Total", "Cum to Date", "Safety Drills", "Well Status at 6:00 am", "Personnel", "Supply Boats", "Standby Boat", "Weather Conditions"]):
                            if ww_2 == "Time Log": 
                                if cell[ii][j+1] == cell[ii][k]:
                                    continue
                                else:
                                    break
                            elif ww_2 in ["Mud", "Mud Products"] and (cell[ii][j+1] == cell[ii][k] or cell[ii-1][j+1] == cell[ii-1][k]):
                                    continue
                            else:
                                for jj in range(j+1, k+1): 
                                    if cell[ii][jj] - cell[ii-1][jj] != cell[ii][j] - cell[ii-1][j]:break
                                else:
                                    continue
                                break
                    else:
                        if ii < i + 2: ii = i + 2                        
                        if ii == len(df.index) - 2 : ii += 1
                    
                    if ww_2 == "Time Log":
                        pre_cell = -2
                        header = []
                        # Get the column headers in a group
                        for jj in range(j, k + 1):
                            if cell[i+1][jj] != pre_cell:
                                header.append(" ".join(word[cell[i+1][jj]].splitlines()))
                                pre_cell = cell[i+1][jj]
                        # Get the columns data in group
                        for iii in range(i + 2, ii): 
                            group_column_num = 0
                            tmp_list = []
                            pre_cell = -2
                            # Get cell data
                            for jj in range(j, k + 1):
                                if cell[i+1][jj] != pre_cell:
                                    tmp_list.append( word[cell[iii][jj]])
                                    pre_cell = cell[i+1][jj]
                                cell[iii][jj] = -1

                            # Split cell data to multiple rows
                            if len(tmp_list) > 0 and tmp_list[0] == "" and tmp_list[2] != "":
                                # write_into_file('"time_log_comment": "' + remove_special_characters(tmp_list[2]) + '"')
                                if ss != "": ss += ", \n"
                                ss += '{"Start Time": "", "End Time": "", "Comment": "' + remove_special_characters(" ".join(tmp_list[2].splitlines())) + '", "Code": "", "Dur (hr)": "" } '
                                # ss = '"time_log_comment": "' + remove_special_characters(tmp_list[2]) + '"'
                            pre_comp_str = ""
                            while len(tmp_list) > 0 and len(tmp_list[0].splitlines()) > 0:
                                f_ok = False
                                # Get data of the first line of the first column
                                comp_str = tmp_list[0].splitlines()[-1].strip() 
                                pre_comp_str = comp_str
                                
                                # Compare data of word array with comp_str and Set data
                                for t_a in t_word[find_page_num - 1]:
                                    for t_b in t_a:
                                        # Whether Is there comp_str in data of word array
                                        if t_b.find(comp_str.strip()) > -1 :
                                            f = False
                                            for c in tmp_list:  
                                                if len(c.splitlines()) == 0: continue                                           
                                                for t_c in t_a:
                                                    if t_c.find(c.splitlines()[-1].strip()) > -1:  
                                                        f = True
                                                        break
                                                if f == False: break
                                            # If there is comp_str in data of word array, check other data
                                            if f == True:                                                
                                                for t_c in t_a:
                                                    if len(tmp_list) == 0: break
                                                    if len(tmp_list[0].splitlines()) ==0: break
                                                    if t_c.find(tmp_list[0].splitlines()[-1].strip()) == -1: continue
                                                    ssss = ""
                                                    tt = tmp_list[:]
                                                    for c in range(len(tmp_list)):
                                                        sss = ""                                               
                                                        if len(tmp_list[c].splitlines()) == 0 :
                                                            sss = header[c] + ":   "
                                                            continue    

                                                        tt[c] =  tmp_list[c]                                                 
                                            
                                                        for c_len in range(len(tt[c].splitlines())):
                                                            for t_d in t_a:
                                                                # print("t_d = " + t_d)
                                                                # print("t_c = " + tt[c].splitlines()[len(tt[c].splitlines())- c_len -1].strip())
                                                                # if t_d.find(tt[c].splitlines()[len(tt[c].splitlines())- c_len -1].strip()) > -1:
                                        
                                                                if remove_space(str(t_d)).find(remove_space(tt[c].splitlines()[len(tt[c].splitlines())- c_len -1].strip())) > -1:
                                                                    cc = "  ".join(tt[c].splitlines()[len(tt[c].splitlines())- c_len -1:])
                                                                    sss = '"' + header[c] + '": "' + remove_special_characters("  ".join(tt[c].splitlines())) + '" '
                                                                    tt[c] = ""
                                                                    break
                                                            else:
                                                                continue
                                                            break
                                                        else:
                                                            break
                                                        if ssss != "": ssss += ", "
                                                        ssss += sss
                                                    else:
                                                        if ss == "":
                                                            ss = '{' + ssss + '}'
                                                        else:    
                                                            ss += ', {' + ssss + '}'
                                                        tmp_list = tt[:]
                                                    f_ok = True


                                                if ss != "" and ss != "\n": ss += "\n"
                                                if len(tmp_list) == 0: 
                                                    # write_into_file("\n")
                                                    write_into_file(ss)
                                                    break
                                if not f_ok: find_page_num += 1
                            if tmp_list[0] == "" : 
                                if len(tmp_list[4].splitlines()) > 0 and tmp_list[4].splitlines()[0] == "Cum Dur" and len(tmp_list[4].splitlines()) > 1:
                                    ss = ss[:-1] + ', \n{"Cum Dur": "' + str(tmp_list[4].splitlines()[1]) + '"}'

                        for jj in range(j, k + 1):
                            cell[i+1][jj] = -1

                    elif ww_2 in ["Penetration", "Bit", "Parameters", "Drillstring Assembly", "Survey Data", "Mud Products", "Personnel", "Supply Boats", "Standby Boat", "Variable Load", "Main Stock"]:
                        # col header
                        pre_cell = -2
                        header = []
                        # Get the columns data in group
                        for jj in range(j, k + 1):
                            if cell[i+1][jj] != pre_cell:
                                header.append(remove_special_characters(" ".join(word[cell[i+1][jj]].splitlines())))
                                pre_cell = cell[i+1][jj]
                            cell[i+1][jj] = -1
                        # Get the columns data in group
                        for iii in range(i + 2, ii): 
                            if ww_2 == "Mud Products" and cell[iii][j] == cell[iii][k]: 
                                continue
                            header_cc = 0
                            sss = ""
                            if remove_special_characters(" ".join(word[cell[iii][j]].splitlines())) == "": 
                                if iii == i + 2:
                                    while header_cc < len(header):
                                        if sss != "": sss += ", "
                                        sss += '"' + header[header_cc] + '": ""'
                                        header_cc += 1
                                    sss = '{' + sss + '}'
                                    if ss != "": ss += ", "
                                    ss += sss
                                continue

                            for jj in range(j, k + 1):
                                if cell[iii][jj] != pre_cell:
                                    if header[header_cc] != "":
                                        if sss != "": sss += ", "
                                        sss += '"' + header[header_cc] + '": "' + remove_special_characters(" ".join(word[cell[iii][jj]].splitlines())) + '" '
                                    pre_cell = cell[iii][jj]
                                    header_cc += 1
                                cell[iii][jj] = -1
                                
                            sss = '{' + sss + '}'
                            if ss != "": ss += ", "
                            ss += sss                    

                    elif ww_2 in ["Mud", "Daily Operations", "Daily Cost/Time Summary", "Mud/Fluid Checks", "Weather Conditions", "BHA Information", "Drilling Parameters", "Leak Off and Formation Integrity Tests", "Casing Pressure Tests", "BOP Pressure Tests"]:
                        pre_cell = -2
                        ss += "{\n"
                        mud_type_appear = False
                        for iii in range(i + 1, ii): 
                            sss = ""
                            if ww_2 == "Mud" and cell[iii][j] == cell[iii][k]:
                                print("####################")
                                print(word[cell[iii][j]])
                                print("####################")
                                if not mud_type_appear : 
                                    mud_type_appear = True
                                    print(str(cell[iii][j]) + " :: " + str(pre_cell))
                                    if cell[iii][j] != pre_cell:
                                        print("1")
                                        if sss != "" and word[cell[iii][j]] != "": sss += ", "  
                                        ww = " ".join(word[cell[iii][j]].splitlines()) 
                                        print("2")
                                        if len(word[cell[iii][j]].splitlines()) > 0 :
                                            print("3")
                                            if remove_special_characters(word[cell[iii][j]].splitlines()[0]) == "Summary/Remarks" : continue
                                            tmp_key = remove_special_characters(word[cell[iii][j]].splitlines()[0])
                                            if tmp_key[-1] == ":": tmp_key = tmp_key[:-1]
                                            sss += '"' + tmp_key + '": "'
                                            if len(word[cell[iii][j]].splitlines()) > 1 : 
                                                sss += remove_special_characters(word[cell[iii][j]].splitlines()[1])
                                            sss += '"'
                                        pre_cell = cell[iii][j]
                                        print("sss = " + sss)
                                        if sss != "":
                                            if ss != "{\n": ss += ", "
                                            ss += sss

                                for jj in range(j, k + 1):
                                    cell[iii][jj] = -1
                                continue
                            
                            for jj in range(j, k + 1):
                                if cell[iii][jj] != pre_cell:
                                    if sss != "" and word[cell[iii][jj]] != "": sss += ", "  
                                    ww = " ".join(word[cell[iii][jj]].splitlines()) 
                                    if len(word[cell[iii][jj]].splitlines()) > 0 :
                                        if remove_special_characters(word[cell[iii][jj]].splitlines()[0]) == "Summary/Remarks" : continue
                                        tmp_key = remove_special_characters(word[cell[iii][jj]].splitlines()[0])
                                        if ww_2 == "Mud":
                                            if tmp_key == "YS (lbf/100ft²": tmp_key = "YS (lbf/100ft²)"
                                            if tmp_key == ")PV (cp)": tmp_key = "PV (cp)"
                                            if tmp_key == "CEC (me/hg": tmp_key = "CEC (me/hg)"
                                            if tmp_key == "Filt. (ml/30 mi": tmp_key = "Filt. (ml/30 min)"
                                            if tmp_key == "nF)C (mm)": tmp_key = "FC (mm)"
                                            if tmp_key == "HPHT Filt. (ml/3": tmp_key = "HPHT Filt. (ml/30min)"
                                            if tmp_key == "0H mPiHn)T FC (m": tmp_key = "HPHT FC (m)"
                                        sss += '"' + tmp_key + '": "'
                                        if len(word[cell[iii][jj]].splitlines()) > 1 : 
                                            sss += remove_special_characters(word[cell[iii][jj]].splitlines()[1])
                                        sss += '"'
                                    pre_cell = cell[iii][jj]
                                cell[iii][jj] = -1
                            if sss != "":
                                if ss != "{\n": ss += ", "
                                ss += sss
                        ss += "}"

                    elif ww_2 in ["Operation Summary", "Planned Operation", "Accidents", "Mud Total", "Mud Cum to Date", "Cum to Date", "Safety Drills", "Well Status at 6:00 am", "Day Total"]:
                        ww_2 += ':' + " ".join(word[cell[i+1][j]].splitlines())   
                        for iiii in range(i, i + 2):
                            cc = cell[iiii][j]
                            for jjjj in range(j, len(df.columns)):
                                if cell[iiii][jjjj] == cc:
                                    cell[iiii][jjjj] = -1
                                else:
                                    break
                    elif ww_2 in ["Summary/Remarks"]:
                        ww_2 += ':' + " ".join(word[cell[i+1][j]].splitlines()) 
                        for iiii in range(i, ii):
                            cc = cell[iiii][j]
                            for jjjj in range(j, len(df.columns)):
                                if cell[iiii][jjjj] == cc:
                                    cell[iiii][jjjj] = -1
                                else:
                                    break
                    elif ww_2 in []:
                        pre_cell = -2
                        ss += "{\n"
                        for iii in range(i + 1, ii): 
                            sss = ""
                            for jj in range(j, k + 1):
                                if cell[iii][jj] != pre_cell:
                                    if sss != "" and word[cell[iii][jj]] != "": sss += ", "  
                                    ww = " ".join(word[cell[iii][jj]].splitlines()) 
                                    if len(word[cell[iii][jj]].split(":")) > 0 :
                                        sss += '"' + remove_special_characters(word[cell[iii][jj]].split(":")[0]) + '": "'
                                        if len(word[cell[iii][jj]].split(":")) > 1 : 
                                            sss += remove_special_characters(" ".join(word[cell[iii][jj]].split(":")[1].splitlines()))
                                        sss += '"'
                                    pre_cell = cell[iii][jj]
                                cell[iii][jj] = -1
                            if sss != "":
                                if ss != "{\n": ss += ", "
                                ss += sss
                        ss += "}"

                        
                    else: # etc group
                        pre_cell = -2
                        for iii in range(i + 1, ii): 
                            sss = ""
                            for jj in range(j, k + 1):
                                if cell[iii][jj] != pre_cell:
                                    if sss != "" and word[cell[iii][jj]] != "": sss += ", "
                                    ww = " ".join(word[cell[iii][jj]].splitlines()) 
                                    sss += word[cell[iii][jj]]
                                    pre_cell = cell[iii][jj]
                                cell[iii][jj] = -1
                            if sss != "":
                                sss = '{' + sss + '}'
                                
                                if ss != "": ss += ", "
                                ss += sss
            # Output to output file
            if ww_2 != "": 
                ww_2 = remove_special_characters(ww_2)
                if write_started:
                    write_into_file(", \n")
                if ss != "" and ss[0] == "{": 
                    ww_2 = '"' + ww_2 + '": [\n'
                elif ww_2.find(":") > -1:
                    if ww_2.find("Well Status at 6:00 am") > -1 :
                        ww_2 = '"Well Status at 6:00 am": "' + ww_2[24:] + '"'
                    else:    
                        ww_2 = '"' + remove_special_characters(ww_2.split(":", 1)[0]) + '": "' + ww_2.split(":", 1)[1] + '"'
                elif len(ww_2.splitlines()) > 1:
                    ww_2 = '"' + remove_special_characters(ww_2.splitlines()[0]) + '": "' + "  ".join(ww_2.splitlines()[1:]) + '"'
                else:
                    ww_2 = remove_special_characters(ww_2)
                    ww_2 = '"' + ww_2 + '": ""'

                

                if ww_2.__contains__('Penetration') and not already_defined_report_header:
                    already_defined_report_header = True
                    write_into_file(report_header_info + ww_2)
                else:
                    write_into_file(ww_2)
                write_started = True

            
            if ss != "": write_into_file(ss)

            if ww_2 != "" and ss != "" and ss[0] == "{": write_into_file('\n]')
            for jj in range(j, k+1):
                cell[i][jj] = -1

write_into_file("\n")
write_into_file("}")
my_file.close()

print(f"{output_path}\{filename}")
output_file = open(f"{output_path}\{filename}", "w", encoding="utf8")
input_file = open(f"{output_path}\\temp.txt", "r", encoding="utf8")
ss = input_file.read()

remove_array = ['"Personnel": [\n{"Company": "", "Qty": ""}\n],', 
'"Penetration": [\n{"Bit Run": "", "Start (m)": "", "End (m)": "", "Interval (m)": "", "Time (hr)": "", "ROP (m/hr)": "", "Cum Depth (m)": "", "Cum Time (hr)": "", "Tot ROP (m/hr)": ""}\n],', 
'"Bit": [\n{"Bit and Core Head Inventory": "", "Bit Dull": "", "Nozzle (32nd\\")": "", "TFA (in²)": ""}\n],', 
'"Parameters": [\n{"WOB (kip)": "", "RPM (rpm)": "", "Flow (L/min)": "", "SPP (psi)": "", "On Btm (ft-lbf)": ""}\n], ', 
'"Drillstring Assembly": [\n{"BHA Run": "", "BHA": ""}\n],', 
'"Day Total": "",',
'"Cum to Date": "",', 
'"Mud Total": "",', 
'"Mud Cum to Date": "",', 
'"Main Stock": [\n{"Supply Item": "", "Unit": "", "Receive": "", "Used": "", "Stock": ""}\n],', 
'"Supply Boats": [\n{"Vessel Name": "", "Date arrival": "", "Depart": ""}\n],', 
'"Weather Conditions": [\n{\n"Wave Height (m)": "", "Wave Period (sec)": "", "Wave Direction (°)": "", "Wind Speed (knots)": "", "Wind Direction (°)": "", "P Bar (mbar)": "", "Current Speed (knots)": "", "Current Direction (°)": ""}\n],', 
'"Standby Boat": [\n{"Vessel Name": ""}\n],',
'"Variable Load": [\n{"Max Variable Load (kip)": ""}\n],'
]

for ra in remove_array:
    ss = ss.replace(ra + " \n", '')

first_start_pos = 0
first_end_pos = 0
start_pos = 0
while True:
    cur_pos = ss.find('\"Time Log\": [', start_pos)
    if cur_pos == -1: break
    end_pos = ss.find("]", cur_pos)
    if start_pos != 0:
        part_str = ss[cur_pos + 14:end_pos]                
        ss = ss[:first_end_pos] + ",\n" + part_str + "\n" + ss[first_end_pos:cur_pos] + ss[end_pos+2:]
        first_end_pos = ss.find("]", first_start_pos)        
    else:
        first_start_pos = cur_pos
        first_end_pos = end_pos
    start_pos = first_end_pos + 1

str_1 = '{"Start Time": "", "End Time": "", "Comment": "'
while ss.find(str_1) > -1:    
    start_pos = ss.find(str_1)
    end_pos = ss.find('", "Code":', start_pos)
    add_comment = ss[start_pos + len(str_1): end_pos]
    end_pos = ss.find("}", start_pos)    
    ss = ss[:start_pos-4] + ss[end_pos + 1:]
    
    str_2 = '"Comment": "'
    start_pos = ss[:start_pos].rfind(str_2)
    end_pos = ss.find('" , "Code":', start_pos)
    ori_comment = ss[start_pos + len(str_2): end_pos]
    ss= ss[:start_pos + len(str_2)] + ori_comment + " " + add_comment + ss[end_pos:]

    
start_pos = ss.find("{\"Cum Dur\":")
if start_pos > -1:
    end_pos = ss.find("}", start_pos)
    part_str = ss[start_pos + 13 : end_pos - 1]
    ss = ss[:start_pos] + '{"Start Time": "" , "End Time": "" , "Comment": "" , "Code": "" , "Dur (hr)": "Cum Dur ' + part_str + '" }' + ss[end_pos + 1:]

# Summary/Remarks
first_start_pos = 0
first_end_pos = 0
start_pos = 0
while True:
    cur_pos = ss.find('"Summary/Remarks": "', start_pos)
    if cur_pos == -1: break
    search_pos = cur_pos + 20
    while True:
        end_pos = ss.find('"', search_pos)
        if ss[end_pos-1] != '\\': break
        search_pos += 1

    if start_pos != 0:
        part_str = ss[cur_pos + 20:end_pos]                
        ss = ss[:first_end_pos] + " " + part_str + ss[first_end_pos:cur_pos] + ss[end_pos+2:]
        first_end_pos = ss.find("]", first_start_pos)        
    else:
        first_start_pos = cur_pos
        first_end_pos = end_pos
    start_pos = first_end_pos + 1

output_file.write(ss)
input_file.close()
output_file.close()
os.remove("temp.txt")

