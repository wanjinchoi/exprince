from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Initialize Chrome WebDriver with logging preferences
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--log-level=0')  # Set log level to capture network logs

# Start measuring time
start_time = time.time()
chrome_driver_path = r"C:\Users\vivans\.wdm\drivers\chromedriver\win64\122.0.6261.69\chromedriver-win32\chromedriver.exe"
# Initialize Chrome WebDriver with logging enabled
driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)

# Navigate to a webpage
driver.get("https://www.google.com")

# Retrieve browser logs
logs = driver.get_log('performance')

# Find the network event containing connect time
connect_time_event = next((entry for entry in logs if 'Network.responseReceived' in entry['message']['method']), None)

# Extract connect time from the event
connect_time = connect_time_event['message']['params']['response']['timing']['connectEnd'] / 1000.0

# End measuring time
end_time = time.time()

# Calculate and print the time taken
time_taken = end_time - start_time
print(f"Connect time: {connect_time:.2f} seconds")
print(f"Total time taken: {time_taken:.2f} seconds")

# Close the WebDriver
driver.quit()
