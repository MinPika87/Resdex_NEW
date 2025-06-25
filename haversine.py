import math
def haversine(lat1, lon1, lat2, lon2):
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0
    lat1 = (lat1) * math.pi / 180.0
    lat2 = (lat2) * math.pi / 180.0
    a = (pow(math.sin(dLat / 2), 2) + 
         pow(math.sin(dLon / 2), 2) * 
             math.cos(lat1) * math.cos(lat2));
    rad = 6371
    c = 2 * math.asin(math.sqrt(a))
    return rad * c

if __name__ == "__main__":
    lat1 = 20.197874050000003
    lon1 = 85.29288977742775
    lat2 = 23.431601399999998
    lon2 = 82.31383043383778
    
    print(haversine(lat1, lon1,lat2, lon2), "K.M.")
