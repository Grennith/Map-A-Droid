import s2sphere


class S2Helper:
    @staticmethod
    def latLngToCellId(lat, lng):
        regionCover = s2sphere.RegionCoverer()
        regionCover.min_level = 10
        regionCover.max_level = 10
        regionCover.max_cells = 1
        p1 = s2sphere.LatLng.from_degrees(lat, lng)
        p2 = s2sphere.LatLng.from_degrees(lat, lng)
        covering = regionCover.get_covering(s2sphere.LatLngRect.from_point_pair(p1, p2))
        # we will only get our desired cell ;)
        return covering[0].id()

    # RM stores lat, long as well...
    # returns tuple  <lat, lng>
    @staticmethod
    def middleOfCell(cellId):
        cell = s2sphere.CellId(cellId)
        latLng = cell.to_lat_lng()
        return latLng.lat().degrees, latLng.lng().degrees
