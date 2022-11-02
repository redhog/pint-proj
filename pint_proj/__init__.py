import pint
import pyproj
import projnames
import pandas as pd
import numpy as np
import pint_pandas
from pandas.api.extensions import (
    ExtensionArray,
    ExtensionDtype,
    register_dataframe_accessor,
    register_extension_dtype,
    register_series_accessor,
)

ureg = pint.get_application_registry()

epsgs = list(projnames.by_epsg.keys()) + [4326]

for epsg in epsgs:
    ureg.define('epsg_%s = [epsg_%s]; offset: 1 = _' % (epsg, epsg))

ureg.define('@alias epsg_4326 = latlon')

class Coord(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __sub__(self, other):
        if not isinstance(other, Coord): return self
        return Coord(self.x - other.x, self.y - other.y)
    def __mul__(self, other):
        return Coord(self.x * other, self.y * other)
    def __truediv__(self, other):
        return Coord(self.x / other, self.y / other)
    def __add__(self, other):
        if not isinstance(other, Coord): return self
        return Coord(self.x + other.x, self.y + other.y)
    def __format__(self, format_spec):
        return str(self.x) + ";" + str(self.y)
    def __repr__(self):
        return str(self.x) + ";" + str(self.y)

def register_epsg(epsg, c):
    def tolatlon(ureg, q):
        if hasattr(q.m, "__array__"):
            x = np.vectorize(lambda item: item.x)(q)
            y = np.vectorize(lambda item: item.y)(q)
            return ureg.Quantity(
                np.array([Coord(*item) for item in zip(
                    *pyproj.Transformer.from_crs(
                        epsg, 4326, always_xy=True).transform(x, y))]),
                "latlon")
        return ureg.Quantity(
            Coord(*pyproj.Transformer.from_crs(
                         epsg, 4326, always_xy=True).transform(q.m.x, q.m.y)), "latlon")
    def fromlatlon(ureg, q):
        if hasattr(q.m, "__array__"):
            x = np.vectorize(lambda item: item.x)(q)
            y = np.vectorize(lambda item: item.y)(q)
            return ureg.Quantity(
                np.array([Coord(*item) for item in zip(
                    *pyproj.Transformer.from_crs(
                        4326, epsg, always_xy=True).transform(x, y))]),
                "epsg_%s" % epsg)
        return ureg.Quantity(
            Coord(*pyproj.Transformer.from_crs(
                         4326, epsg, always_xy=True).transform(q.m.x, q.m.y)), "epsg_%s" % epsg)

    c.add_transformation("epsg_%s" % epsg, 'latlon', tolatlon)
    c.add_transformation("latlon", "epsg_%s" % epsg, fromlatlon)

    if (epsg in projnames.by_epsg) and ("UTM" in projnames.by_epsg[epsg]):
        def tom(ureg, q):
            if hasattr(q.m, "__array__"):
                x = np.vectorize(lambda item: item.x)(q)
                y = np.vectorize(lambda item: item.y)(q)
                return ureg.Quantity((x**2+y**2)**0.5, "m")
            return ureg.Quantity((q.m.x**2+q.m.y**2)**0.5, "m")
        c.add_transformation("delta_epsg_%s" % epsg, 'm', tom)

c = pint.Context('proj')
for epsg in epsgs:
    register_epsg(epsg, c)

ureg.add_context(c)


@register_series_accessor("proj")
class PintProjSeriesAccessor(object):
    def __init__(self, pandas_obj):
        self.pandas_obj = pandas_obj
        
    def to_geoseries(self):
        import geopandas as gpd
        
        crs = int(str(self.pandas_obj.dtype.units).split("epsg_")[1])
        return gpd.GeoSeries(gpd.points_from_xy(
            self.pandas_obj.apply(lambda q: q.magnitude.x),
            self.pandas_obj.apply(lambda q: q.magnitude.y),
            crs=crs))

    def from_geoseries(self):
        return pd.Series(self.pandas_obj.apply(lambda s: Coord(s.x, s.y)),
                         dtype="pint[epsg_%s]" % self.pandas_obj.crs.to_epsg())
