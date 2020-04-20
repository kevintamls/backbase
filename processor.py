''' Assumptions:
    1. All accounts balance start at 0.
    2. Csv files are only valid in format 'customer-xxxxxxx-ledger.csv', where xxxxxxx is a
        7 digit number with integers between 0-9 for each character.
    3. Savings account can't drop below 0.
    4. Import format in columns order AccountID, AccountType, InitiatorType, DataTime,
    TransactionValue
    5. System initiated transactions are initiated immediately post detection of negative
       current account balance and where savings amount permit a transafer to current
       account.
'''

# Import modules Pandas, fnmatch, os
import pandas as pd
import fnmatch
import os
import sys

# Function to import CSV as Pandas Dataframe
def dataImport():
    # Pattern for file name checking
    pattern = 'customer-[0-9][0-9][0-9][0-9][0-9][0-9][0-9]-ledger.csv'

    # Current Execution directory containing all csv files
    directory = os.getcwd()

    # List variablesfor Dataframe and Filename
    filenames = []
    dataframes = []

    # Filter out irrelevant files 
    for filename in os.listdir(directory):
        if fnmatch.fnmatchcase(filename, pattern):
            filenames.append(filename)
            continue
        else:
            continue
    
    # Check if there are any valid files to process and exits program if there are none
    if len(filenames) == 0:
        sys.exit('Error: No Valid files to process, exiting')

    # Print number of files to process
    print('There are ' + str(len(filenames)) + ' valid files to process')
    
    # Import relevant files into dataframe, converter to leave 0 by converting into string        
    for files in filenames:
        dataframes.append(pd.read_csv(files, converters={
                          'AccountID': lambda x: str(x)}))
    #print(dataframes[1])
    return filenames, dataframes

# Function for data processing
def dataProcessing(dataframe):
    # Print indicator of processing for user
    print('Files are now being processed. Please wait.')

    # List to store processed dataframes
    processedDF = []

    # Iterator to keep track of how many files have been processed
    fileNumber = 1
    # For loop to process data per dataframe
    for i, df in enumerate(dataframe):
        print('Processing File ' + str(fileNumber))
        # Check if imported CSV dataframe is correct for processing, if not skips file
        if not {'AccountID', 'AccountType', 'InitiatorType', 'DataTime', 'TransactionValue'}.issubset(df.columns):
            print('File ' + str(fileNumber) + ' is not in the correct format. Skipping.')
            pass

        # 2 copies of dataframe to process, one to iterate, one to modify
        currentDF = dataframe[i].copy()
        modifiedDF = dataframe[i].copy()
        
        # Iterator to keep track of how many rows have been added for correct index insertion
        rowsAdded = 0

        # Initialise Assumption: All accounts balances start with 0
        currentAccountBalance = 0
        savingsAccountBalance = 0

        # Current/Savings account number definition. Locate AccountID where
        # AccountType = CURRENT/SAVINGS
        currentAccountNo = currentDF.loc[currentDF.AccountType == 
                                         'CURRENT', 'AccountID'].values[0]
        savingsAccountNo = currentDF.loc[currentDF.AccountType ==
                                         'SAVINGS', 'AccountID'].values[0]

        # For loop to iterate through each row in dataframe. Itertuples used for performance
        for row in currentDF.itertuples():
            # Add/Subtraction of Current Account Balance
            if (currentDF.iat[int(row.Index),1]) == 'CURRENT':
                # Locate value of transaction
                currentTransaction = currentDF.iat[int(row.Index), 4]
                # Add transaction to current account balance
                currentAccountBalance += currentTransaction

                # Nested if loop, when current Account Balance is below 0
                if currentAccountBalance < 0:
                    # Nested if loop, do nothing if savings is at 0 or below
                    if savingsAccountBalance <= 0:
                        # print('You currently have no savings')
                        continue
                    
                    # Else if there are sufficient funds from savings to return current account
                    # balance to 0, calculate amount required for transfer and add/deduct to current
                    # or savings respectively. Abs needed to convert balance to positive number for 
                    # comparison
                    elif abs(currentAccountBalance) < savingsAccountBalance:
                        # Amount to transfer to current account = positive of negative account balance
                        currentToCredit = abs(currentAccountBalance) 
                        # Amount to debit from savings = Deficit of current account balance
                        savingsToDebit = currentAccountBalance
                        currentAccountBalance += currentToCredit # Credit of current account
                        savingsAccountBalance += savingsToDebit # Debit of savings account
                        # print('Sufficient funds transfered from savings to current account. No overdraft charges are being applied.')
                    
                    # Else if there are insufficient funds from savings to return current account
                    # balance to 0 but savings balance is more than 0, transfer all savings to current
                    # account to reduce overdraft costs.
                    elif abs(currentAccountBalance) >= savingsAccountBalance and savingsAccountBalance > 0:
                        currentToCredit = savingsAccountBalance # Paying off from all savings
                        savingsToDebit = -abs(currentToCredit) # Debit all savings
                        currentAccountBalance += currentToCredit # Credit of current account
                        savingsAccountBalance += savingsToDebit # Debit of savings account
                        # print('Insufficient funds transfered from savings to current account. Overdraft charges may apply.')

                    # DataFrame Modification: Savings Debit + Current Credit
                    savingsToAppend = pd.DataFrame({'AccountID': savingsAccountNo, 'AccountType': 'SAVINGS',
                                                    'InitiatorType': 'SYSTEM', 'DataTime': [currentDF.iat[int(row.Index), 3]], 
                                                    'TransactionValue': savingsToDebit}, index=[int(row.Index)+ 0.5 + rowsAdded])
                    
                    currentToAppend = pd.DataFrame({'AccountID': currentAccountNo, 'AccountType': 'CURRENT',
                                                    'InitiatorType': 'SYSTEM', 'DataTime': [currentDF.iat[int(row.Index), 3]], 
                                                    'TransactionValue': currentToCredit}, index=[int(row.Index)+ 0.75 + rowsAdded])

                    # Use of second copy of dataframe to append to
                    modifiedDF = modifiedDF.append(savingsToAppend, ignore_index=False)
                    modifiedDF = modifiedDF.append(currentToAppend, ignore_index=False)
                    modifiedDF = modifiedDF.sort_index().reset_index(drop=True)
                    rowsAdded += 2 # Add 2 to rowadded iterator to maintain proper indexing for modification
        
            # Add/Subtraction of Savings Account Balance
            elif(currentDF.iat[int(row.Index), 1]) == 'SAVINGS':
                # Location of savings transaction value
                savingsTransaction = currentDF.iat[int(row.Index), 4]
                # Add transaction into savings account balance
                savingsAccountBalance += savingsTransaction

                # If there are savings and current balance < 0, transfer immediately
                if currentAccountBalance < 0 and savingsAccountBalance > 0:
                    currentToCredit = savingsAccountBalance  # Paying off from all savings
                    savingsToDebit = -abs(currentToCredit) # Amount to debit = Calculated current credit required
                    currentAccountBalance += currentToCredit # Credit of current account
                    savingsAccountBalance += savingsToDebit # Debit of savings account

                    # DataFrame Modification: Savings Debit + Current Credit
                    savingsToAppend = pd.DataFrame({'AccountID': savingsAccountNo, 'AccountType': 'SAVINGS',
                                                    'InitiatorType': 'SYSTEM', 'DataTime': [currentDF.iat[int(row.Index), 3]],
                                                    'TransactionValue': savingsToDebit}, index=[int(row.Index) + 0.5 + rowsAdded])

                    currentToAppend = pd.DataFrame({'AccountID': currentAccountNo, 'AccountType': 'CURRENT',
                                                    'InitiatorType': 'SYSTEM', 'DataTime': [currentDF.iat[int(row.Index), 3]],
                                                    'TransactionValue': currentToCredit}, index=[int(row.Index) + 0.75 + rowsAdded])

                    # Use of second copy of dataframe to append to
                    modifiedDF = modifiedDF.append(savingsToAppend, ignore_index=False)
                    modifiedDF = modifiedDF.append(currentToAppend, ignore_index=False)
                    modifiedDF = modifiedDF.sort_index().reset_index(drop=True)
                    rowsAdded += 2 # Add 2 to rowadded iterator to maintain proper indexing for modification

        # Append modified dataframe into processed dataframe list
        processedDF.append(modifiedDF)
        # Add 1 to amount of file proccessed
        fileNumber += 1
    # Return full processed dataframe
    return (processedDF)

# Function for data export
def dataExport(filenames, dataframe):
    # New list to store modified csv names
    modifiedNameList = []

    # For loop to modify file names
    for i in range(len(filenames)):
        # Strings immutable, thus new variable
        modifiedFileName = filenames[i].replace('.csv', '-modified.csv')
        modifiedNameList.append(modifiedFileName)

    # For loop to export dataframe data to CSV
    for i, df in enumerate(dataframe):
        dataframe[i].to_csv(modifiedNameList[i], index=False)
    
    # Indicator to show processing complete
    print('Processing Complete')

# Main Function
filenames, raw_data = dataImport()
processed_data = dataProcessing(raw_data)
dataExport(filenames, processed_data)
