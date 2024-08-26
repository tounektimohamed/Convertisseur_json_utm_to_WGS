import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import pyproj
from shapely.geometry import shape, mapping
from shapely.ops import transform

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

def remove_z(geometry):
    logging.debug(f"Suppression de la composante Z pour la géométrie : {geometry}")
    geom_type = geometry['type']
    coords = geometry['coordinates']
    
    if geom_type == 'Point':
        return {'type': geom_type, 'coordinates': coords[:2]}
    elif geom_type == 'LineString':
        return {'type': geom_type, 'coordinates': [coord[:2] for coord in coords]}
    elif geom_type == 'Polygon':
        return {'type': geom_type, 'coordinates': [[coord[:2] for coord in ring] for ring in coords]}
    elif geom_type == 'MultiPolygon':
        return {'type': geom_type, 'coordinates': [[[coord[:2] for coord in ring] for ring in polygon] for polygon in coords]}
    else:
        raise ValueError(f"Unsupported geometry type: {geom_type}")

def convert_utm_to_wgs84(geometry, epsg_code):
    logging.debug(f"Début de la conversion de UTM à WGS84 avec EPSG: {epsg_code} pour la géométrie : {geometry}")
    try:
        geometry_2d = remove_z(geometry)
        logging.debug(f"Géométrie après suppression de Z : {geometry_2d}")
        
        transformer = pyproj.Transformer.from_crs(f"epsg:{epsg_code}", "epsg:4326", always_xy=True)
        logging.debug("Transformer créé avec succès")
        
        def transform_coords(x, y):
            logging.debug(f"Transformation des coordonnées: x={x}, y={y}")
            return transformer.transform(x, y)
        
        transformed_geom = transform(transform_coords, shape(geometry_2d))
        logging.debug(f"Géométrie transformée : {transformed_geom}")
        
        return transformed_geom
    except Exception as e:
        logging.error(f"Erreur de conversion UTM à WGS84: {e}")
        raise

@app.route('/convert', methods=['POST'])
def convert():
    logging.debug("Requête de conversion reçue")
    try:
        data = request.get_json()
        logging.debug(f"Données reçues : {data}")

        epsg_code = data.get('epsg_code')
        geojson = data.get('geojson')

        if not epsg_code or not geojson:
            logging.error("Données manquantes: epsg_code et geojson sont requis.")
            return jsonify({"error": "epsg_code et geojson sont requis."}), 400

        features = []
        for feature in geojson.get('features', []):
            try:
                logging.debug(f"Traitement de la fonctionnalité : {feature}")
                geom = convert_utm_to_wgs84(feature['geometry'], epsg_code)
                features.append({
                    'type': 'Feature',
                    'geometry': mapping(geom),
                    'properties': feature['properties']
                })
                logging.debug(f"Fonctionnalité convertie avec succès : {features[-1]}")
            except Exception as e:
                logging.error(f"Erreur lors de la conversion de la fonctionnalité: {e}")
                return jsonify({"error": f"Erreur lors de la conversion de la fonctionnalité: {e}"}), 400

        result = {'type': 'FeatureCollection', 'features': features}
        logging.debug(f"Résultat final de la conversion : {result}")

        return jsonify(result)
    except Exception as e:
        logging.error(f"Erreur lors du traitement de la requête: {e}")
        return jsonify({"error": f"Erreur lors du traitement de la requête: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
