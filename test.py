import tkinter as tk
from bs4 import BeautifulSoup
import requests
import json
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

def closing():
    for figure in plt.get_fignums():
        plt.close(figure)
    if root.winfo_exists():
        root.destroy()

link_1 = requests.get('https://www.wunderground.com/weather/us/oh/akron/KOHAKRON143').text
WU_html = BeautifulSoup(link_1, 'lxml')

link_2 = requests.get('https://weather.com/weather/today/l/b62519aa392532c1c0124b11374e0470b07ca48c2a90261effab935d4f431cff652f6b6efc73a656969b154aedcb08af').text
WCOM_html = BeautifulSoup(link_2, 'lxml')

link_3 = requests.get('https://api.weather.gov/alerts/active?area=OH').text
NWSOH_alerts = json.loads(link_3)

link_4 = requests.get('https://weather.com/weather/hourbyhour/l/b62519aa392532c1c0124b11374e0470b07ca48c2a90261effab935d4f431cff652f6b6efc73a656969b154aedcb08af').text
WCOM_Hour_html = BeautifulSoup(link_4, 'lxml')

SPC_img = requests.get('https://www.spc.noaa.gov/products/outlook/day1otlk.gif')
with open("d1otlk.gif", "wb") as f:
    f.write(SPC_img.content)

NOAA_radar_img = requests.get('https://radar.weather.gov/ridge/standard/CENTGRLAKES_loop.gif')
with open("greatlksrdr.gif", "wb") as f:
    f.write(NOAA_radar_img.content)

#init tk GUI
root = tk.Tk()
root.geometry("1500x875")
root.title("Aggregator")
root.protocol("WM_DELETE_WINDOW", closing)

#Parsing html for specific information
WU_copley_general = WU_html.find('div', class_="condition-data")
WU_copley_temp = WU_copley_general.find('span',class_ ="wu-value wu-value-to").text
print("Wunderground " + WU_copley_temp)

WCOM_copley_temp = WCOM_html.find('span', class_ = "CurrentConditions--tempValue--MHmYY").text
print("Weather.com " + WCOM_copley_temp[:2])

time_list = []
temp_list = []
rain_list = []
index = 0
id_str = "detailIndex" + str(index) #concat
index+=1

while index < 8: #this will be 9 distint ordered hour 3 data points
    WCOM_hour_html_t1 = WCOM_Hour_html.find('details', id = id_str) #must be detailIndex1 to get next hours and onwards
    WCOM_hour_html_t2 = WCOM_hour_html_t1.find('span', {'data-testid': 'TemperatureValue'}).text #temp
    WCOM_hour_html_t3 = WCOM_hour_html_t1.find('h2', {'data-testid': 'daypartName'}).text #time
    WCOM_hour_html_t4 = WCOM_hour_html_t1.find('span', {'data-testid': 'PercentageValue'}).text #rainchance
    time_list.append(WCOM_hour_html_t3)
    temp_list.append(WCOM_hour_html_t2)
    rain_list.append(WCOM_hour_html_t4)
    id_str = "detailIndex" + str(index) #concat
    index = index + 1

print(WCOM_hour_html_t2)
print(WCOM_hour_html_t3)
print(WCOM_hour_html_t4)
print(rain_list)
print(temp_list)
print(time_list)

#Making the plot
figure1, sp1 = plt.subplots()
sp1.plot(time_list, temp_list, color='red', marker='o', label = 'Predicted Temperatures')
sp1.set_xlabel('Time')
sp1.set_ylabel('Temperature')
sp1.invert_yaxis()
#plt.show()

figure2, sp2 = plt.subplots()
sp2.plot(time_list, rain_list, color='blue', marker='x', label = 'Predicted Rainfall Chance')
sp2.set_xlabel('Time')
sp2.set_ylabel('Rain')
#plt.show()

#Embedding two plots into tkinter
plot_canvas1 = FigureCanvasTkAgg(figure1, master=root)
plot_canvas1.draw()
plot_canvas1.get_tk_widget().place(x=120,y=10, width=450, height=270)

plot_canvas2 = FigureCanvasTkAgg(figure2, master=root)
plot_canvas2.draw()
plot_canvas2.get_tk_widget().place(x=550,y=10, width=450, height=270)

#alert state detection
alert_map = []
alert_map_copley = []
alert_flag = False
for alert in NWSOH_alerts["features"]:
    properties = alert.get("properties") #KV pairs? it is a dictionary from the load for json
    desc = properties.get("description","")
    headline = properties.get("headline","")
    alert_map.append((headline, desc))
    if "Akron" in desc or "Copley" in desc:
        alert_map_copley.append((headline, desc))
        alert_flag = True #set so there is alert
if alert_flag == False:
    print("No current alerts for Copley/Akron")
    alert_map_copley.append(("No headline","No current alerts for Copley/Akron"))

WU_temp_label = tk.Label(root, text=WU_copley_temp+"°", font=('Arial',15))
WU_temp_label.place(x=80, y=0)

WCOM_temp_label = tk.Label(root, text=WCOM_copley_temp, font=('Arial',15))
WCOM_temp_label.place(x=60,y=60)

alert_map_copley_text = "" #convert list of tuple to str to avoid issues when printing the message
for tuple in alert_map_copley:
    for item in tuple:
        alert_map_copley_text += item
        alert_map_copley_text += "\n"
    alert_map_copley_text += "\n"

#these flags for any warning in ohio both watch and warning count will jsut show up as a switch on
flood_warning = False
tornado_warning = False
svr_storm_warning = False
for headline, description in alert_map:
    if "Flood" in headline or "Flash" in headline:
        flood_warning = True
    if "Severe Thunderstorm" in headline:
        svr_storm_warning = True
    if "Tornado" in headline:
        tornado_warning = True

print(flood_warning)
print(tornado_warning)
print(svr_storm_warning)

#MESSAGE
alert_message = tk.Message(root, text=alert_map_copley_text, font=("Arial", 9))
alert_message.config(bg="lightgreen")
alert_message.place(x=825, y=310)

#BUTTON
refresh_button = tk.Button(root, text="Refresh", font=('Arial', 12))
refresh_button.place(x=900, y=800)

#IMAGES
image1 = Image.open('WU.png')
image1_scaled = image1.resize((image1.width // 5, image1.height // 5))
image2 = Image.open('weatherchannel.png')
image2_scaled = image2.resize((image2.width // 24, image2.height // 24))
imageSPC = Image.open('d1otlk.gif')
imageSPC_scaled = imageSPC.resize((imageSPC.width, imageSPC.height)) #needs 2 tuple floored integer
imageRDR = Image.open('greatlksrdr.gif')

WU_image = ImageTk.PhotoImage(image1_scaled)
WCOM_image = ImageTk.PhotoImage(image2_scaled)
SPC_image = ImageTk.PhotoImage(imageSPC_scaled)
NOAA_rdr_image = ImageTk.PhotoImage(imageRDR)

WCOM_image_label = tk.Label(root, image=WCOM_image)
WCOM_image_label.place(x=0,y=65)
WU_image_label = tk.Label(root, image=WU_image)
WU_image_label.place(x=0,y=0)
SPC_image_label = tk.Label(root, image=SPC_image)
SPC_image_label.place(x=0, y=310)
NOAA_image_rdr_label = tk.Label(root, image=NOAA_rdr_image) #tkinter does not support movement in gif
NOAA_image_rdr_label.place(x=800, y=500)

image3 = Image.open('warningoff.jpg')
image3_scaled = image3.resize((image3.width // 5, image3.height // 5))
image4 = Image.open('warningon.jpg')
image4_scaled = image4.resize((image4.width // 5, image4.height // 5))

WarningON_image = ImageTk.PhotoImage(image4_scaled)
WarningOFF_image = ImageTk.PhotoImage(image3_scaled)

#State warning on or off 
if tornado_warning == True:
    WarningON_image_label_tornado = tk.Label(root, image=WarningON_image)
    WarningON_image_label_tornado.place(x=1465-320,y=5)
else:
    WarningON_image_label_tornado = tk.Label(root, image=WarningOFF_image)
    WarningON_image_label_tornado.place(x=1465-320,y=5)
    
if flood_warning == True:
    WarningON_image_label_tornado = tk.Label(root, image=WarningON_image)
    WarningON_image_label_tornado.place(x=1465-320,y=45)
else:
    WarningON_image_label_tornado = tk.Label(root, image=WarningOFF_image)
    WarningON_image_label_tornado.place(x=1465-320,y=45)

if svr_storm_warning == True:
    WarningON_image_label_tornado = tk.Label(root, image=WarningON_image)
    WarningON_image_label_tornado.place(x=1465-320,y=85)
else:
    WarningON_image_label_tornado = tk.Label(root, image=WarningOFF_image)
    WarningON_image_label_tornado.place(x=1465-320,y=85)

tornado_warning_label = tk.Label(root, text="Tornado Warning", font=('Arial',12), fg="purple") #Warning Labels
tornado_warning_label.place(x=1330-320,y=10)
flood_warning_label = tk.Label(root, text="Flood Warning", font=('Arial',12), fg="green") #Warning Labels
flood_warning_label.place(x=1345-320,y=50)
tornado_warning_label = tk.Label(root, text="Severe T Warning", font=('Arial',12), fg="orange") #Warning Labels
tornado_warning_label.place(x=1330-320,y=90)

#Plot with predicted temp and rainfall changes merged into 1

#for item in NWSOH_alerts.items():
#    print(item)
#    print("\n\n\n")

#with open('output.html', 'w', encoding='utf-8') as file:
#   file.write(NWSOH_alerts["features"])
root.mainloop()

