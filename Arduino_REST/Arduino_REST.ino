#include <SPI.h>
#include <Ethernet.h>

// Use 1 to pass the entire parameter string to the function, which will be responsible for parsing the parameter string
// Useful for more complex situations, where the key name as well as its value is important, or there are mutliple key-value pairs
//    function?params=hello    ==> params=hello gets passed to the function
#define AREST_PARAMS_MODE 1
#include <aREST.h>
#include <avr/wdt.h>

int tempPin = 0;
int redPin = 2;

char MyKey[] = "123456";
#define DENIED -100



// Enter a MAC address and IP address for your controller below.
// The IP address will be dependent on your local network:
byte mac[] = {
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
};
IPAddress ip(192, 168, 0, 199);

// Initialize the Ethernet server library
// with the IP address and port you want to use
// (port 80 is default for HTTP):
EthernetServer server(80);

// Create aREST instance
aREST rest = aREST();

// To be exposed via REST
float temp = -100.0;

unsigned long time = millis();
//value can't exceed 32 bytes
char value[32];

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.println("Ethernet WebServer Example");

  
  // start the Ethernet connection and the server:
  Ethernet.begin(mac, ip);

  // Check for Ethernet hardware present
  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
    Serial.println("Ethernet shield was not found.  Sorry, can't run without hardware. :(");
    while (true) {
      delay(1); // do nothing, no point running without Ethernet hardware
    }
  }
  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println("Ethernet cable is not connected.");
  }

  // Register Temp variable
  rest.function("getT", readTemperature);
  rest.function("setLed", setLED);

  // Set board name
  rest.set_name((char *)"MyMegaBoard");
  rest.set_id("001");



  // start the server
  server.begin();
  Serial.print("server is at ");
  Serial.println(Ethernet.localIP());
    // Start watchdog
  wdt_enable(WDTO_4S);

  pinMode(redPin, OUTPUT);

}

// Returns value of the specified parameter
// params - input, such as param1=value1&param2=value2...
// paramName - name of the specific parameter
// value - buffer for returned value
// returns 0 if ok, -1 if no parameter defined
int getParam(String params, char *paramName, char *value) {

  char *param, *valS, *valE;
  int valueLen;
  char buf[params.length()+1];

  params.toCharArray(buf,params.length()+1);


  //find paramName within the params
  param = strstr(buf, paramName);
  if(param == NULL) {
    return -1;
  }

  //find beginning of the value
  valS = strstr(param,"=");
  if(valS == NULL) {  // always expects param=value
    return -1;
  }

  valS++;

  valE = strstr(valS,"&");
  if (valE == NULL) { // this was the last entry in the params
    valueLen = strlen(valS);
  } else {
    valueLen = valE - valS;
  }

  memcpy(value,valS,valueLen);
  value[valueLen]='\0';
  return 0;
}

//AuthMe expects one of the parameters to be key=MyKey
bool AuthMe(String params) {
  if(getParam(params,(char *)"key",value) == 0) {
    if(strcmp(value,MyKey) == 0) {
      Serial.println("Access Granted");
      return(true);
    } 
  }  
  Serial.println("Access Denied");
  return(false);
}

//expected parameters: 
//key = MyKey
//scale = C/F/K, default C
int readTemperature(String params) {
  if(AuthMe(params)) {
    int tempReading = analogRead(tempPin);
  // This is OK
    double tempK = log(10000.0 * ((1024.0 / tempReading - 1)));
    tempK = 1 / (0.001129148 + (0.000234125 + (0.0000000876741 * tempK * tempK )) * tempK );       //  Temp Kelvin
    float tempC = tempK - 273.15;            // Convert Kelvin to Celcius
    float tempF = (tempC * 9.0)/ 5.0 + 32.0; // Convert Celcius to Fahrenheit
    if(getParam(params, (char *)"scale",value) == 0) {
      if(strcmp(value,"K") == 0) {
        return int(tempK);
      }
      if(strcmp(value,"F") == 0) {
        return int(tempF);
      }
    }
    return int(tempC);
  } else {
    return(DENIED);  
  }
}

//expected parameters:
//key = MyKey
//set = 0-255
//returns set value
int setLED(String params) {
  if(AuthMe(params)) {
    if(getParam(params, (char *)"set", value) == 0) {
       analogWrite(redPin, atoi(value));
       return(atoi(value));
    }
  } else {
    return(DENIED);  
  }
}


void loop() {
  // listen for incoming clients
  EthernetClient client = server.available();
  rest.handle(client);
  wdt_reset();
}
