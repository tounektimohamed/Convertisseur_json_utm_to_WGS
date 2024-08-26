import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import pyproj
from shapely.geometry import shape, mapping
from shapely.ops import transform

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)  # Permet les requêtes CORS

# Fonction pour supprimer la composante Z des coordonnées 3D
def remove_z(geometry):
    geom_type = geometry['type']
    coords = geometry['coordinates']
    
    if geom_type == 'Point':
        return {'type': geom_type, 'coordinates': coords[:2]}
    elif geom_type in ['LineString', 'Polygon']:
        return {'type': geom_type, 'coordinates': [[c[:2] for c in ring] for ring in coords]}
    elif geom_type == 'MultiPolygon':
        return {'type': geom_type, 'coordinates': [[[c[:2] for c in ring] for ring in polygon] for polygon in coords]}
    else:
        raise ValueError(f"Unsupported geometry type: {geom_type}")

# Fonction pour convertir les coordonnées de UTM à WGS84 avec un code EPSG spécifique
def convert_utm_to_wgs84(geometry, epsg_code):
    try:
        geometry_2d = remove_z(geometry)
        transformer = pyproj.Transformer.from_crs(f"epsg:{epsg_code}", "epsg:4326", always_xy=True)
        transformed_geom = transform(transformer.transform, shape(geometry_2d))
        return transformed_geom
    except Exception as e:
        logging.error(f"Erreur de conversion UTM à WGS84: {e}")
        raise

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json()
        epsg_code = data.get('epsg_code')
        geojson = data.get('geojson')

        if not epsg_code or not geojson:
            return jsonify({"error": "epsg_code et geojson sont requis."}), 400

        features = []
        for feature in geojson.get('features', []):
            try:
                geom = convert_utm_to_wgs84(feature['geometry'], epsg_code)
                features.append({'type': 'Feature', 'geometry': mapping(geom), 'properties': feature['properties']})
            except Exception as e:
                logging.error(f"Erreur lors de la conversion de la fonctionnalité: {e}")
                return jsonify({"error": f"Erreur lors de la conversion de la fonctionnalité: {e}"}), 400

        return jsonify({'type': 'FeatureCollection', 'features': features})
    except Exception as e:
        logging.error(f"Erreur lors du traitement de la requête: {e}")
        return jsonify({"error": f"Erreur lors du traitement de la requête: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
