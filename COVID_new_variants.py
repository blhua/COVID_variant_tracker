import pandas as pd
from sodapy import Socrata
from datetime import datetime
import os
from mac_notifications import client
import traceback
import requests

VARIANT_TRACKER_HISTORY_PATH = '/YOUR/PATH/HERE/COVID_variant_tracker.csv' #set absolute path to save csv file with current variant data
TODAY = datetime.today().strftime('%Y-%m-%d')

#connects to CDC database and pulls 
def get_last_month_data():

    today=datetime.now()
    last_month=datetime(today.year,today.month-1,today.day)    
    
    
    # Unauthenticated client only works with public data sets. Note 'None'
    # in place of application token, and no username or password:
    client = Socrata("data.cdc.gov", None)

    # Example authenticated client (needed for non-public datasets):
    # client = Socrata(data.cdc.gov,
    #                  MyAppToken,
    #                  username="user@example.com",
    #                  password="AFakePassword")

    # First 100 results, returned as JSON from API / converted to Python list of
    # dictionaries by sodapy.
    results = client.get("jr58-6ysp", limit=100, where=f"week_ending > \"{last_month.isoformat()}\"") 

    # Convert to pandas DataFrame
    results_df = pd.DataFrame.from_records(results)
    
    # Retype data
    results_df['share']=results_df['share'].astype(float)
    results_df['week_ending']=results_df['week_ending'].apply(datetime.fromisoformat)
    results_df['time_elapsed']=datetime.now()-results_df['week_ending']
    results_df['creation_date']=results_df['creation_date'].apply(datetime.fromisoformat)
    
    return results_df

#Filter for all of USA and sort
def filter_data(results_df):
    results_df=results_df.sort_values(['time_elapsed','creation_date','share'], ascending=[True,False,False])
    mask=results_df['usa_or_hhsregion']=='USA'
    return results_df[mask]

#Load previous dataset
def load_prev_data():
    if os.path.exists(VARIANT_TRACKER_HISTORY_PATH):
        return pd.read_csv(VARIANT_TRACKER_HISTORY_PATH)
    
    return None

#identify if there is a new predominant variant
def compare_data():
    
    #get old data
    old_data=load_prev_data()
    
    #get new data
    new_data=get_last_month_data()
    filtered_new_data=filter_data(new_data)
    
    if old_data is not None:

        old_variant=old_data.iloc[0]['variant']
        old_variant_share=old_data.iloc[0]['share']
        new_variant=filtered_new_data.iloc[0]['variant']
        new_variant_share=filtered_new_data.iloc[0]['share']

    filtered_new_data.to_csv(VARIANT_TRACKER_HISTORY_PATH)
    
    return old_variant, old_variant_share, new_variant, new_variant_share

#check WHO SARS-CoV-2 variant website for info on variant
def get_WHO_info(new_variant):
    #WHO SARS-CoV-2 variant tracking website
    url = 'https://www.who.int/activities/tracking-SARS-CoV-2-variants'

    header = {
      "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
      "X-Requested-With": "XMLHttpRequest"
    }
    r = requests.get(url, headers=header)

    dfs = pd.read_html(r.text)

    #Currently circulating variants of interest - VOI
    VOI = dfs[0]
    VOI.columns=VOI.iloc[0]
    VOI.drop(VOI.index[0],inplace=True)
    VOI['Pango lineage']=VOI['Pango lineage'].str.extract('([\w|\.]+)')
    VOI['Genetic features'] = VOI['Genetic features'].apply(lambda x: str(x).replace(u'\xa0', u' '))

    #Variants under monitoring - VUM
    VUM = dfs[1]
    VUM.columns=VUM.iloc[0]
    VUM.drop(VUM.index[0],inplace=True)
    VUM['Pango lineage']=VUM['Pango lineage'].str.extract('([\w|\.]+)')
    VUM['Genetic features'] = VUM['Genetic features'].apply(lambda x: str(x).replace(u'\xa0', u' '))

    if len(VOI[VOI['Pango lineage']==new_variant])==1:
        features=VOI[VOI['Pango lineage']==new_variant]['Genetic features'].tolist()[0]
    elif len(VUM[VUM['Pango lineage']==new_variant])==1:
        features=VUM[VUM['Pango lineage']==new_variant]['Genetic features'].tolist()[0]
    else:
        features='No features'

    return features

#send notification if new variant
def send_newvar_notification(old_variant, new_variant, new_variant_share, features):
    message = f'There is a new predominant SARS-CoV-2 variant in the US.\nOld variant: {old_variant}. New variant: {new_variant} ({round(new_variant_share*100,2)}%).\nGenetic features of new variant from WHO: {features}.\nFor more info, see: https://outbreak.info/situation-reports?xmin=2023-11-22&xmax=2024-05-22&pango={new_variant}'
    client.create_notification(
        title='SARS-CoV-2 variant update, '+TODAY,
        subtitle='New predominant US variant',
        text=message
    )
    
    with open('./SARS-CoV-2_variant_updates/'+TODAY+'_variant_update.txt','w') as f:
        f.write(message)

#send notification if no new variant
def send_nonewvar_notification(new_variant, new_variant_share):
    message = f'No change to predominant variant ({new_variant}, {round(new_variant_share*100,2)}%)'
    client.create_notification(
        title='SARS-CoV-2 variant update, '+TODAY,
        subtitle='No new predominant US variant',
        text=message
    )

    with open('./SARS-CoV-2_variant_updates/'+TODAY+'_variant_update.txt','w') as f:
        f.write(message)
    
#automate sending an error notification
def send_error_notification(error_message):

    client.create_notification(
        title='SARS-CoV-2 variant weekly update',
        subtitle='Error encountered with variant calling tool',
        text= error_message
    )
  
    with open('./SARS-CoV-2_variant_updates/'+TODAY+'_error_log.txt','w') as f:
        f.write(error_message)

#send the notification
def send_notification(old_variant, old_variant_share, new_variant, new_variant_share, features):
        if old_variant!=new_variant:
            print(f'There is a new predominant variant. Old= {old_variant}, New= {new_variant}')
            
            #send notification with new variant
            send_newvar_notification(old_variant, new_variant, new_variant_share, features)
        else:
            print('No new variant')
            
            #send notification that there's no new variant
            send_nonewvar_notification(new_variant, new_variant_share)

    
    
if __name__ == '__main__':
    try:
        old_variant, old_variant_share, new_variant, new_variant_share = compare_data()
        features = get_WHO_info(new_variant)
        send_notification(old_variant, old_variant_share, new_variant, new_variant_share, features)
    except Exception as err:
        error_text=traceback.format_exc()
        send_error_notification(error_text)