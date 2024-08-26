from flask import Flask, request, jsonify
from flask_cors import CORS
import pyproj
from shapely.geometry import shape, mapping
from shapely.ops import transform

app = Flask(__name__)
CORS(app)  # Permet les requêtes CORS

# Fonction pour supprimer la composante Z des coordonnées 3D
def remove_z_from_geometry(geometry):
    geom_type = geometry['type']
    coords = geometry['coordinates']
    
    if geom_type == 'Point':
        return {
            'type': 'Point',
            'coordinates': coords[:2]  # Conserver uniquement x et y
        }
    elif geom_type == 'LineString':
        return {
            'type': 'LineString',
            'coordinates': [coord[:2] for coord in coords]  # Conserver uniquement x et y
        }
    elif geom_type == 'Polygon':
        return {
            'type': 'Polygon',
            'coordinates': [[coord[:2] for coord in ring] for ring in coords]  # Conserver uniquement x et y
        }
    elif geom_type == 'MultiPolygon':
        return {
            'type': 'MultiPolygon',
            'coordinates': [[
                [coord[:2] for coord in ring] for ring in polygon
            ] for polygon in coords]  # Conserver uniquement x et y
        }
    else:
        raise Exception(f"Type de géométrie non pris en charge: {geom_type}")

# Fonction pour convertir les coordonnées de UTM à WGS84 avec un code EPSG spécifique
def convert_utm_to_wgs84(geometry, epsg_code):
    try:
        # Supprimer la composante Z si elle existe
        geometry_2d = remove_z_from_geometry(geometry)

        # Utiliser le code EPSG pour UTM
        proj_utm = pyproj.Proj(f"epsg:{epsg_code}")
        proj_wgs84 = pyproj.Proj(proj="latlong", datum="WGS84")

        # Créer un transformateur
        transformer = pyproj.Transformer.from_proj(proj_utm, proj_wgs84, always_xy=True)

        # Utiliser shapely's transform fonction directement avec le transformateur
        transformed_geom = transform(transformer.transform, shape(geometry_2d))
        
        # Débogage : imprime les coordonnées avant et après transformation
        print("Avant transformation:", shape(geometry_2d))
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
