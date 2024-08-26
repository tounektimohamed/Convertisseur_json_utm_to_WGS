from flask import Flask, request, jsonify
from flask_cors import CORS
import pyproj
import json
from shapely.geometry import shape, mapping
from shapely.ops import transform

app = Flask(__name__)
CORS(app)  # Permet les requêtes CORS

def convert_utm_to_wgs84(geometry, epsg_code):
    try:
        # Utiliser le code EPSG pour UTM
        proj_utm = pyproj.Proj(f"epsg:{epsg_code}")
        proj_wgs84 = pyproj.Proj(proj="latlong", datum="WGS84")

        transformer = pyproj.Transformer.from_proj(proj_utm, proj_wgs84, always_xy=True)

        def project(x, y):
            return transformer.transform(x, y)

        # Vérifier si la géométrie a une dimension Z
        if geometry.get('coordinates') and len(geometry['coordinates'][0]) > 2:
            # Suppression de la dimension Z
            def remove_z(geom):
                if geom['type'] == 'Point':
                    return {'type': 'Point', 'coordinates': geom['coordinates'][:2]}
                elif geom['type'] == 'LineString':
                    return {'type': 'LineString', 'coordinates': [p[:2] for p in geom['coordinates']]}
                elif geom['type'] == 'Polygon':
                    return {'type': 'Polygon', 'coordinates': [[p[:2] for p in ring] for ring in geom['coordinates']]}
                elif geom['type'] == 'MultiPolygon':
                    return {'type': 'MultiPolygon', 'coordinates': [[p[:2] for p in ring] for ring in poly] for poly in geom['coordinates']}
                # Ajouter d'autres types de géométrie si nécessaire
                return geom

            geometry = remove_z(geometry)

        transformed_geom = transform(project, shape(geometry))

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
