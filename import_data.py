import sqlite3
import pandas as pd
import os
import sys
from pathlib import Path
import requests
from datetime import datetime
import json
import math
import re

class RealEstateDatabase:
    def __init__(self, db_path='database/real_estate.db', data_dir='data'):

        self.db_path = db_path
        self.data_dir = data_dir
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
    def create_schema(self, schema_file='real_estate_database_schema.sql'):
 
        print("Creating database schema...")
        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            self.cursor.executescript(schema_sql)
            self.conn.commit()
            print("✓ Schema created successfully")
        except Exception as e:
            print(f"✗ Error creating schema: {e}")
            raise
    
    def clean_coordinate(self, value):
  
        try:
            if pd.isna(value) or value == '' or value is None:
                return None
            coord = float(value)
            if math.isnan(coord) or math.isinf(coord):
                return None
            return coord
        except (ValueError, TypeError):
            return None
    
    def parse_location_1_parentheses(self, location_str):

        try:
            if not location_str or pd.isna(location_str):
                return None, None
            
            location_str = str(location_str)

            pattern = r'\(([+-]?\d+\.?\d*),\s*([+-]?\d+\.?\d*)\)'
            matches = re.findall(pattern, location_str)
            
            if matches:

                lat_str, lon_str = matches[-1]
                lat = self.clean_coordinate(lat_str)
                lon = self.clean_coordinate(lon_str)
                

                if lat and lon and -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
            
        except Exception as e:
            pass
        
        return None, None
    
    def parse_location_1_json(self, location_str):

        try:
            if not location_str or pd.isna(location_str):
                return None, None
            
            location_str = str(location_str)
            

            lat_match = re.search(r"'latitude':\s*'([+-]?\d+\.?\d*)'", location_str)
            lon_match = re.search(r"'longitude':\s*'([+-]?\d+\.?\d*)'", location_str)
            
            if lat_match and lon_match:
                lat = self.clean_coordinate(lat_match.group(1))
                lon = self.clean_coordinate(lon_match.group(1))
                
                if lat and lon and -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
            
        except Exception:
            pass
        
        return None, None
    
    def parse_point_string(self, point_str):

        try:
            if not point_str or pd.isna(point_str):
                return None, None
            
            point_str = str(point_str).strip()
            point_str = re.sub(r'POINT\s*\(', '', point_str, flags=re.IGNORECASE)
            point_str = point_str.replace(')', '').strip()
            
            parts = point_str.split()
            if len(parts) == 2:
                lon = self.clean_coordinate(parts[0])
                lat = self.clean_coordinate(parts[1])
                
                if lat and lon and -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
        except Exception:
            pass
        return None, None
    
    def extract_coordinates(self, row, df_columns):

        latitude = None
        longitude = None
        

        if 'Latitude' in df_columns or 'LATITUDE' in df_columns:
            lat = self.clean_coordinate(row.get('Latitude') or row.get('LATITUDE'))
            if lat and -90 <= lat <= 90:
                latitude = lat
        
        if 'Longitude' in df_columns or 'LONGITUDE' in df_columns:
            lon = self.clean_coordinate(row.get('Longitude') or row.get('LONGITUDE'))
            if lon and -180 <= lon <= 180:
                longitude = lon
        

        if (latitude is None or longitude is None) and 'Location 1' in df_columns:
            location_val = row.get('Location 1')
            

            lat, lon = self.parse_location_1_parentheses(location_val)
            if lat is not None and lon is not None:
                latitude, longitude = lat, lon
            else:

                lat, lon = self.parse_location_1_json(location_val)
                if lat is not None and lon is not None:
                    latitude, longitude = lat, lon
        

        if latitude is None and 'GTFS Latitude' in df_columns:
            lat = self.clean_coordinate(row.get('GTFS Latitude'))
            if lat and -90 <= lat <= 90:
                latitude = lat
        
        if longitude is None and 'GTFS Longitude' in df_columns:
            lon = self.clean_coordinate(row.get('GTFS Longitude'))
            if lon and -180 <= lon <= 180:
                longitude = lon
        

        if (latitude is None or longitude is None) and 'Georeference' in df_columns:
            lat, lon = self.parse_point_string(row.get('Georeference'))
            if lat is not None and lon is not None:
                latitude, longitude = lat, lon
        
  
        if latitude is None and 'Y_COORDINATE' in df_columns:
            y = self.clean_coordinate(row.get('Y_COORDINATE'))
            if y and -90 <= y <= 90:
                latitude = y
        
        if longitude is None and 'X_COORDINATE' in df_columns:
            x = self.clean_coordinate(row.get('X_COORDINATE'))
            if x and -180 <= x <= 180:
                longitude = x
        

        if latitude is not None and longitude is not None:

            if 40.0 <= latitude <= 41.0 and -75.0 <= longitude <= -73.0:
                return latitude, longitude
        
        return None, None
    
    def clean_integer(self, value):
        """Clean integer values"""
        try:
            if pd.isna(value) or value == '' or value is None:
                return None
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def clean_text(self, value):
        """Clean text values"""
        if pd.isna(value) or value == '':
            return None
        return str(value).strip()
    
    def import_schools(self):
        """Import school data from CSV"""
        print("\nImporting schools data...")
        try:
            file_path = os.path.join(self.data_dir, '2017_-_2018_School_Locations.csv')
            df = pd.read_csv(file_path)
            
            print(f"  Found {len(df)} rows in CSV")
            
            imported = 0
            skipped_no_coords = 0
            skipped_no_data = 0
            
            for idx, row in df.iterrows():
                try:
                    school_id = self.clean_text(row.get('LOCATION_CODE') or row.get('ATS SYSTEM CODE'))
                    name = self.clean_text(row.get('LOCATION_NAME'))
                    
                    if not school_id or not name:
                        skipped_no_data += 1
                        continue
                    

                    latitude, longitude = self.extract_coordinates(row, df.columns)
                    
                    if latitude is None or longitude is None:
                        skipped_no_coords += 1
                        if skipped_no_coords <= 3:  # Debug first few
                            print(f"  DEBUG: Skipping {name} - no valid coordinates")
                        continue
                    
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO schools 
                        (school_id, name, school_type, grades, borough, latitude, longitude,
                         location_code, address, community_district, council_district,
                         phone_number, principal_name, open_date, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        school_id,
                        name,
                        self.clean_text(row.get('LOCATION_TYPE_DESCRIPTION')),
                        self.clean_text(row.get('GRADES_FINAL_TEXT') or row.get('GRADES_TEXT')),
                        self.clean_text(row.get('Borough')),
                        latitude,
                        longitude,
                        self.clean_text(row.get('LOCATION_CODE')),
                        self.clean_text(row.get('PRIMARY_ADDRESS_LINE_1')),
                        self.clean_text(row.get('COMMUNITY_DISTRICT')),
                        self.clean_text(row.get('COUNCIL_DISTRICT')),
                        self.clean_text(row.get('PRINCIPAL_PHONE_NUMBER') or row.get('Phone')),
                        self.clean_text(row.get('PRINCIPAL_NAME')),
                        self.clean_text(row.get('OPEN_DATE')),
                        self.clean_text(row.get('STATUS_DESCRIPTIONS'))
                    ))
                    imported += 1
                    
                except Exception as e:
                    if idx < 5:
                        print(f"  ERROR on row {idx}: {e}")
                    continue
            
            self.conn.commit()
            print(f"✓ Imported {imported} schools")
            if skipped_no_coords > 0:
                print(f"  ℹ️  Skipped {skipped_no_coords} schools (no valid coordinates)")
            if skipped_no_data > 0:
                print(f"  ℹ️  Skipped {skipped_no_data} schools (missing ID or name)")
                
        except Exception as e:
            print(f"✗ Error importing schools: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def import_health_facilities(self):
        """Import health facilities data from CSV"""
        print("\nImporting health facilities data...")
        try:
            file_path = os.path.join(self.data_dir, 'health-and-hospitals-corporation-hhc-facilities.csv')
            df = pd.read_csv(file_path)
            
            print(f"  Found {len(df)} rows in CSV")
            
            imported = 0
            no_coords = 0
            
            for idx, row in df.iterrows():
                try:
                    name = self.clean_text(row.get('Facility Name'))
                    
                    if not name:
                        continue
                    
                    hospital_id = f"HF_{idx}_{name[:20].replace(' ', '_')}"
                    
                    latitude, longitude = self.extract_coordinates(row, df.columns)
                    
                    if latitude is None or longitude is None:
                        no_coords += 1
                    
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO health_facilities 
                        (hospital_id, name, facility_type, borough, latitude, longitude,
                         address, phone, cross_streets, community_board, council_district)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        hospital_id,
                        name,
                        self.clean_text(row.get('Facility Type')),
                        self.clean_text(row.get('Borough')),
                        latitude,
                        longitude,
                        self.clean_text(row.get('Location 1')),
                        self.clean_text(row.get('Phone')),
                        self.clean_text(row.get('Cross Streets')),
                        self.clean_text(row.get('Community Board')),
                        self.clean_text(row.get('Council District'))
                    ))
                    imported += 1
                    
                except Exception as e:
                    if idx < 5:
                        print(f"  ERROR on row {idx}: {e}")
                    continue
            
            self.conn.commit()
            print(f"✓ Imported {imported} health facilities")
            if no_coords > 0:
                print(f"  ℹ️  {no_coords} facilities have no coordinates (still imported)")
                
        except Exception as e:
            print(f"✗ Error importing health facilities: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def import_transit_stations(self):

        print("\nImporting transit stations data...")
        try:
            file_path = os.path.join(self.data_dir, 'MTA_Subway_Stations.csv')
            df = pd.read_csv(file_path)
            
            print(f"  Found {len(df)} rows in CSV")
            
            imported = 0
            skipped = 0
            
            for idx, row in df.iterrows():
                try:
                    station_id = self.clean_text(row.get('GTFS Stop ID') or row.get('Station ID'))
                    name = self.clean_text(row.get('Stop Name'))
                    
                    if not station_id or not name:
                        skipped += 1
                        continue
                    
                    latitude, longitude = self.extract_coordinates(row, df.columns)
                    
                    if latitude is None or longitude is None:
                        skipped += 1
                        continue
                    
                    ada_value = row.get('ADA')
                    ada = 1 if str(ada_value).strip().upper() in ['1', 'TRUE', 'YES'] else 0
                    
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO transit_stations 
                        (station_id, name, lines, structure, ada, latitude, longitude,
                         borough, complex_id, division, daytime_routes, ada_northbound,
                         ada_southbound, ada_notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        station_id,
                        name,
                        self.clean_text(row.get('Line')),
                        self.clean_text(row.get('Structure')),
                        ada,
                        latitude,
                        longitude,
                        self.clean_text(row.get('Borough')),
                        self.clean_text(row.get('Complex ID')),
                        self.clean_text(row.get('Division')),
                        self.clean_text(row.get('Daytime Routes')),
                        1 if str(row.get('ADA Northbound', '')).strip().upper() in ['1', 'TRUE', 'YES'] else 0,
                        1 if str(row.get('ADA Southbound', '')).strip().upper() in ['1', 'TRUE', 'YES'] else 0,
                        self.clean_text(row.get('ADA Notes'))
                    ))
                    imported += 1
                    
                except Exception as e:
                    if idx < 5:
                        print(f"  ERROR on row {idx}: {e}")
                    skipped += 1
                    continue
            
            self.conn.commit()
            print(f"✓ Imported {imported} transit stations")
            if skipped > 0:
                print(f"  ℹ️  Skipped {skipped} stations (missing data)")
                
        except Exception as e:
            print(f"✗ Error importing transit stations: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def import_properties(self):
        print("\nImporting properties data...")
        try:
            file_path = os.path.join(self.data_dir, 'NY-House-Dataset.csv')
            df = pd.read_csv(file_path)
            
            print(f"  Found {len(df)} rows in CSV")
            
            imported = 0
            no_coords = 0
            
            for idx, row in df.iterrows():
                try:
                    price = self.clean_integer(row.get('PRICE'))
                    beds = self.clean_integer(row.get('BEDS'))
                    baths = self.clean_integer(row.get('BATH'))
                    sqft = self.clean_integer(row.get('PROPERTYSQFT'))
                    
                    latitude, longitude = self.extract_coordinates(row, df.columns)
                    
                    if latitude is None or longitude is None:
                        no_coords += 1
                    
                    self.cursor.execute('''
                        INSERT INTO properties 
                        (price, beds, baths, sqft, address, borough, neighborhood,
                         latitude, longitude, city, state, zip_code, property_type,
                         main_address, street_name, formatted_address)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        price,
                        beds,
                        baths,
                        sqft,
                        self.clean_text(row.get('ADDRESS')),
                        self.clean_text(row.get('ADMINISTRATIVE_AREA_LEVEL_2')),
                        self.clean_text(row.get('SUBLOCALITY')),
                        latitude,
                        longitude,
                        self.clean_text(row.get('LOCALITY')),
                        self.clean_text(row.get('STATE')),
                        None,
                        self.clean_text(row.get('TYPE')),
                        self.clean_text(row.get('MAIN_ADDRESS')),
                        self.clean_text(row.get('STREET_NAME')),
                        self.clean_text(row.get('FORMATTED_ADDRESS'))
                    ))
                    imported += 1
                    
                except Exception as e:
                    if idx < 5:
                        print(f"  ERROR on row {idx}: {e}")
                    continue
            
            self.conn.commit()
            print(f"✓ Imported {imported} properties")
            if no_coords > 0:
                print(f"  ℹ️  {no_coords} properties have no coordinates (still imported)")
                
        except Exception as e:
            print(f"✗ Error importing properties: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def import_crime_data_from_api(self, api_url=None, limit=10000):

        print("\nImporting crime data from API...")
        
        if api_url is None:
            api_url = "https://data.cityofnewyork.us/resource/5uac-w243.json"
        
        try:
            params = {
                '$limit': limit,
                '$order': 'cmplnt_fr_dt DESC'
            }
            
            print(f"  Fetching data from API (limit: {limit})...")
            response = requests.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            
            crime_records = response.json()
            print(f"  Received {len(crime_records)} records")
            
            imported = 0
            for record in crime_records:
                try:
                    latitude = self.clean_coordinate(record.get('latitude'))
                    longitude = self.clean_coordinate(record.get('longitude'))
                    
                    self.cursor.execute('''
                        INSERT INTO crime_data 
                        (incident_date, incident_time, borough, precinct, offense_description,
                         offense_level, latitude, longitude, location_desc, zip_code)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        self.clean_text(record.get('cmplnt_fr_dt')),
                        self.clean_text(record.get('cmplnt_fr_tm')),
                        self.clean_text(record.get('boro_nm')),
                        self.clean_integer(record.get('addr_pct_cd')),
                        self.clean_text(record.get('ofns_desc')),
                        self.clean_text(record.get('law_cat_cd')),
                        latitude,
                        longitude,
                        self.clean_text(record.get('prem_typ_desc')),
                        None
                    ))
                    imported += 1
                except Exception:
                    continue
            
            self.conn.commit()
            print(f"✓ Imported {imported} crime records")
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not fetch crime data from API: {e}")
            print("  Continuing without crime data...")
        except Exception as e:
            print(f"⚠️  Error processing crime data: {e}")
            print("  Continuing without crime data...")
    
    def calculate_neighborhood_stats(self):

        print("\nCalculating neighborhood statistics...")
        try:
            self.cursor.execute('DELETE FROM neighborhood_stats')
            
            self.cursor.execute('''
                INSERT INTO neighborhood_stats 
                (neighborhood, borough, avg_price, median_price, min_price, max_price,
                 property_count, avg_sqft, price_per_sqft)
                SELECT 
                    neighborhood,
                    borough,
                    ROUND(AVG(price)),
                    ROUND(AVG(price)),
                    MIN(price),
                    MAX(price),
                    COUNT(*),
                    ROUND(AVG(sqft)),
                    ROUND(AVG(CAST(price AS REAL) / NULLIF(sqft, 0)), 2)
                FROM properties
                WHERE neighborhood IS NOT NULL 
                  AND price > 0 
                  AND sqft > 0
                GROUP BY neighborhood, borough
            ''')
            
            neighborhoods = self.cursor.execute(
                'SELECT stat_id, neighborhood, borough FROM neighborhood_stats'
            ).fetchall()
            
            for stat_id, neighborhood, borough in neighborhoods:
                center = self.cursor.execute('''
                    SELECT AVG(latitude), AVG(longitude)
                    FROM properties
                    WHERE neighborhood = ? AND borough = ?
                    AND latitude IS NOT NULL AND longitude IS NOT NULL
                ''', (neighborhood, borough)).fetchone()
                
                if center[0] and center[1]:
                    lat, lon = center
                    
                    school_count = self.cursor.execute('''
                        SELECT COUNT(*) FROM schools
                        WHERE ABS(latitude - ?) < 0.01 
                        AND ABS(longitude - ?) < 0.01
                    ''', (lat, lon)).fetchone()[0]
                    
                    hospital_count = self.cursor.execute('''
                        SELECT COUNT(*) FROM health_facilities
                        WHERE latitude IS NOT NULL
                        AND ABS(latitude - ?) < 0.01 
                        AND ABS(longitude - ?) < 0.01
                    ''', (lat, lon)).fetchone()[0]
                    
                    transit_count = self.cursor.execute('''
                        SELECT COUNT(*) FROM transit_stations
                        WHERE ABS(latitude - ?) < 0.01 
                        AND ABS(longitude - ?) < 0.01
                    ''', (lat, lon)).fetchone()[0]
                    
                    crime_count = self.cursor.execute('''
                        SELECT COUNT(*) FROM crime_data
                        WHERE borough = ?
                    ''', (borough,)).fetchone()[0]
                    
                    self.cursor.execute('''
                        UPDATE neighborhood_stats
                        SET school_count = ?,
                            hospital_count = ?,
                            transit_count = ?,
                            crime_count = ?
                        WHERE stat_id = ?
                    ''', (school_count, hospital_count, transit_count, crime_count, stat_id))
            
            self.conn.commit()
            print(f"✓ Calculated statistics for {len(neighborhoods)} neighborhoods")
        except Exception as e:
            print(f"✗ Error calculating statistics: {e}")
            import traceback
            traceback.print_exc()
    
    def get_summary_stats(self):

        print("\n" + "="*60)
        print("DATABASE SUMMARY")
        print("="*60)
        
        stats = [
            ("Schools", "SELECT COUNT(*) FROM schools"),
            ("  - With coordinates", "SELECT COUNT(*) FROM schools WHERE latitude IS NOT NULL"),
            ("Health Facilities", "SELECT COUNT(*) FROM health_facilities"),
            ("  - With coordinates", "SELECT COUNT(*) FROM health_facilities WHERE latitude IS NOT NULL"),
            ("Transit Stations", "SELECT COUNT(*) FROM transit_stations"),
            ("Properties", "SELECT COUNT(*) FROM properties"),
            ("  - With coordinates", "SELECT COUNT(*) FROM properties WHERE latitude IS NOT NULL"),
            ("Crime Records", "SELECT COUNT(*) FROM crime_data"),
            ("Neighborhoods", "SELECT COUNT(*) FROM neighborhood_stats")
        ]
        
        for name, query in stats:
            count = self.cursor.execute(query).fetchone()[0]
            print(f"{name:25}: {count:,}")
        
        print("="*60)
    
    def close(self):

        self.conn.close()

def main():

    print("="*60)
    print("REAL ESTATE DATABASE IMPORT TOOL - FINAL")
    print("="*60)
    
    db = RealEstateDatabase()
    
    try:
        db.create_schema()
        db.import_schools()
        db.import_health_facilities()
        db.import_transit_stations()
        db.import_properties()
        
        print("\n" + "="*60)
        print("Would you like to import crime data from NYC Open Data API?")
        print("This requires internet and may take a few moments.")
        print("="*60)
        import_crime = input("Import crime data? (y/n): ").lower().strip() == 'y'
        
        if import_crime:
            db.import_crime_data_from_api(limit=50000)
        
        db.calculate_neighborhood_stats()
        db.get_summary_stats()
        
        print("\n✓ Database created successfully!")
        print(f"  Location: {db.db_path}")
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()