from shapely.geometry import shape, mapping
from shapely.ops import transform
import pyproj

def convert_utm_to_wgs84(geometry, epsg_code):
    try:
        # Définir les systèmes de projection
        proj_utm = pyproj.Proj(f"epsg:{epsg_code}")
        proj_wgs84 = pyproj.Proj(proj="latlong", datum="WGS84")

        # Créer un transformateur entre UTM et WGS84
        transformer = pyproj.Transformer.from_proj(proj_utm, proj_wgs84, always_xy=True)

        # Fonction pour transformer les coordonnées en ignorant Z si présent
        def project(x, y, z=None):
            return transformer.transform(x, y)

        # Transformer la géométrie
        transformed_geom = transform(lambda x, y, z=None: project(x, y, z), shape(geometry))
        
        # Afficher les géométries avant et après transformation
        print("Avant transformation:", mapping(geometry))
        print("Après transformation:", mapping(transformed_geom))

        return transformed_geom
    
    except Exception as e:
        raise Exception(f"Erreur de conversion UTM à WGS84: {e}")

# Exemple d'utilisation pour géométries 2D et 3D
geometry_example_2d = {
    "type": "LineString",
    "coordinates": [
        [630349.2017514162, 3576258.533900627],
        [630348.8256283968, 3576258.1334881177]
    ]
}

geometry_example_3d = {
    "type": "LineString",
    "coordinates": [
        [630867.9692095905, 3575942.284303735, 0],
        [630937.898215378, 3576008.15828909, 0]
    ]
}

# Code EPSG pour UTM Zone 32N (exemple)
epsg_code = 32632

# Conversion des géométries
result_2d = convert_utm_to_wgs84(geometry_example_2d, epsg_code)
result_3d = convert_utm_to_wgs84(geometry_example_3d, epsg_code)

# Afficher les résultats
print("Résultat transformation 2D:", mapping(result_2d))
print("Résultat transformation 3D:", mapping(result_3d))
