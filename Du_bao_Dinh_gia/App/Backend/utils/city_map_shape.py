from typing import Dict, List, Any

def city_map_shape(data: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    city_map: Dict[str, Dict[str, Dict[str, List[str]]]] = {}
    for city, dist_obj in data.items():
        if not isinstance(dist_obj, dict):
            continue
        city_map.setdefault(city, {})
        for dist, ward_obj in dist_obj.items():
            if not isinstance(ward_obj, dict):
                continue
            city_map[city].setdefault(dist, {})
            for ward, streets in ward_obj.items():
                if isinstance(streets, list):
                    clean = [s for s in streets if isinstance(s, str) and s.strip()]
                elif isinstance(streets, str):
                    clean = [streets.strip()] if streets.strip() else []
                else:
                    clean = []
                city_map[city][dist][ward] = sorted(set(clean))
    return city_map