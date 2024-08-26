from flask import Flask, request, jsonify
from flask_cors import CORS
import pyproj
import json
from shapely.geometry import shape, mapping
from shapely.ops import transform

app = Flask(__name__)
CORS(app)  # Permet les requêtes CORS

# Fonction pour convertir les coordonnées de UTM à WGS84 avec un code EPSG spécifique
def convert_utm_to_wgs84(geometry, epsg_code):
    try:
        # Détecter si la géométrie est 2D ou 3D
        is_3d = 'z' in geometry.get('coordinates', [])
        
        # Utiliser le code EPSG pour UTM
        proj_utm = pyproj.Proj(f"epsg:{epsg_code}")
        proj_wgs84 = pyproj.Proj(proj="latlong", datum="WGS84")
        
        if is_3d:
            # Créer un transformateur pour 3D
            transformer = pyproj.Transformer.from_proj(proj_utm, proj_wgs84, always_xy=True)
            
            def project_3d(x, y, z):
                lon, lat = transformer.transform(x, y)
                return lon, lat, z
            
            project = lambda x, y, z: project_3d(x, y, z)
            transformed_geom = transform(lambda g: transform(project, g), shape(geometry))
        else:
            # Créer un transformateur pour 2D
            transformer = pyproj.Transformer.from_proj(proj_utm, proj_wgs84, always_xy=True)
            
            def project_2d(x, y):
                lon, lat = transformer.transform(x, y)
                return lon, lat
            
            project = lambda x, y: project_2d(x, y)
            transformed_geom = transform(lambda g: transform(project, g), shape(geometry))
        
        # Débogage : imprime les coordonnées avant et après transformation
        print("Avant transformation:", shape(geometry))
        print("Après transformation:", transformed_geom)

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

        # Debug print to see the result in the console
        print(json.dumps(result, indent=2))

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Erreur lors du traitement de la requête: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
