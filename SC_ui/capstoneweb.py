import streamlit as st
import pandas as pd
from PIL import Image
import numpy as np
import base64
import math
import zipfile
from io import BytesIO, StringIO

# py -3 -m streamlit run capstoneweb.py  
def inputpage():
    st.sidebar.title('Download your CSV file here')

    st.title("Input your requirements and restrictions")

    gpr = st.number_input("Gross Plot Ratio (GPR):")

    min_area=4000.00    # for condo
    site_area = st.number_input("Site Area in sqm:",min_value=min_area)

    #max 50% of the site area
    site_coverage = site_area/2 

    # Max gfa is gpr*site area
    max_gfa=math.ceil(gpr*site_area)
    gfa = st.number_input("Maximum Gross Floor Area (GFA) in sqm:",min_value=0,max_value=max_gfa,value=0,step=1)
    resi_gfa = gfa
    # got cap, need add in restriction
    # capped at 1% of total GFA
    # the communal indoor recreation spaces to be counted as bonus GFA,
    # provided such spaces exceed 0.6% of the total GFA of the development or 10 sqm
    st.subheader("**Bonus GFA**")   
    bonus_gfa1 = st.checkbox("For Balcony, Private Enclosed Spaces (PES), roof terrace") 
    if bonus_gfa1:
        st.write("**Balcony**") 
        balcony_length = st.number_input("Length of the balcony:",min_value=1.5)
        balcony_width = st.number_input("Width of the balcony:",min_value=1.5)
        if balcony_length<balcony_width:
            st.error('Length should be larger than width')
        balcony_x = 2*balcony_width+balcony_length
        st.write("Total Balcony Perimeter =",balcony_x+balcony_width)
        st.write("Open Balcony Perimeter =",balcony_x)
        if balcony_length > 0.0 or balcony_width > 0.0:
            balcony_percentage = (balcony_x/(balcony_x+balcony_length))*100
            st.write("Percentage of Balcony Perimeter Opening is ",round(balcony_percentage,2),"%")
            if balcony_percentage<40:
                st.error("Percentage of Balcony Perimeter Opening is less than 40%",balcony_percentage)
        # size for each dwelling unit is capped at 15% of internal nett unit size
        internal_net_unit_size=st.number_input('Internal net unit size',min_value=0.00)
        balcony_size=balcony_length*balcony_width
        st.write('Size of Balcony =',balcony_size)
        if internal_net_unit_size*0.15>balcony_size:
            st.error('Size for each dwelling unit is capped at 15% of internal net unit size')
        
        # st.write("**PES**")
        # st.write("**Roof Terrace**")

    # bonus_gfa2 = st.checkbox("Indoor Recreational Space")

    # Trigger conditions need to be taken care of
    st.subheader("**Dwelling Units**")
    location_option = st.radio("Inside central area?",['yes','within the estates in Maps 2-10','no'])
    if location_option != 'yes':
        numerator = gpr*site_area
        if location_option == 'no':
            maxUnits = round(numerator/85)
        else:
            maxUnits = round(numerator/100)
        # print(numerator,maxUnits)
        dwelling_units = maxUnits 
        st.write("Number of dwelling units:",maxUnits)
    else:
        dwelling_units = st.number_input("Number of Dwelling Units:",min_value=0,max_value=1000,step=1,value=0)
        
    st.subheader("**Building Height**")
    building_total_height = st.number_input("Height of the building:",min_value=0.00)
    max_storey=0
    first_storey_height=5.0
    top_storey_height=3.6
    other_storey_height=3.6
    if gpr<=1.4:
        max_storey=5
    elif gpr<1.6:
        max_storey=12
    elif gpr==1.6:
        max_storey=12
        top_storey_height=5.0
    elif gpr<=2.1:
        top_storey_height=5.0
        max_storey=24
    else:
        max_storey=36
        top_storey_height=5.0
    building_max_storeys = st.number_input("Maximum number of storeys:",min_value=0,max_value=max_storey,step=1,value=1)
    st.write("Floor to Floor Height:")
    floor2floor_first_height = st.number_input("Height for the First storey:",min_value=0.0,max_value=first_storey_height,step=0.1,value=first_storey_height)
    floor2floor_top_height = st.number_input("Height for the Top storey:",min_value=0.0,max_value=top_storey_height,step=0.1,value=top_storey_height)
    floor2floor_others_height = st.number_input("Height for the Other storeys:",min_value=0.0,max_value=other_storey_height,step=0.1,value=other_storey_height)
    # if st.checkbox("Additional Height for Predominant Sky Terrace Storey"):
    #     # occupy >60% of the floor plate
    #     B_additionalHeight = st.text_input()

    st.subheader("Refuse Bin Collection")
    refuse_bin_underground = st.radio("Is the refuse bin underground?",['yes','no'])
    #checking if refuse bin collection is underground or above ground
    #checking the total amount of refuse produced from max DU
    no_of_bins=0
    total_refuse = dwelling_units * 20
    if total_refuse < 4000:
        no_of_bins = total_refuse / 1100
        bin_area = 1.26 * 0.78 * no_of_bins * 1.1
        resi_gfa = resi_gfa - bin_area 
    else:
        bin_area = 7.4 * 9
        resi_gfa = resi_gfa - bin_area 

    if refuse_bin_underground == 'no':
        site_coverage = site_coverage - bin_area

    # substation
    # checking if the substation is above or underground and updating GFA
    st.subheader("Sub-Station")
    sub_underground = st.radio("Is the sub-station underground?",['yes','no'])
    # default is 12, 12
    sub_w = 12
    sub_l = 12
    area_of_substation = sub_w * sub_l
    if sub_underground == 'no':
    #calculating the area of the sub station and new GFA
        # above ground
        resi_gfa = resi_gfa - area_of_substation
        site_coverage = site_coverage - area_of_substation
    else:
        resi_gfa = resi_gfa - area_of_substation

    st.subheader("**Building Setback From Boundary**")
    # depends on no. of storeys
    roadngreenbuf = st.radio("Road and Green Buffer",("Category 1",'Category 2','Category 3','Category 4-5 and slip road'))
    greenbuf = 5.0
    roadbuf=0
    if building_max_storeys<6:
        if roadngreenbuf=="Category 1":
            roadbuf=24.0
        elif roadngreenbuf=="Category 2":
            roadbuf=12.0
        else:
            # cat 3 same as cat 4-5
            roadbuf=7.5
            greenbuf=3.0
    else:
        if roadngreenbuf=="Category 1":
            roadbuf=30.0
        elif roadngreenbuf=="Category 2":
            roadbuf=15.0
        elif roadngreenbuf=="Category 3":
            roadbuf=10
            greenbuf=3.0
        else: 
            # cat 4-5 and sliproad
            roadbuf=7.5
            greenbuf=3.0
    # check height of building 
    height_checker = floor2floor_first_height + floor2floor_top_height + (building_max_storeys - 2)*floor2floor_others_height
    if height_checker>building_total_height:
        st.error("The maximum building height has been exceeded. Please check the heights.")
        
    # For common boundary setback % planting strip, 36 storey and above same
    condo = {1:3.0, 2:3.0, 3:3.4, 4:3.8, 5:4.7, 6:5.5, 7:6.4,\
            8:7.2, 9:8.0, 10:8.7, 11:9.0, 12:9.2, 13:9.5, 14:9.8,\
            15:10.1, 16:10.3, 17:10.6, 18:10.8, 19:11.1, 20:11.3,\
            21:11.6, 22:11.8, 23:12.1, 24:12.4, 25:12.7, 26:12.9,\
            27:13.2, 28:13.4, 29:13.7, 30:14.0, 31:14.2, 32:14.5,\
            33:14.7, 34:15.0, 35:15.2, 36:15.5}
    flats = {1: 3.0, 2: 3.0, 3: 3.0, 4: 3.0, 5: 3.3, 6: 3.6,\
            7: 3.9, 8: 4.2, 9: 4.5, 10: 4.8, 11: 5.1, 12: 5.4,\
            13: 5.7, 14: 6.0, 15: 6.3, 16: 6.6, 17: 6.9, 18: 7.2,\
            19: 7.5, 20: 7.8, 21: 8.1, 22: 8.4, 23: 8.7, 24: 9.0,\
            25: 9.3, 26: 9.6, 27: 9.9, 28: 10.2, 29: 10.5, 30: 10.8,\
            31: 11.1, 32: 11.4, 33: 11.7, 34: 12.0, 35: 12.3, 36: 12.6}

    if site_area>=4000 and gpr>=1.4:
        landscape_deck = st.checkbox("Landscape Deck")
        # need check requirements for a landscape deck
        # deck = st.text_input("Landscape Deck:")  
    else:
        landscape_deck = 0

    basement = st.radio('Basement',['No basement','Basement with protrusion','Sunken basement'])

    # waterbody=st.radio('Does the development involve waterbodies?',['Yes','No'])
    if floor2floor_top_height<=5:
        attic=st.radio('Is there an attic?',['Yes','No'])
    ancillary=st.radio('Are there any ancillary shops?',['Yes','No'])
    st.subheader("Carpark")
    parking_zone = st.radio("Which zone is the carpark in?",[1,2,3])
    ratio_lots = st.number_input("Ratio lots:",value=2.0)
    # def car_parking (max_DU,ratio_lots,zone):
    # no_of_car_lots,area_of_carpark = car_parking (max_DU,2,1)
    #using the input ratio to determine the number of carpark lots required
    area_of_carpark=0
    if parking_zone == 1:
        if ratio_lots>2:
            st.error("Ratio too low") 
        else:
            no_of_car_lots = dwelling_units/ratio_lots
            area_of_carpark  = no_of_car_lots * 35
            # return no_of_car_lots,area_of_carpark

    if parking_zone == 2 or parking_zone == 3:
        if ratio_lots > 1.25:
            st.error("Ratio too low")
        else:
            no_of_car_lots = dwelling_units/ratio_lots
            area_of_carpark  = no_of_car_lots * 35
            # return no_of_car_lots,area_of_carpark
    resi_gfa = resi_gfa - area_of_carpark
    flat_roof=st.radio('Is the roof a flat one?',['Yes','No'])
    if dwelling_units>700:
        walkingcyclingplan="yes"
    else:
        walkingcyclingplan="no"

    st.subheader("__Building shape__")
    building_shape = st.selectbox("Choose the shape of the building",['1','2','3'])
    col1, col2, col3 = st.beta_columns(3)
    building_shape1 = Image.open("SC_ui/REC.png")
    building_shape2 = Image.open("SC_ui/LSHAPE.png")
    building_shape3 = Image.open("SC_ui/TSHAPE.png")
    with col1:
        st.header("Rectangle")
        st.image(building_shape1, caption="1", use_column_width=True)
    with col2:
        st.header("L shape")
        st.image(building_shape2, caption="2", use_column_width=True)
    with col3:
        st.header("T shape")
        st.image(building_shape3, caption="3",use_column_width=True)

    st.subheader("building checker")
    number_of_blocks = st.number_input("Number of blocks:",value=2.0)
    number_of_floorplates = number_of_blocks * building_max_storeys
    # floor area
    x = resi_gfa/number_of_floorplates
    # floorplate area
    y = site_coverage/number_of_blocks
    st.write("Floorplate area:",y)
    st.write("floor area:",x)
    st.write("Number of storeys:",building_max_storeys)
    st.write('Number of blocks:',number_of_blocks)
    st.write("Resi GFA:",resi_gfa,"         max gfa",gfa)
    if y<x:
        st.error("The number of floors/blocks is too low. Please increase it.")

    st.subheader("LIFTS and STAIRS")
    du_per_floor = math.floor(dwelling_units/(number_of_blocks*building_max_storeys))
    lift_w = st.number_input("Width of lift",value=5.0)
    lift_l = st.number_input("Length of width", value=5.0)
    lift_ratio = st.text_input("Ratio of number of lifts to dwelling units  = ",value="1:4")
    lr = int(lift_ratio.split(":")[1])
    number_of_lifts = math.ceil(du_per_floor/lr)
    stairs_w = st.number_input("Width of stairs",value=3.0)
    stairs_l = st.number_input("Length of stairs",value=5.0)
    stairs_ratio = st.text_input("Ratio of dwelling units to number of stairs = ",value="1:4")
    sr = int(stairs_ratio.split(":")[1])
    number_of_stairs = math.ceil(du_per_floor/sr)
    st.write("number of dwelling units per floor:",du_per_floor)
    st.write("number of lift:",number_of_lifts)
    st.write("number of stairs:",number_of_stairs)


    #compile as pandas df
    if bonus_gfa1:
        col=['GPR','site area','site coverage','max GFA','Balcony width','Balcony length','Balcony size','dwelling units',\
            'building storeys','building floor to floor first storey height','building floor to floor top storey height',\
            'building floor to floor others height','road buffer','green buffer','building shape',\
            'residential GFA','Number of refuse chute bin','refuse bin area','sub-station width','sub-station length','sub-station area',\
            'parking zone','ratio_lots',"number of car lots","area of carpark","number of (building) blocks",\
            'number of floorplates','floor area','floorplates area',\
            'lift width','lift length','number of lifts','lift ratio','stairs width','stairs length','number of stairs','stairs ratio']
        data=[(gpr,site_area,site_coverage,gfa,balcony_width,balcony_length,balcony_size,dwelling_units,\
            building_max_storeys,floor2floor_first_height,floor2floor_top_height,floor2floor_others_height,roadbuf,greenbuf,building_shape,\
            resi_gfa,no_of_bins,bin_area,sub_w,sub_l,area_of_substation,\
            parking_zone,ratio_lots,no_of_car_lots,area_of_carpark,\
            number_of_blocks,number_of_floorplates,x,y,\
            lift_w,lift_l,number_of_lifts,lift_ratio,stairs_w,stairs_l,number_of_stairs,stairs_ratio)]
    else:
        col=['GPR','site area','site coverage','max GFA','dwelling units',\
            'building storeys','building floor to floor first storey height','building floor to floor top storey height',\
            'building floor to floor others height','road buffer','green buffer','building shape',\
            'residential GFA','Number of refuse chute bin','refuse bin area','sub-station width','sub-station length','sub-station area',\
            'parking zone','ratio_lots',"number of car lots","area of carpark","number of (building) blocks",\
            'number of floorplates','floor area','floorplates area',\
            'lift width','lift length','number of lifts','lift ratio','stairs width','stairs length','number of stairs','stairs ratio']
        data=[(gpr,site_area,site_coverage,gfa,dwelling_units,\
            building_max_storeys,floor2floor_first_height,floor2floor_top_height,floor2floor_others_height,roadbuf,greenbuf,building_shape,\
            resi_gfa,no_of_bins,bin_area,sub_w,sub_l,area_of_substation,\
            parking_zone,ratio_lots,no_of_car_lots,area_of_carpark,\
            number_of_blocks,number_of_floorplates,x,y,\
            lift_w,lift_l,number_of_lifts,lift_ratio,stairs_w,stairs_l,number_of_stairs,stairs_ratio)]

    st.write('**Final CSV**')
    df = pd.DataFrame(data,columns=col)
    # df
    df_transpose = df.T
    newdfTrans = df_transpose.reset_index(drop=False)
    df_transpose
    # newdfTrans

    # st.write(df_transpose.index,"Check",newdfTrans.index)
    # df_oneCol = newdfTrans.stack().reset_index(drop=True)
    # df_oneCol


    csv = df_transpose.to_csv(index=True,header=None)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}">Download CSV File</a> (right-click and save as &lt;some_name&gt;.csv)'
    st.sidebar.markdown(href, unsafe_allow_html=True)


def displaypage():
    st.title("Output from our program")
    
    uploaded_zip = st.file_uploader('Upload zip file', type="zip")
    sf = st.empty()
    if uploaded_zip is not None:
        # print(uploaded_zip)
        zf = zipfile.ZipFile(uploaded_zip,'r')
        zf.extractall("./")
        list_files = zf.namelist()
        print(list_files)
        imgs=[]
        for i in range(len(list_files)):
            content = './'+list_files[i]
            if content.find("png")!=-1:
                imgs.append(content)
                
            else:
                data = pd.read_csv(content)
                # st.dataframe(data.head(10))
                data
        sf.image(imgs,caption=['test','1','2'],width=200)





def main():
    menu = ["Requirement Inputs","Display Outputs"]
    choice = st.sidebar.radio("Navigation",menu)
    if choice == "Requirement Inputs":
        inputpage()
    else:
        displaypage()
    

main()

