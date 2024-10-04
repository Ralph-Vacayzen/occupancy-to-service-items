import streamlit as st
import pandas as pd

st.set_page_config(page_title='Occupancy to Service Items', page_icon='🗓️', layout="centered", initial_sidebar_state="auto", menu_items=None)


st.caption('VACAYZEN')
st.title('Occupancy to Service Items')
st.info('Convert the occupancy-import file to integraRental service items.')


with st.expander('Uploaded Files'):
    
    file_descriptions = [
        ['Import1.csv','The initial import file for occupany import sessions.'],
        ['Partner Program Register (PPR) - BIKE.csv','The properties and bikes currently on the house bike program.'],
        ['Partner Program Register (PPR) - GART.csv','The properties and garts currently on the house gart program.'],
    ]

    files = {
        'Import1.csv': None,
        'Partner Program Register (PPR) - BIKE.csv': None,
        'Partner Program Register (PPR) - GART.csv': None,
    }

    uploaded_files = st.file_uploader(
        label='Files (' + str(len(files)) + ')',
        accept_multiple_files=True
    )

    st.info('File names are **case sensitive** and **must be identical** to the file name below.')
    st.dataframe(pd.DataFrame(file_descriptions, columns=['Required File','Source Location']), hide_index=True, use_container_width=True)


if len(uploaded_files) > 0:
    for index, file in enumerate(uploaded_files):
        files[file.name] = index

    hasAllRequiredFiles = True
    missing = []

    for file in files:
        if files[file] == None:
            hasAllRequiredFiles = False
            missing.append(file)

if len(uploaded_files) > 0 and not hasAllRequiredFiles:
    for item in missing:
        st.warning('**' + item + '** is missing and required.')

elif len(uploaded_files) > 0 and hasAllRequiredFiles:
    oc = pd.read_csv(uploaded_files[files['Import1.csv']], low_memory=False)
    bp = pd.read_csv(uploaded_files[files['Partner Program Register (PPR) - BIKE.csv']], low_memory=False)
    gp = pd.read_csv(uploaded_files[files['Partner Program Register (PPR) - GART.csv']], low_memory=False)
    
    oc = oc[['Customer','Unit_Code','Reservation Type','Start_Date','Departure']]
    bp = bp[['PARTNER','UNIT CODE','ORDER #']]
    gp = gp[['PARTNER','UNIT CODE','ORDER #']]

    oc.columns = ['Partner','Unit','Type','Arrival','Departure']
    bp.columns = ['Partner','Unit','Bike']
    gp.columns = ['Partner','Unit','Gart']

    df = pd.merge(oc, bp, how='left')
    df = pd.merge(df, gp, how='left')

    df = df[~pd.isna(df.Bike) | ~pd.isna(df.Gart)]
    df = df.drop_duplicates()

    header  = ['Service Item','Line Note','Date','Rental Agreement']
    results = []

    def add_service_to_results(service, date, agreement):
        results.append([service, '', date, agreement])

    def get_services(row):
        is_on_bike_program = not pd.isna(row.Bike)
        is_on_gart_program = not pd.isna(row.Gart)
    

        if 'TP' in row.Unit and is_on_bike_program:
            add_service_to_results(service='The Pointe Arrival',   date=row.Arrival,   agreement=row.Bike)
            add_service_to_results(service='The Pointe Departure', date=row.Departure, agreement=row.Bike)
            return

        if row.Type == 'Guest of Owner' or row.Type == 'Owner':
            if is_on_bike_program: add_service_to_results(service='Bike Check - Owner Arrival', date=row.Arrival, agreement=row.Bike)
            if is_on_gart_program: add_service_to_results(service='Gart Check - Owner Arrival', date=row.Arrival, agreement=row.Gart)
            
            
        if is_on_bike_program: add_service_to_results(service='Bike Check', date=row.Departure, agreement=row.Bike)
        if is_on_gart_program: add_service_to_results(service='Gart Check', date=row.Departure, agreement=row.Gart)
    
    df.apply(get_services, axis=1)

    deliverable = pd.DataFrame(results, columns=header)
    deliverable.Date = pd.to_datetime(deliverable.Date)
    deliverable = deliverable.sort_values(by='Date')
    deliverable.Date = deliverable.Date.dt.strftime('%m/%d/%Y')

    st.dataframe(deliverable, use_container_width=True, hide_index=True)