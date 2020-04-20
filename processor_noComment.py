import pandas as pd
import fnmatch
import os
import sys

def dataImport():
    pattern = 'customer-[0-9][0-9][0-9][0-9][0-9][0-9][0-9]-ledger.csv'
    directory = os.getcwd()
    filenames = []
    dataframes = []
 
    for filename in os.listdir(directory):
        if fnmatch.fnmatchcase(filename, pattern):
            filenames.append(filename)
        else:
            pass
    
    if len(filenames) == 0:
        sys.exit('Error: No Valid files to process, exiting')
           
    for files in filenames:
        dataframes.append(pd.read_csv(files, converters={
                          'AccountID': lambda x: str(x)}))
    
    for i, df in enumerate(dataframes):
        if not {'AccountID', 'AccountType', 'InitiatorType', 'DataTime', 'TransactionValue'}.issubset(df.columns):
            del dataframes[i]
            del filenames[i]

    print('There are ' + str(len(filenames)) + ' valid files to process')
    return filenames, dataframes

def dataProcessing(dataframe):
    print('Files are now being processed. Please wait.')
    processedDF = []
    fileNumber = 1

    for i, df in enumerate(dataframe):
        print('Processing File ' + str(fileNumber))
        currentDF = dataframe[i].copy()
        modifiedDF = dataframe[i].copy()
        rowsAdded = 0
        currentAccountBalance = 0
        savingsAccountBalance = 0
        currentAccountNo = currentDF.loc[currentDF.AccountType == 
                                         'CURRENT', 'AccountID'].values[0]
        savingsAccountNo = currentDF.loc[currentDF.AccountType ==
                                         'SAVINGS', 'AccountID'].values[0]

        for row in currentDF.itertuples():
            if (currentDF.iat[int(row.Index),1]) == 'CURRENT':
                currentTransaction = currentDF.iat[int(row.Index), 4]
                currentAccountBalance += currentTransaction

                if currentAccountBalance < 0:
                    if savingsAccountBalance <= 0:
                        # print('You currently have no savings')
                        pass
                    elif abs(currentAccountBalance) < savingsAccountBalance:
                        currentToCredit = abs(currentAccountBalance) 
                        savingsToDebit = currentAccountBalance
                        currentAccountBalance += currentToCredit 
                        savingsAccountBalance += savingsToDebit 
                        # print('Sufficient funds transfered from savings to current account. No overdraft charges are being applied.')
                    elif abs(currentAccountBalance) >= savingsAccountBalance and savingsAccountBalance > 0:
                        currentToCredit = savingsAccountBalance 
                        savingsToDebit = -abs(currentToCredit) 
                        currentAccountBalance += currentToCredit 
                        savingsAccountBalance += savingsToDebit 
                        # print('Insufficient funds transfered from savings to current account. Overdraft charges may apply.')

                    savingsToAppend = pd.DataFrame({'AccountID': savingsAccountNo, 'AccountType': 'SAVINGS',
                                                    'InitiatorType': 'SYSTEM', 'DataTime': [currentDF.iat[int(row.Index), 3]], 
                                                    'TransactionValue': savingsToDebit}, index=[int(row.Index)+ 0.5 + rowsAdded])
                    
                    currentToAppend = pd.DataFrame({'AccountID': currentAccountNo, 'AccountType': 'CURRENT',
                                                    'InitiatorType': 'SYSTEM', 'DataTime': [currentDF.iat[int(row.Index), 3]], 
                                                    'TransactionValue': currentToCredit}, index=[int(row.Index)+ 0.75 + rowsAdded])

                    modifiedDF = modifiedDF.append(savingsToAppend, ignore_index=False)
                    modifiedDF = modifiedDF.append(currentToAppend, ignore_index=False)
                    modifiedDF = modifiedDF.sort_index().reset_index(drop=True)
                    rowsAdded += 2
        
            elif(currentDF.iat[int(row.Index), 1]) == 'SAVINGS':
                savingsTransaction = currentDF.iat[int(row.Index), 4]
                savingsAccountBalance += savingsTransaction
                
                if currentAccountBalance < 0 and savingsAccountBalance > 0:
                    currentToCredit = savingsAccountBalance  
                    savingsToDebit = -abs(currentToCredit)
                    currentAccountBalance += currentToCredit 
                    savingsAccountBalance += savingsToDebit 

                    savingsToAppend = pd.DataFrame({'AccountID': savingsAccountNo, 'AccountType': 'SAVINGS',
                                                    'InitiatorType': 'SYSTEM', 'DataTime': [currentDF.iat[int(row.Index), 3]],
                                                    'TransactionValue': savingsToDebit}, index=[int(row.Index) + 0.5 + rowsAdded])

                    currentToAppend = pd.DataFrame({'AccountID': currentAccountNo, 'AccountType': 'CURRENT',
                                                    'InitiatorType': 'SYSTEM', 'DataTime': [currentDF.iat[int(row.Index), 3]],
                                                    'TransactionValue': currentToCredit}, index=[int(row.Index) + 0.75 + rowsAdded])

                    modifiedDF = modifiedDF.append(savingsToAppend, ignore_index=False)
                    modifiedDF = modifiedDF.append(currentToAppend, ignore_index=False)
                    modifiedDF = modifiedDF.sort_index().reset_index(drop=True)
                    rowsAdded += 2

        processedDF.append(modifiedDF)
        fileNumber += 1
    return (processedDF)

def dataExport(filenames, dataframe):
    modifiedNameList = []
    
    for i in range(len(filenames)):
        modifiedFileName = filenames[i].replace('.csv', '-modified.csv')
        modifiedNameList.append(modifiedFileName)

    for i, df in enumerate(dataframe):
        dataframe[i].to_csv(modifiedNameList[i], index=False)
    
    print('Processing Complete')

# Main Function
filenames, raw_data = dataImport()
processed_data = dataProcessing(raw_data)
dataExport(filenames, processed_data)
