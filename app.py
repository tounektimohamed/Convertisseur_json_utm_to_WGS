from flask import Flask, request, jsonify
from flask_cors import CORS
import pyproj
import json
from shapely.geometry import shape, mapping
from shapely.ops import transform

app = Flask(__name__)
CORS(app)  # Permet les requêtes CORS

# Fonction pour convertir les coordonnées de UTM à WGS84
def convert_utm_to_wgs84(geometry, utm_zone):
    proj_utm = pyproj.Proj(proj="utm", zone=utm_zone, datum="WGS84")
    proj_wgs84 = pyproj.Proj(proj="latlong", datum="WGS84")

    transformer = pyproj.Transformer.from_proj(proj_utm, proj_wgs84, always_xy=True)

    project = lambda x, y: transformer.transform(x, y)
    return transform(project, shape(geometry))

@app.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()
    utm_zone = data.get('utm_zone')
    geojson = data.get('geojson')

    features = []
    for feature in geojson['features']:
        geom = convert_utm_to_wgs84(feature['geometry'], utm_zone)
        features.append({
            'type': 'Feature',
            'geometry': mapping(geom),
            'properties': feature['properties']
        })

    result = {
        'type': 'FeatureCollection',
        'features': features
    }

    # Debug print to see the result in the console
    print(json.dumps(result, indent=2))

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
