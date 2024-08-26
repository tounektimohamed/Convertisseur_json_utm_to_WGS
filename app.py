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

        # Fonction pour transformer les coordonnées (2D ou 3D)
        def project(coords):
            if len(coords) == 2:
                x, y = coords
                return transformer.transform(x, y)
            elif len(coords) == 3:
                x, y, z = coords
                return transformer.transform(x, y)  # Z est ignoré dans la transformation
            else:
                raise ValueError("Les coordonnées doivent avoir 2 ou 3 dimensions.")

        # Fonction de transformation des géométries
        def transform_geom(geom):
            return transform(lambda x, y, z=None: project((x, y, z)), shape(geom))

        # Transformer la géométrie
        transformed_geom = transform_geom(geometry)

        # Afficher les géométries avant et après transformation
        print("Avant transformation:", mapping(geometry))
        print("Après transformation:", mapping(transformed_geom))

        return transformed_geom
    
    except Exception as e:
        raise Exception(f"Erreur de conversion UTM à WGS84: {e}")
