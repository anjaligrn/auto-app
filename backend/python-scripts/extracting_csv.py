import sys, csv, os, shutil

def delete_all_contents_in_folder(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path):
        print(f"The folder '{folder_path}' does not exist.")
        return

    # List all files and directories in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Remove the file or link
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Remove the directory and its contents
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def extract_bill_values(file_path):
    moa_values = []
    totals_values = []
    uns_values = []
    tva_list = []
    bill_reference = ""
    formatted_date = ""
    advance_value = 0
    to_pay = 0
    
    try:
        # Open file with specified encoding
        with open(file_path, 'r', encoding='ISO-8859-1') as file:
            # Read all lines from the file
            lines = file.readlines()
            first_line = lines[0].strip()
    except FileNotFoundError:
        print(f"Error: The text file you're trying to get formatted named '{file_path}' can't be found.")
        sys.exit(1)

    # Loop through each line by index for more control
    for i, line in enumerate(lines):
        if "EDI" not in first_line:
            print("The file you provided is not an EDI file.")
            sys.exit(1)

        # Searching for the fourth line, where the date resides 
        if i + 1 == 4:
            parts = line.split('+')[1]
            date_info = parts.split(':')[1] 

            # Format the new date string
            if len(date_info) == 8:  # Check if date info is of the correct length
                year = date_info[:4]
                month = date_info[4:6]
                day = date_info[6:]
                formatted_date = f"{day}/{month}/{year}" 

        # Searching for the third line, where the bill reference resides 
        if i + 1 == 3:
            bill_reference = line.split('+')[2]
    
        # Check if the current line starts with 'IMD'
        if line.startswith('IMD'):
            if i > 0 and not lines[i - 1].startswith('PIA'):
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()

                    if next_line.startswith('MOA'):
                        next_line = next_line.rstrip("'")
                        parts = next_line.split('+')

                        if len(parts) > 1:
                            moa_value_part = parts[1].split(':')
                            if len(moa_value_part) > 1:
                                moa_value = moa_value_part[1]
                                moa_values.append(moa_value)
                        break  # Stop once you find the MOA after IMD

        # Check if the current line starts with 'UNS'
        if line.startswith('UNS'):
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                    
                if next_line.startswith('MOA'):
                    if len(parts) > 1:
                        next_line = next_line.rstrip("'")
                        parts = next_line.split('+')
                        moa_value_part = parts[1].split(':')                    

                    if len(moa_value_part) > 1:
                        moa_value = moa_value_part[1]
                        uns_values.append(moa_value)
                        totals_values.append(moa_value)

                tva_values = uns_values[-2:]
                tva_list = [float(i) for i in tva_values]

                tva = round(sum(tva_list), 2)

    total = max(totals_values, default=0)  # Handle case where totals_values is empty
    total = round(float(total), 2)

    for num in totals_values:
        num = float(num)
        if num < 0:
            advance_value = num
            to_pay = total + num

    bill_values = {
        'articles_values': moa_values,
        'advance': advance_value,
        'tva': tva,
        'net_payable': to_pay,
        'reference': bill_reference,
        'date': formatted_date
    }

    return bill_values

# Main execution logic
def formating_csv():
    if __name__ == "__main__": 
        if len(sys.argv) > 1: 
            edi_filename = sys.argv[1]

            bill_values = extract_bill_values(edi_filename)

            if isinstance(bill_values, str):
                print(bill_values)  # If extract_bill_values returned an error message
                return

            # Put all the values of debit of articles in an array
            articles = bill_values['articles_values']

            # Save the extracted values to a CSV file
            with open("totals_values.csv", "w", newline='', encoding='utf-8') as f:
                data = [
                    {"JOURNAL": "ACM", "DATE": bill_values['date'], "GENERAL": "401000", "AUXILIAIRE": "", "REFERENCE": bill_values['reference'], "LIBELLE": "Achat MB " + bill_values['reference'], "DEBIT": "", "CREDIT": bill_values['net_payable']},
                    {"JOURNAL": "ACM", "DATE": bill_values['date'], "GENERAL": "411000", "AUXILIAIRE": "", "REFERENCE": bill_values['reference'], "LIBELLE": "Achat MB " + bill_values['reference'], "DEBIT": bill_values['advance'], "CREDIT": ""},          
                    {"JOURNAL": "ACM", "DATE": bill_values['date'], "GENERAL": "445660", "AUXILIAIRE": "", "REFERENCE": bill_values['reference'], "LIBELLE": "Achat MB " + bill_values['reference'], "DEBIT": bill_values['tva'], "CREDIT": ""},          
                ]

                for i in articles:
                    data.append({"JOURNAL": "ACM", "DATE": bill_values['date'], "GENERAL": "", "AUXILIAIRE": "", "REFERENCE": bill_values['reference'], "LIBELLE": "Achat MB " + bill_values['reference'], "DEBIT": i, "CREDIT": ""})

                writer = csv.writer(f)

                # Write the headers first
                fieldnames = ["JOURNAL", "DATE", "GENERAL", "AUXILIAIRE", "REFERENCE", "LIBELLE", "DEBIT", "CREDIT"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

                print("Your EDI text file has been formatted and saved in 'totals_values.csv'")
        else:
            print("Usage: python3 extracting_csv.py <text_filename>")
            sys.exit(1)

# Call the main execution logic
formating_csv()

folder_path = './uploads'
delete_all_contents_in_folder(folder_path)