import sqlite3
import math

class RealEstateQueryHelper:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        if None in [lat1, lon1, lat2, lon2]:
            return None
        
        R = 6371 
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def search_properties(self, min_price=None, max_price=None, beds=None, 
                         baths=None, borough=None, neighborhood=None, limit=50):
        query = "SELECT * FROM properties WHERE 1=1"
        params = []
        
        if min_price:
            query += " AND price >= ?"
            params.append(min_price)
        if max_price:
            query += " AND price <= ?"
            params.append(max_price)
        if beds:
            query += " AND beds >= ?"
            params.append(beds)
        if baths:
            query += " AND baths >= ?"
            params.append(baths)
        if borough:
            query += " AND borough = ?"
            params.append(borough)
        if neighborhood:
            query += " AND neighborhood = ?"
            params.append(neighborhood)
        
        query += " ORDER BY price LIMIT ?"
        params.append(limit)
        
        results = self.cursor.execute(query, params).fetchall()
        return [dict(row) for row in results]
    
    def get_property_by_id(self, property_id):
        result = self.cursor.execute(
            "SELECT * FROM properties WHERE property_id = ?",
            (property_id,)
        ).fetchone()
        return dict(result) if result else None
    
    def get_nearby_schools(self, latitude, longitude, radius_km=1.0):
        schools = self.cursor.execute(
            "SELECT * FROM schools WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
        ).fetchall()
        
        nearby = []
        for school in schools:
            dist = self.calculate_distance(
                latitude, longitude,
                school['latitude'], school['longitude']
            )
            if dist and dist <= radius_km:
                school_dict = dict(school)
                school_dict['distance_km'] = round(dist, 2)
                nearby.append(school_dict)
        
        return sorted(nearby, key=lambda x: x['distance_km'])
    
    def get_nearby_hospitals(self, latitude, longitude, radius_km=1.0):
        hospitals = self.cursor.execute(
            "SELECT * FROM health_facilities WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
        ).fetchall()
        
        nearby = []
        for hospital in hospitals:
            dist = self.calculate_distance(
                latitude, longitude,
                hospital['latitude'], hospital['longitude']
            )
            if dist and dist <= radius_km:
                hospital_dict = dict(hospital)
                hospital_dict['distance_km'] = round(dist, 2)
                nearby.append(hospital_dict)
        
        return sorted(nearby, key=lambda x: x['distance_km'])
    
    def get_nearby_transit(self, latitude, longitude, radius_km=1.0):
        stations = self.cursor.execute(
            "SELECT * FROM transit_stations WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
        ).fetchall()
        
        nearby = []
        for station in stations:
            dist = self.calculate_distance(
                latitude, longitude,
                station['latitude'], station['longitude']
            )
            if dist and dist <= radius_km:
                station_dict = dict(station)
                station_dict['distance_km'] = round(dist, 2)
                nearby.append(station_dict)
        
        return sorted(nearby, key=lambda x: x['distance_km'])
    
    def get_nearby_crimes(self, latitude, longitude, radius_km=1.0):
        crimes = self.cursor.execute(
            "SELECT * FROM crime_data WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
        ).fetchall()
        
        nearby_crimes = []
        for crime in crimes:
            dist = self.calculate_distance(
                latitude, longitude,
                crime['latitude'], crime['longitude']
            )
            if dist and dist <= radius_km:
                crime_dict = dict(crime)
                crime_dict['distance_km'] = round(dist, 2)
                nearby_crimes.append(crime_dict)
        
    
        crime_stats = {
            'total_crimes': len(nearby_crimes),
            'by_offense': {},
            'by_level': {},
            'crimes': nearby_crimes[:20]  
        }
        
       
        for crime in nearby_crimes:
            offense = crime.get('offense_description', 'Unknown')
            level = crime.get('offense_level', 'Unknown')
            
            crime_stats['by_offense'][offense] = crime_stats['by_offense'].get(offense, 0) + 1
            crime_stats['by_level'][level] = crime_stats['by_level'].get(level, 0) + 1
        
        return crime_stats
    
    def get_property_price_analysis(self, property_id):
        prop = self.get_property_by_id(property_id)
        
        if not prop:
            return {'error': 'Property not found'}
        
        analysis = {
            'property': prop,
            'price_per_sqft': round(prop['price'] / prop['sqft'], 2) if prop['sqft'] else None
        }
        
        if prop.get('latitude') and prop.get('longitude'):
            analysis['nearby_amenities'] = {
                'schools': self.get_nearby_schools(prop['latitude'], prop['longitude']),
                'hospitals': self.get_nearby_hospitals(prop['latitude'], prop['longitude']),
                'transit_stations': self.get_nearby_transit(prop['latitude'], prop['longitude']),
                'crime_stats': self.get_nearby_crimes(prop['latitude'], prop['longitude'])
            }
        
        if prop.get('neighborhood') and prop.get('borough'):
            neighborhood_stats = self.cursor.execute(
                "SELECT * FROM neighborhood_stats WHERE neighborhood = ? AND borough = ?",
                (prop['neighborhood'], prop['borough'])
            ).fetchone()
            
            if neighborhood_stats:
                analysis['neighborhood_stats'] = dict(neighborhood_stats)
        
        return analysis
    
    def get_borough_statistics(self):
        results = self.cursor.execute(
            "SELECT * FROM borough_statistics ORDER BY property_count DESC"
        ).fetchall()
        return [dict(row) for row in results]
    
    def close(self):
        self.conn.close()