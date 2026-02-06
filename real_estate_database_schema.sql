
DROP TABLE IF EXISTS properties;
DROP TABLE IF EXISTS schools;
DROP TABLE IF EXISTS health_facilities;
DROP TABLE IF EXISTS transit_stations;
DROP TABLE IF EXISTS crime_data;
DROP TABLE IF EXISTS neighborhood_stats;


CREATE TABLE schools (
    school_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    school_type TEXT,
    grades TEXT,
    borough TEXT,
    latitude REAL,
    longitude REAL,
    location_code TEXT,
    address TEXT,
    community_district TEXT,
    council_district TEXT,
    phone_number TEXT,
    principal_name TEXT,
    open_date TEXT,
    status TEXT,
    CONSTRAINT check_latitude CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT check_longitude CHECK (longitude BETWEEN -180 AND 180)
);

CREATE INDEX idx_schools_location ON schools(latitude, longitude);
CREATE INDEX idx_schools_borough ON schools(borough);

CREATE TABLE health_facilities (
    hospital_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    facility_type TEXT,
    borough TEXT,
    latitude REAL,
    longitude REAL,
    address TEXT,
    phone TEXT,
    cross_streets TEXT,
    community_board TEXT,
    council_district TEXT,
    CONSTRAINT check_latitude CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT check_longitude CHECK (longitude BETWEEN -180 AND 180)
);

CREATE INDEX idx_health_location ON health_facilities(latitude, longitude);
CREATE INDEX idx_health_borough ON health_facilities(borough);


CREATE TABLE transit_stations (
    station_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    lines TEXT,
    structure TEXT,
    ada BOOLEAN,
    latitude REAL,
    longitude REAL,
    borough TEXT,
    complex_id TEXT,
    division TEXT,
    daytime_routes TEXT,
    ada_northbound BOOLEAN,
    ada_southbound BOOLEAN,
    ada_notes TEXT,
    CONSTRAINT check_latitude CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT check_longitude CHECK (longitude BETWEEN -180 AND 180)
);

CREATE INDEX idx_transit_location ON transit_stations(latitude, longitude);
CREATE INDEX idx_transit_borough ON transit_stations(borough);
CREATE INDEX idx_transit_ada ON transit_stations(ada);


CREATE TABLE properties (
    property_id INTEGER PRIMARY KEY AUTOINCREMENT,
    price INTEGER,
    beds INTEGER,
    baths INTEGER,
    sqft INTEGER,
    address TEXT,
    borough TEXT,
    neighborhood TEXT,
    latitude REAL,
    longitude REAL,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    property_type TEXT,
    main_address TEXT,
    street_name TEXT,
    formatted_address TEXT,
    CONSTRAINT check_price CHECK (price >= 0),
    CONSTRAINT check_beds CHECK (beds >= 0),
    CONSTRAINT check_baths CHECK (baths >= 0),
    CONSTRAINT check_sqft CHECK (sqft >= 0),
    CONSTRAINT check_latitude CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT check_longitude CHECK (longitude BETWEEN -180 AND 180)
);

CREATE INDEX idx_properties_location ON properties(latitude, longitude);
CREATE INDEX idx_properties_borough ON properties(borough);
CREATE INDEX idx_properties_price ON properties(price);
CREATE INDEX idx_properties_beds ON properties(beds);
CREATE INDEX idx_properties_neighborhood ON properties(neighborhood);


CREATE TABLE crime_data (
    crime_id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_date TEXT,
    incident_time TEXT,
    borough TEXT,
    precinct INTEGER,
    offense_description TEXT,
    offense_level TEXT,
    latitude REAL,
    longitude REAL,
    location_desc TEXT,
    zip_code TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_latitude CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT check_longitude CHECK (longitude BETWEEN -180 AND 180)
);

CREATE INDEX idx_crime_location ON crime_data(latitude, longitude);
CREATE INDEX idx_crime_borough ON crime_data(borough);
CREATE INDEX idx_crime_date ON crime_data(incident_date);
CREATE INDEX idx_crime_zip ON crime_data(zip_code);


CREATE TABLE neighborhood_stats (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    neighborhood TEXT NOT NULL,
    borough TEXT,
    avg_price INTEGER,
    median_price INTEGER,
    min_price INTEGER,
    max_price INTEGER,
    property_count INTEGER,
    avg_sqft INTEGER,
    price_per_sqft REAL,
    school_count INTEGER,
    hospital_count INTEGER,
    transit_count INTEGER,
    crime_count INTEGER,
    crime_rate REAL,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(neighborhood, borough)
);

CREATE INDEX idx_neighborhood_stats_name ON neighborhood_stats(neighborhood);
CREATE INDEX idx_neighborhood_stats_borough ON neighborhood_stats(borough);


CREATE VIEW property_amenity_summary AS
SELECT 
    p.property_id,
    p.address,
    p.price,
    p.beds,
    p.baths,
    p.sqft,
    p.borough,
    p.neighborhood,
    p.latitude,
    p.longitude,
    ROUND(p.price / NULLIF(p.sqft, 0), 2) as price_per_sqft,
    (SELECT COUNT(*) FROM schools s 
     WHERE ABS(s.latitude - p.latitude) < 0.01 
     AND ABS(s.longitude - p.longitude) < 0.01) as nearby_schools,
    (SELECT COUNT(*) FROM health_facilities h 
     WHERE ABS(h.latitude - p.latitude) < 0.01 
     AND ABS(h.longitude - p.longitude) < 0.01) as nearby_hospitals,
    (SELECT COUNT(*) FROM transit_stations t 
     WHERE ABS(t.latitude - p.latitude) < 0.01 
     AND ABS(t.longitude - p.longitude) < 0.01) as nearby_transit
FROM properties p;


CREATE VIEW borough_statistics AS
SELECT 
    borough,
    COUNT(*) as property_count,
    ROUND(AVG(price), 2) as avg_price,
    ROUND(AVG(price / NULLIF(sqft, 0)), 2) as avg_price_per_sqft,
    MIN(price) as min_price,
    MAX(price) as max_price,
    AVG(beds) as avg_beds,
    AVG(baths) as avg_baths,
    AVG(sqft) as avg_sqft
FROM properties
WHERE price > 0 AND sqft > 0
GROUP BY borough;