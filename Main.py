#--------------SETUP GOOGLE SR--------------
import speech_recognition as sr
r = sr.Recognizer()

#---------------SETUP AI--------------------
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# Define the template for the assistant
template = """
{user_input}
"""
# Initialize the model
model = OllamaLLM(model="tinyllama")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

#-------------------SETUP Bluetooth-------------
from bluepy import btle  
import time
import wave  # Import wave module to write WAV files

#Use terminal command "sudo hcitool lescan" to find MAC
mac_address = "92:32:7E:F5:B4:3F"
SERVICE_UUID = "180F"
CHARACTERISTIC_UUID = "2A19"  # For receiving data
CONTROL_UUID = "2A1A"          # For sending control commands

# Connect to the BLE device
print("Connecting…")
nano_sense = btle.Peripheral(mac_address)

print("Discovering Services…")
_ = nano_sense.services
bleService = nano_sense.getServiceByUUID(SERVICE_UUID)

print("Discovering Characteristics…")
dataCharacteristic = bleService.getCharacteristics(CHARACTERISTIC_UUID)[0]
controlCharacteristic = bleService.getCharacteristics(CONTROL_UUID)[0]  # Get control characteristic

# Send the "START" message to the Arduino
print("Sending START signal to Arduino...")
controlCharacteristic.write(b"START")
print("Start signal sent!")


#--------------------SETUP Text to Speech------------
import os

#--------------------SETUP GPIO-----------------
import RPi.GPIO as GPIO 
from time import sleep 
GPIO.setwarnings(False) 

red = 2
blue = 3
green = 4

GPIO.setmode(GPIO.BCM) 
GPIO.setup(red, GPIO.OUT)
GPIO.setup(blue, GPIO.OUT)
GPIO.setup(green, GPIO.OUT)
#For some reason true = false idk why
#Turn off LEDs
GPIO.output(red, True)
GPIO.output(blue, True)
GPIO.output(green, True)


#-------------------Create needed functions----------------------
def byte_array_to_string(value):
    # Raw data is hexstring of int values, as a series of bytes, in little endian byte order
    # values are converted from bytes -> bytearray -> int
    # e.g., b'\xb8\x08\x00\x00' -> bytearray(b'\xb8\x08\x00\x00') -> 2232
    value = bytearray(value)
    value = value.decode('utf-8')
    return value

def WriteAudioFile():
    # Set up WAV file parameters
    file_name = "received_audio.wav"
    sample_rate = 44000
    channels = 1
    sample_width = 1

    # Open a new WAV file
    with wave.open(file_name, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)

        print("Receiving audio data...")
        BlueCHAR = bleService.getCharacteristics(CHARACTERISTIC_UUID)[0]

        # Continuously read data until receiving the termination marker
        while True:
            BlueData = BlueCHAR.read()
            if BlueData == b'\x99\x99':  # Check for termination marker
                print("End of transmission received.")
                break
            
            # Write the raw audio data to the WAV file
            wav_file.writeframes(BlueData)
        
        print(f"Audio data saved to {file_name}")

def SpeechToText():
    # Change the .wav file with whatever the file we write to is called
    GoogleSR = sr.AudioFile('received_audio.wav')
    with GoogleSR as source:
        audio = r.record(source)
    try:
        s = r.recognize_google(audio)
        print("Text: " + s)
        return s
    except Exception as e:
        print("Exception: " + str(e))
        return ""

def GenerateAI(user_input):
    # Prepare the input as a mapping
    formatted_input = {"user_input": user_input}

    # Generate a response from the model
    result = chain.invoke(formatted_input)

    # Print the result
    print(result.strip())
    return result.strip()
     
#---------------------Main---------------------------
def main():
    while True:
        BlueCHAR = bleService.getCharacteristics(CHARACTERISTIC_UUID)[0]
        BlueData = BlueCHAR.read()
        BlueData = byte_array_to_string(BlueData)
        print(BlueData)
    
        if BlueData == "01":
            GPIO.output(blue, False)
            WriteAudioFile()  # Write the audio data to a WAV file
            GPIO.output(blue, True)
            
            GPIO.output(green, False)
            Text = SpeechToText()  # Convert the audio file to text
            GPIO.output(green, True)
            
            GPIO.output(red, False)
            Response = GenerateAI(Text)  # Generate a response using AI
            GPIO.output(red, True)
        
            # Use text-to-speech to respond
            os.system(f'espeak "{Response}"')

if __name__ == "__main__":
    main()