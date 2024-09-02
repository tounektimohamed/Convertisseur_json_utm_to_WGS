from flask import Flask, request, jsonify
from flask_cors import CORS
import pyproj
import json
from shapely.geometry import shape, mapping
from shapely.ops import transform
import logging

app = Flask(__name__)
CORS(app)  # Permet les requêtes CORS

# Configurer le logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fonction pour convertir les coordonnées de UTM à WGS84 avec un code EPSG spécifique
def convert_utm_to_wgs84(geometry, epsg_code):
    try:
        # Utiliser le code EPSG pour UTM
        proj_utm = pyproj.Proj(f"epsg:{epsg_code}")
        proj_wgs84 = pyproj.Proj(proj="latlong", datum="WGS84")

        transformer = pyproj.Transformer.from_proj(proj_utm, proj_wgs84, always_xy=True)

        project = lambda x, y: transformer.transform(x, y)
        transformed_geom = transform(project, shape(geometry))
        
        # Logging : imprime les coordonnées avant et après transformation
        logger.debug(f"Avant transformation: {shape(geometry)}")
        logger.debug(f"Après transformation: {transformed_geom}")

        return transformed_geom
    except Exception as e:
        logger.error(f"Erreur de conversion UTM à WGS84: {e}")
        raise

# Fonction pour traiter les données en morceaux
def process_features_in_chunks(features, epsg_code, chunk_size=100):
    results = []
    for i in range(0, len(features), chunk_size):
        chunk = features[i:i + chunk_size]
        for feature in chunk:
            try:
                geom = convert_utm_to_wgs84(feature['geometry'], epsg_code)
                results.append({
                    'type': 'Feature',
                    'geometry': mapping(geom),
                    'properties': feature['properties']
                })
            except Exception as e:
                logger.error(f"Erreur lors de la conversion de la fonctionnalité: {e}")
                raise
    return results

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json()
        epsg_code = data.get('epsg_code')
        geojson = data.get('geojson')

        if not epsg_code or not geojson:
            logger.warning("Données manquantes: epsg_code et geojson sont requis.")
            return jsonify({"error": "Données manquantes: epsg_code et geojson sont requis."}), 400

        if not isinstance(epsg_code, int):
            logger.warning("epsg_code doit être un entier.")
            return jsonify({"error": "epsg_code doit être un entier."}), 400

        features = geojson.get('features', [])
        if not features:
            logger.warning("Aucune fonctionnalité trouvée dans le GeoJSON.")
            return jsonify({"error": "Aucune fonctionnalité trouvée dans le GeoJSON."}), 400

        # Traiter les fonctionnalités en morceaux
        processed_features = process_features_in_chunks(features, epsg_code)

        result = {
            'type': 'FeatureCollection',
            'features': processed_features
        }

        # Logging : imprime le résultat dans la console
        logger.debug(f"Résultat: {json.dumps(result, indent=2)}")

        return jsonify(result)
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête: {e}")
        return jsonify({"error": f"Erreur lors du traitement de la requête: {e}"}), 500

# Nouvelle fonction pour supprimer la composante Z des coordonnées
def remove_z_from_coordinates(coords):
    if isinstance(coords[0], list):  # Coordinates like [x, y, z]
        return [coord[:2] for coord in coords]
    else:
        return coords[:2]

# Nouvelle fonction pour supprimer la composante Z de la géométrie GeoJSON
def remove_z_from_geometry(geometry):
   geom_type = geometry['type']
    coords = geometry['coordinates']

    if geom_type == 'Point':
        geometry['coordinates'] = remove_z_from_coordinates(coords)
    elif geom_type == 'LineString' or geom_type == 'MultiLineString':
        if geom_type == 'MultiLineString':
            geometry['coordinates'] = [remove_z_from_coordinates(line) for line in coords]
        else:
            geometry['coordinates'] = remove_z_from_coordinates(coords)
    elif geom_type == 'Polygon':
        geometry['coordinates'] = [remove_z_from_coordinates(ring) for ring in coords]
    elif geom_type == 'MultiPolygon':
        geometry['coordinates'] = [[remove_z_from_coordinates(ring) for ring in polygon] for polygon in coords]
    else:
        raise Exception(f"Type de géométrie non pris en charge: {geom_type}")

    return geometry

# Nouvelle route pour supprimer la composante Z des coordonnées dans un GeoJSON
@app.route('/remove_z', methods=['POST'])
def remove_z():
    try:
        data = request.get_json()
        geojson = data.get('geojson')

        if not geojson:
            logger.warning("Données manquantes: geojson est requis.")
            return jsonify({"error": "Données manquantes: geojson est requis."}), 400

        for feature in geojson.get('features', []):
            feature['geometry'] = remove_z_from_geometry(feature['geometry'])

        return jsonify(geojson)
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête: {e}")
        return jsonify({"error": f"Erreur lors du traitement de la requête: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
