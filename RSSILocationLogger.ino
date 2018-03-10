
#include <TinyGPS++.h>                                  // Tiny GPS Plus Library
#include <SoftwareSerial.h>                             // Software Serial Library so we can use other Pins for communication with the GPS module

#include <Adafruit_NeoPixel.h>

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(1, 15, NEO_GRB + NEO_KHZ800);

// The WiFi support library
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssidToBeFound = "Freifunk";
const char* host = "kurm.de";
String deviceName = "ESP8266";
static const int RXPin = 12, TXPin = 13;
static const uint32_t GPSBaud = 9600;

uint8_t* bssid;
int32_t rssi;
bool ssidFound;
bool gpsValid;
uint8_t ledRed, ledGreen, ledBlue;

// The TinyGPS++ object
TinyGPSPlus gps;
TinyGPSCustom pdop(gps, "GPGSA", 15); // $GPGSA sentence, 15th element

// The serial connection to the GPS device
SoftwareSerial ss(RXPin, TXPin);

// Data Array
uint16_t dataCount;
typedef struct dataTyp {

  float dLat, dLng, dRssi, dPdop;
  byte dSat;

};
dataTyp data[1000];

void setup() {

  Serial.begin(115200);

  // Setup the WiFi module
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  ss.begin(GPSBaud);

  pixels.begin(); // This initializes the NeoPixel library.

  Serial.println("Setup done");

}


void printBSSID(uint8_t *thisBSSID) {
  for (int i = 0; i < 6; i++) {
    Serial.print(thisBSSID[i], HEX);
    Serial.print(":");
  }
}



void loop() {

  // NeoPixel LED ausschalten
  //pixels.setPixelColor(0, pixels.Color(0, 0, 0));
  //pixels.show();

  // Check for Freifunk is aviable and get the network with highest RSSI
  int networks = WiFi.scanNetworks();

  rssi = -100;
  ssidFound = false;
  gpsValid = false;

  for (int network = 0; network < networks; network++) {

    String ssid_scan;
    int32_t rssi_scan;
    uint8_t sec_scan;
    uint8_t* bssid_scan;
    int32_t chan_scan;
    bool hidden_scan;

    WiFi.getNetworkInfo(network, ssid_scan, sec_scan, rssi_scan, bssid_scan, chan_scan, hidden_scan);
    printBSSID(bssid_scan);
    Serial.print(", ");
    Serial.print(ssid_scan);
    Serial.print(", ");
    Serial.println(rssi_scan);

    if ( ssid_scan == ssidToBeFound ) {

      ssidFound = true;

      if ( rssi < rssi_scan ) {

        bssid = bssid_scan;
        rssi = rssi_scan;

      }

    }

  }

  if (ssidFound) {
    ledRed = 50;
    Serial.println("Freifunk found.");
  }
  else {
    ledRed = 0;
    Serial.println("Freifunk not found.");
  }




  // Check GPS


  if ( gps.location.isValid() && gps.satellites.value() > 7 && atof(pdop.value()) < 2 ) {

    gpsValid = true;
    ledBlue = 50;
    Serial.println("GPS valid.");

  } else{
    gpsValid = false;
    ledBlue = 0;
    Serial.println("GPS invalid.");
  }


  Serial.print("Sat: ");
  Serial.println(gps.satellites.value());  


  /*
     Append location to Array, if gps is valid
  */
  if (gpsValid) {

    if (dataCount < 1000) {

      data[dataCount].dLat = gps.location.lat();
      data[dataCount].dLng = gps.location.lng();
      data[dataCount].dRssi = rssi;
      data[dataCount].dPdop = atof(pdop.value());
      data[dataCount].dSat = gps.satellites.value();

      dataCount++;

    }
    Serial.print("DataCount: ");
    Serial.println(dataCount);

  }


  /*
     Connect to Freifunk if ssidFound is true
     And send Array to Server
  */
  if ( ssidFound && dataCount > 0 ) {

    pixels.setPixelColor(0, pixels.Color(0, 50, 0));
    pixels.show();

    if (WiFi.status() == WL_CONNECTED) {

      Serial.println("WiFi: connected");

      HTTPClient http;

      for ( int i = dataCount - 1 ; i >= 0 ; i-- ) {


        String url = "http://www.kurm.de/rssimap/rssimapapi.php?mode=import";
        url += "&lat=";
        url += String(data[i].dLat, 6);
        url += "&lon=";
        url += String(data[i].dLng, 6);
        url += "&rssi=";
        url += data[i].dRssi;
        url += "&pdop=";
        url += data[i].dPdop;
        url += "&sat=";
        url += data[i].dSat;
        url += "&device=";
        url += deviceName;

        Serial.println(url);
        http.begin(url);
        int httpCode = http.GET();

        Serial.print("[HTTP] GET... code: ");
        Serial.println(httpCode);

        if (httpCode > 0) {

          pixels.setPixelColor(0, pixels.Color(50, 50, 50));
          pixels.show();

          // hier muss noch geprüft werden ob das Eintragen in die Datenbank erfolgreich war

          dataCount--;

        } else {
          break;
        }

        delay(100);
        pixels.setPixelColor(0, pixels.Color(0, 0, 0));
        pixels.show();
        delay(100);

      }

    } else {

      Serial.println("WiFi: connecting...");
      WiFi.begin(ssidToBeFound);
      while (WiFi.status() != WL_CONNECTED) {
        pixels.setPixelColor(0, pixels.Color(0, 0, 50));
        pixels.show();
        delay(250);
        pixels.setPixelColor(0, pixels.Color(0, 0, 0));
        pixels.show();
        delay(250);
        Serial.print(".");
      }

    }




  } else {

    /*
         Je nach Status wird die LED in einer bestimmten Farbe leuchten
    */
    pixels.setPixelColor(0, pixels.Color(ledRed, ledGreen, ledBlue));
    pixels.show();

  }

  showArray();

  Serial.println("=======================================");



  smartDelay(100);                                      // Run Procedure smartDelay

  if (millis() > 5000 && gps.charsProcessed() < 10)
    Serial.println(F("No GPS data received: check wiring"));


}

void showArray() {

  Serial.println("---- Array -----");

  for ( int i = 0 ; i < dataCount ; i++ ) {

    Serial.print(i);
    Serial.print("lat:");
    Serial.print(data[i].dLat, 6);
    Serial.print(", lng:");
    Serial.print(data[i].dLat, 6);

    Serial.print(", rssi:");
    Serial.print(data[i].dRssi);
    Serial.print(", pdop:");
    Serial.print(data[i].dPdop);
    Serial.print(", sat:");
    Serial.println(data[i].dSat);

  }

}


static void smartDelay(unsigned long ms)                // This custom version of delay() ensures that the gps object is being "fed".
{
  unsigned long start = millis();
  do
  {
    while (ss.available())
      gps.encode(ss.read());
  } while (millis() - start < ms);
}

