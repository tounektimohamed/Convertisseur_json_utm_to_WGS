from flask import Flask, request, jsonify
from flask_cors import CORS
import pyproj
import json
from shapely.geometry import shape, mapping
from shapely.ops import transform

app = Flask(__name__)
CORS(app)

def convert_utm_to_wgs84(geometry, epsg_code):
    try:
        proj_utm = pyproj.Proj(f"epsg:{epsg_code}")
        proj_wgs84 = pyproj.Proj(proj="latlong", datum="WGS84")
        transformer = pyproj.Transformer.from_proj(proj_utm, proj_wgs84, always_xy=True)

        def project(x, y, z=None):
            if z is None:
                return transformer.transform(x, y)
            else:
                lon, lat = transformer.transform(x, y)
                return lon, lat, z

        transformed_geom = transform(project, shape(geometry))

        return transformed_geom
    except Exception as e:
        raise Exception(f"Erreur de conversion UTM à WGS84: {e}")

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json()
        epsg_code = data.get('epsg_code')
        geojson = data.get('geojson')

        if not epsg_code or not geojson:
            return jsonify({"error": "Données manquantes: epsg_code et geojson sont requis."}), 400

        if not isinstance(epsg_code, int):
            return jsonify({"error": "epsg_code doit être un entier."}), 400

        features = []
        for feature in geojson.get('features', []):
            try:
                geom = convert_utm_to_wgs84(feature['geometry'], epsg_code)
                features.append({
                    'type': 'Feature',
                    'geometry': mapping(geom),
                    'properties': feature['properties']
                })
            except Exception as e:
                return jsonify({"error": f"Erreur lors de la conversion de la fonctionnalité: {e}"}), 400

        result = {
            'type': 'FeatureCollection',
            'features': features
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Erreur lors du traitement de la requête: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
