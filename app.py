from flask import Flask, request, jsonify
from flask_cors import CORS
import pyproj
import json
from shapely.geometry import shape, mapping
from shapely.ops import transform

app = Flask(__name__)
CORS(app)  # Permet les requêtes CORS

# Fonction pour supprimer la composante Z des coordonnées 3D
def remove_z_from_geometry(geometry):
    print("Supprimer la composante Z de la géométrie:", geometry)  # Débogage
    if geometry['type'] in ['Point', 'LineString', 'Polygon']:
        coords = geometry['coordinates']
        
        # Traiter les coordonnées en fonction du type de géométrie
        if geometry['type'] == 'Point':
            return {
                'type': 'Point',
                'coordinates': coords[:2]  # Conserver uniquement x et y
            }
        elif geometry['type'] == 'LineString':
            return {
                'type': 'LineString',
                'coordinates': [coord[:2] for coord in coords]  # Conserver uniquement x et y
            }
        elif geometry['type'] == 'Polygon':
            return {
                'type': 'Polygon',
                'coordinates': [[coord[:2] for coord in ring] for ring in coords]  # Conserver uniquement x et y
            }
    return geometry

# Fonction pour convertir les coordonnées de UTM à WGS84 avec un code EPSG spécifique
def convert_utm_to_wgs84(geometry, epsg_code):
    print(f"Conversion des coordonnées UTM à WGS84 avec EPSG {epsg_code}")  # Débogage
    try:
        # Supprimer la composante Z si elle existe
        geometry_2d = remove_z_from_geometry(geometry)
        print("Géométrie 2D après suppression de Z:", geometry_2d)  # Débogage

        # Utiliser le code EPSG pour UTM
        proj_utm = pyproj.Proj(f"epsg:{epsg_code}")
        proj_wgs84 = pyproj.Proj(proj="latlong", datum="WGS84")
        
        transformer = pyproj.Transformer.from_proj(proj_utm, proj_wgs84, always_xy=True)
        
        def project(x, y):
            return transformer.transform(x, y)
        
        transformed_geom = transform(lambda g: transform(project, g), shape(geometry_2d))
        print("Avant transformation:", shape(geometry_2d))  # Débogage
        print("Après transformation:", transformed_geom)  # Débogage

        return transformed_geom
    except Exception as e:
        print(f"Erreur de conversion UTM à WGS84: {e}")  # Débogage
        raise Exception(f"Erreur de conversion UTM à WGS84: {e}")

@app.route('/convert', methods=['POST'])
def convert():
    print("Requête de conversion reçue")  # Débogage
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
                print(f"Traitement de la fonctionnalité: {feature}")  # Débogage
                geom = convert_utm_to_wgs84(feature['geometry'], epsg_code)
                features.append({
                    'type': 'Feature',
                    'geometry': mapping(geom),
                    'properties': feature['properties']
                })
            except Exception as e:
                print(f"Erreur lors de la conversion de la fonctionnalité: {e}")  # Débogage
                return jsonify({"error": f"Erreur lors de la conversion de la fonctionnalité: {e}"}), 400

        result = {
            'type': 'FeatureCollection',
            'features': features
        }

        # Debug print to see the result in the console
        print("Résultat final de la conversion:", json.dumps(result, indent=2))  # Débogage

        return jsonify(result)
    except Exception as e:
        print(f"Erreur lors du traitement de la requête: {e}")  # Débogage
        return jsonify({"error": f"Erreur lors du traitement de la requête: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
