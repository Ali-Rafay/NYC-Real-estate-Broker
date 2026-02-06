
from flask import Flask, render_template, request, jsonify
import sqlite3
from query_helper import RealEstateQueryHelper
import json

app = Flask(__name__)
app.config['DATABASE'] = 'database/real_estate.db'

def get_db():
    
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>NYC Real Estate Finder</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            .header h1 { 
                font-size: 2.5rem; 
                margin-bottom: 10px;
                font-weight: 700;
            }
            .header p { 
                font-size: 1.1rem; 
                opacity: 0.9;
            }
            .content { padding: 40px; }
            .search-section {
                background: #f8f9fa;
                padding: 30px;
                border-radius: 8px;
                margin-bottom: 30px;
            }
            .search-section h2 {
                margin-bottom: 20px;
                color: #333;
                font-size: 1.5rem;
            }
            .form-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 8px;
                color: #555;
                font-weight: 500;
            }
            .form-group input, .form-group select {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 1rem;
                transition: border-color 0.3s;
            }
            .form-group input:focus, .form-group select:focus {
                outline: none;
                border-color: #667eea;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 14px 30px;
                border-radius: 6px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
            }
            .btn:active {
                transform: translateY(0);
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .feature-card {
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 25px;
                text-align: center;
                transition: transform 0.2s, border-color 0.2s;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                border-color: #667eea;
            }
            .feature-icon {
                font-size: 3rem;
                margin-bottom: 15px;
            }
            .feature-card h3 {
                color: #333;
                margin-bottom: 10px;
            }
            .feature-card p {
                color: #666;
                line-height: 1.6;
            }
            .api-section {
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 20px;
                margin-top: 30px;
                border-radius: 4px;
            }
            .api-section h3 {
                color: #856404;
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏙️ NYC Real Estate Finder</h1>
                <p>Find your perfect property with comprehensive neighborhood analysis</p>
            </div>
            
            <div class="content">
                <div class="search-section">
                    <h2>🔍 Search Properties</h2>
                    <form action="/search" method="GET">
                        <div class="form-grid">
                            <div class="form-group">
                                <label>Min Price</label>
                                <input type="number" name="min_price" placeholder="e.g., 300000">
                            </div>
                            <div class="form-group">
                                <label>Max Price</label>
                                <input type="number" name="max_price" placeholder="e.g., 1000000">
                            </div>
                            <div class="form-group">
                                <label>Bedrooms</label>
                                <input type="number" name="beds" placeholder="e.g., 2">
                            </div>
                            <div class="form-group">
                                <label>Borough</label>
                                <select name="borough">
                                    <option value="">All Boroughs</option>
                                    <option value="Manhattan">Manhattan</option>
                                    <option value="Brooklyn">Brooklyn</option>
                                    <option value="Queens">Queens</option>
                                    <option value="Bronx">Bronx</option>
                                    <option value="Staten Island">Staten Island</option>
                                </select>
                            </div>
                        </div>
                        <button type="submit" class="btn">Search Properties</button>
                    </form>
                </div>

                <div class="features">
                    <div class="feature-card">
                        <div class="feature-icon">🏫</div>
                        <h3>School Proximity</h3>
                        <p>Find properties near top-rated schools with detailed distance calculations</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🏥</div>
                        <h3>Healthcare Access</h3>
                        <p>Locate nearby hospitals and health facilities for peace of mind</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🚇</div>
                        <h3>Transit Options</h3>
                        <p>Discover properties with easy access to subway stations and public transport</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🛡️</div>
                        <h3>Safety Analysis</h3>
                        <p>View crime statistics and safety metrics for each neighborhood</p>
                    </div>
                </div>

                <div class="api-section">
                    <h3>📊 Live Crime Data Integration</h3>
                    <p>This application integrates real-time crime statistics from NYC Open Data API, 
                    providing up-to-date safety information for informed decision-making.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/search')
def search_properties():
    
    helper = RealEstateQueryHelper(app.config['DATABASE'])
    

    criteria = {}
    if request.args.get('min_price'):
        criteria['min_price'] = int(request.args.get('min_price'))
    if request.args.get('max_price'):
        criteria['max_price'] = int(request.args.get('max_price'))
    if request.args.get('beds'):
        criteria['beds'] = int(request.args.get('beds'))
    if request.args.get('borough'):
        criteria['borough'] = request.args.get('borough')
    
    criteria['limit'] = 50
    
   
    properties = helper.search_properties(**criteria)
    
   
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search Results - NYC Real Estate</title>
        <meta charset="UTF-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header h1 {{ color: #333; margin-bottom: 10px; }}
            .back-link {{ 
                display: inline-block;
                color: #667eea;
                text-decoration: none;
                margin-top: 10px;
            }}
            .back-link:hover {{ text-decoration: underline; }}
            .results-count {{
                background: #667eea;
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
                font-size: 1.2rem;
            }}
            .property-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 20px;
            }}
            .property-card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .property-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            }}
            .price {{
                font-size: 1.8rem;
                color: #667eea;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .address {{
                color: #333;
                font-size: 1.1rem;
                margin-bottom: 15px;
                font-weight: 500;
            }}
            .details {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin-bottom: 15px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 6px;
            }}
            .detail-item {{
                text-align: center;
            }}
            .detail-label {{
                font-size: 0.85rem;
                color: #666;
                display: block;
            }}
            .detail-value {{
                font-size: 1.2rem;
                color: #333;
                font-weight: bold;
            }}
            .location {{
                color: #666;
                font-size: 0.9rem;
            }}
            .view-btn {{
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                width: 100%;
                margin-top: 10px;
                font-size: 1rem;
            }}
            .view-btn:hover {{
                background: #5568d3;
            }}
            .no-results {{
                text-align: center;
                padding: 60px 20px;
                background: white;
                border-radius: 8px;
            }}
            .no-results h2 {{
                color: #666;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Search Results</h1>
                <a href="/" class="back-link">← Back to Search</a>
            </div>
            
            <div class="results-count">
                Found {len(properties)} properties
            </div>
    '''
    
    if properties:
        html += '<div class="property-grid">'
        for prop in properties:
            price = f"${prop['price']:,}" if prop['price'] else "Price not available"
            address = prop['address'] or 'Address not available'
            beds = prop['beds'] if prop['beds'] is not None else 'N/A'
            baths = prop['baths'] if prop['baths'] is not None else 'N/A'
            sqft = f"{prop['sqft']:,}" if prop['sqft'] else 'N/A'
            borough = prop['borough'] or 'Unknown'
            neighborhood = prop['neighborhood'] or ''
            
            price_per_sqft = ''
            if prop['sqft'] and prop['sqft'] > 0 and prop['price']:
                pps = prop['price'] / prop['sqft']
                price_per_sqft = f"${pps:,.0f}/sqft"
            
            html += f'''
            <div class="property-card">
                <div class="price">{price}</div>
                <div class="address">{address}</div>
                <div class="details">
                    <div class="detail-item">
                        <span class="detail-label">Beds</span>
                        <span class="detail-value">{beds}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Baths</span>
                        <span class="detail-value">{baths}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Sqft</span>
                        <span class="detail-value">{sqft}</span>
                    </div>
                </div>
                <div class="location">
                    📍 {borough}{' - ' + neighborhood if neighborhood else ''}
                </div>
                {f'<div class="location" style="margin-top: 5px; color: #667eea;">{price_per_sqft}</div>' if price_per_sqft else ''}
                <button class="view-btn" onclick="window.location.href='/property/{prop['property_id']}'">
                    View Details & Nearby Amenities
                </button>
            </div>
            '''
        html += '</div>'
    else:
        html += '''
        <div class="no-results">
            <h2>No properties found</h2>
            <p>Try adjusting your search criteria</p>
        </div>
        '''
    
    html += '''
        </div>
    </body>
    </html>
    '''
    
    helper.close()
    return html

@app.route('/property/<int:property_id>')
def property_detail(property_id):
    """Show detailed property information"""
    helper = RealEstateQueryHelper(app.config['DATABASE'])
    analysis = helper.get_property_price_analysis(property_id)
    
    if 'error' in analysis:
        helper.close()
        return f"<h1>Property not found</h1><a href='/'>Back to search</a>"
    
    prop = analysis['property']
    amenities = analysis.get('nearby_amenities', {})
    
  
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Property Details - {prop['address']}</title>
        <meta charset="UTF-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .back-link {{ 
                display: inline-block;
                color: #667eea;
                text-decoration: none;
                margin-bottom: 20px;
                font-size: 1.1rem;
            }}
            .back-link:hover {{ text-decoration: underline; }}
            .main-card {{
                background: white;
                border-radius: 8px;
                padding: 40px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .price {{ 
                font-size: 3rem; 
                color: #667eea; 
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .address {{
                font-size: 1.5rem;
                color: #333;
                margin-bottom: 20px;
            }}
            .specs {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .spec-item {{
                text-align: center;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }}
            .spec-label {{
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 5px;
            }}
            .spec-value {{
                color: #333;
                font-size: 1.8rem;
                font-weight: bold;
            }}
            .section {{
                background: white;
                border-radius: 8px;
                padding: 30px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                color: #333;
                margin-bottom: 20px;
                font-size: 1.8rem;
            }}
            .amenity-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 15px;
            }}
            .amenity-item {{
                padding: 15px;
                background: #f8f9fa;
                border-radius: 6px;
                border-left: 4px solid #667eea;
            }}
            .amenity-name {{
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }}
            .amenity-distance {{
                color: #667eea;
                font-size: 0.9rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="javascript:history.back()" class="back-link">← Back to Results</a>
            
            <div class="main-card">
                <div class="price">${prop['price']:,}</div>
                <div class="address">{prop['address']}</div>
                
                <div class="specs">
                    <div class="spec-item">
                        <div class="spec-label">Bedrooms</div>
                        <div class="spec-value">{prop['beds'] or 'N/A'}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Bathrooms</div>
                        <div class="spec-value">{prop['baths'] or 'N/A'}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Square Feet</div>
                        <div class="spec-value">{prop['sqft']:,}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Price/Sqft</div>
                        <div class="spec-value">${analysis.get('price_per_sqft', 0):,.0f}</div>
                    </div>
                </div>
            </div>
    '''
    

    if amenities.get('schools'):
        html += '''
        <div class="section">
            <h2>🏫 Nearby Schools ({} within 1km)</h2>
            <div class="amenity-grid">
        '''.format(len(amenities['schools']))
        
        for school in amenities['schools'][:10]:
            html += f'''
            <div class="amenity-item">
                <div class="amenity-name">{school['name']}</div>
                <div class="amenity-distance">{school['distance_km']} km away</div>
            </div>
            '''
        html += '</div></div>'
    

    if amenities.get('hospitals'):
        html += '''
        <div class="section">
            <h2>🏥 Nearby Healthcare ({} within 1km)</h2>
            <div class="amenity-grid">
        '''.format(len(amenities['hospitals']))
        
        for hospital in amenities['hospitals'][:10]:
            html += f'''
            <div class="amenity-item">
                <div class="amenity-name">{hospital['name']}</div>
                <div class="amenity-distance">{hospital['distance_km']} km away</div>
            </div>
            '''
        html += '</div></div>'
    

    if amenities.get('transit_stations'):
        html += '''
        <div class="section">
            <h2>🚇 Nearby Transit ({} within 1km)</h2>
            <div class="amenity-grid">
        '''.format(len(amenities['transit_stations']))
        
        for station in amenities['transit_stations'][:10]:
            ada_badge = ' ♿ ADA' if station.get('ada') else ''
            html += f'''
            <div class="amenity-item">
                <div class="amenity-name">{station['name']}{ada_badge}</div>
                <div class="amenity-distance">{station['distance_km']} km away • Lines: {station.get('lines', 'N/A')}</div>
            </div>
            '''
        html += '</div></div>'
    

    if amenities.get('crime_stats'):
        crime_stats = amenities['crime_stats']
        crime_count = crime_stats.get('total_crimes', 0)
        

        if crime_count < 10:
            safety_level = "Low Crime Area"
            safety_color = "#28a745"
            safety_icon = "🟢"
        elif crime_count < 30:
            safety_level = "Moderate Crime Area"
            safety_color = "#ffc107"
            safety_icon = "🟡"
        else:
            safety_level = "Higher Crime Area"
            safety_color = "#dc3545"
            safety_icon = "🔴"
        
        html += f'''
        <div class="section">
            <h2>🛡️ Crime & Safety Statistics (within 1km)</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div>
                        <div style="font-size: 1.2rem; color: #666;">Safety Level</div>
                        <div style="font-size: 1.8rem; font-weight: bold; color: {safety_color};">
                            {safety_icon} {safety_level}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.2rem; color: #666;">Total Incidents</div>
                        <div style="font-size: 2.5rem; font-weight: bold; color: {safety_color};">
                            {crime_count}
                        </div>
                    </div>
                </div>
            </div>
        '''
        
        if crime_stats.get('by_offense'):
            html += '''
            <h3 style="margin-bottom: 15px; color: #333;">Crime Types</h3>
            <div class="amenity-grid">
            '''
            for offense, count in sorted(crime_stats['by_offense'].items(), key=lambda x: x[1], reverse=True)[:8]:
                html += f'''
                <div class="amenity-item">
                    <div class="amenity-name">{offense}</div>
                    <div class="amenity-distance">{count} incidents</div>
                </div>
                '''
            html += '</div>'
        
        html += '</div>'
    
    html += '''
        </div>
    </body>
    </html>
    '''
    
    helper.close()
    return html

@app.route('/api/properties')
def api_properties():
    """API endpoint for property search"""
    helper = RealEstateQueryHelper(app.config['DATABASE'])
    
    criteria = {}
    if request.args.get('min_price'):
        criteria['min_price'] = int(request.args.get('min_price'))
    if request.args.get('max_price'):
        criteria['max_price'] = int(request.args.get('max_price'))
    if request.args.get('beds'):
        criteria['beds'] = int(request.args.get('beds'))
    if request.args.get('borough'):
        criteria['borough'] = request.args.get('borough')
    
    criteria['limit'] = int(request.args.get('limit', 50))
    
    properties = helper.search_properties(**criteria)
    helper.close()
    
    return jsonify(properties)

@app.route('/api/property/<int:property_id>')
def api_property_detail(property_id):
    """API endpoint for property details"""
    helper = RealEstateQueryHelper(app.config['DATABASE'])
    analysis = helper.get_property_price_analysis(property_id)
    helper.close()
    
    return jsonify(analysis)

if __name__ == '__main__':
    print("="*60)
    print("NYC Real Estate Finder Web Application")
    print("="*60)
    print("\nStarting server...")
    print("Open your browser to: http://localhost:5000")
    print("\nAPI Endpoints:")
    print("  GET /api/properties - Search properties")
    print("  GET /api/property/<id> - Get property details")
    print("\nPress Ctrl+C to stop the server")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)